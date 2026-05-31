"""
NASDAQ_BACKFILL.py  -  Python 3
Loads historical Nasdaq daily CSV files in date order.

Key difference from NASDAQ_UPLOAD.py (daily script):
  - Processes ALL files in the directory sorted by date
  - Extracts trade date from filename (NASDAQ_YYYYMMDD.csv)
  - Passes explicit date to SPLIT_PROC and NASDAQ_AVG_PROC_DAILY
    so each day's moving averages use all correct prior history

CSV format (no header row):
  SYMBOL, TRADEDATE, OPEN, HIGH, LOW, CLOSE, VOLUME
  e.g.: AAPL,14-Nov-2022,148.97,150.28,147.43,148.28,73374100

Place CSV files in : C:\\Users\\jenit\\Downloads\\NASDAQ\\
Filename format    : NASDAQ_YYYYMMDD.csv  (e.g. NASDAQ_20221114.csv)
Backup goes to     : D:\\Nasdaq_loaded\\

Run: python NASDAQ_BACKFILL.py

--- SAFEGUARDS ---
1. Date already fully loaded (in nasdaq_avg)
      -> SCRIPT STOPS. Shows cleanup SQL if you want to reload.

2. Partial CSV load detected (rows in nasdaq_hist but nothing in nasdaq_avg)
      -> SCRIPT STOPS. Shows cleanup SQL to wipe partial data before retry.

3. Any error during CSV load or proc execution
      -> SCRIPT STOPS immediately. Shows which step failed and cleanup SQL.

To reload a date that was already processed:
   DELETE FROM NASDAQ_HIST WHERE TRADEDATE = DATE 'YYYY-MM-DD';
   DELETE FROM NASDAQ_AVG  WHERE TRADEDATE = DATE 'YYYY-MM-DD';
   COMMIT;
   Then re-run the script.
"""

import os
import sys
import csv
import glob
import shutil
from datetime import datetime
import oracledb

# ── Oracle thick mode — required for Oracle 11g ────────────────────────────
ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)

connection = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
cursor     = connection.cursor()

CSV_DIR    = r"C:\Users\jenit\Downloads\NASDAQ"
BACKUP_DIR = r"D:\Nasdaq_loaded"


def parse_date_from_filename(filepath):
    """NASDAQ_20221114.csv  ->  date(2022, 11, 14)"""
    basename = os.path.basename(filepath)
    date_str = basename.replace('NASDAQ_', '').replace('.csv', '')
    return datetime.strptime(date_str, '%Y%m%d').date()


def stop(message, cleanup_sql=None):
    """Print error, optional cleanup SQL, and exit with code 1."""
    print(f"\n  {'='*61}")
    print(f"  STOPPED : {message}")
    if cleanup_sql:
        print(f"\n  Run this SQL to fix, then re-run the script:")
        for line in cleanup_sql:
            print(f"    {line}")
    print(f"  {'='*61}\n")
    sys.exit(1)


def cleanup_sql_for_date(tradedate):
    """Returns the SQL lines needed to wipe a date and start fresh."""
    d = tradedate
    return [
        f"-- Core price tables",
        f"DELETE FROM NASDAQ_HIST      WHERE TRADEDATE   = DATE '{d}';",
        f"DELETE FROM NASDAQ_AVG       WHERE TRADEDATE   = DATE '{d}';",
        f"DELETE FROM VOL_TOPPERS_HIST WHERE TRADEDATE   = DATE '{d}';",
        f"-- Price / volume signal logs (nasdaq_avg_proc_daily)",
        f"DELETE FROM PRI_LOG          WHERE INSERT_DATE = DATE '{d}';",
        f"DELETE FROM PRI2_LOG         WHERE INSERT_DATE = DATE '{d}';",
        f"DELETE FROM VOL_LOG          WHERE INSERT_DATE = DATE '{d}';",
        f"DELETE FROM VOL2_LOG         WHERE INSERT_DATE = DATE '{d}';",
        f"-- Screener output tables (nasdaq_postive_proc / nasdaq_VOL_proc)",
        f"DELETE FROM STRONG_POSITIVE  WHERE INS_DATE    = DATE '{d}';",
        f"DELETE FROM ALL_POSITIVE     WHERE INS_DATE    = DATE '{d}';",
        f"DELETE FROM STRONG_NEGITIVE  WHERE INS_DATE    = DATE '{d}';",
        f"DELETE FROM ALL_NEGITIVE     WHERE INS_DATE    = DATE '{d}';",
        f"DELETE FROM BULLISH          WHERE INS_DATE    = DATE '{d}';",
        f"DELETE FROM POS_VOL          WHERE INSERT_DATE = DATE '{d}';",
        f"DELETE FROM NEG_VOL          WHERE INSERT_DATE = DATE '{d}';",
        f"-- Snapshot log tables (view inserts)",
        f"DELETE FROM PE               WHERE TRADEDATE   = DATE '{d}';",
        f"DELETE FROM FUNDA            WHERE TRADEDATE   = DATE '{d}';",
        f"DELETE FROM QUICK_LOOK_LOG   WHERE TRADEDATE   = DATE '{d}';",
        f"DELETE FROM RSI2530_LOG      WHERE TRADEDATE   = DATE '{d}';",
        f"DELETE FROM DOWN150_VW       WHERE TRADEDATE   = DATE '{d}';",
        f"-- Analysis proc tables (observer_proc / Buy_proc)",
        f"DELETE FROM OBSERVER_LOG     WHERE TRADEDATE   = DATE '{d}';",
        f"DELETE FROM PRICE_POINTS_LOG WHERE TRADEDATE   = DATE '{d}';",
        f"DELETE FROM BUY_LOG_LOG      WHERE TRADEDATE   = DATE '{d}';",
        "COMMIT;",
    ]


def check_date_state(tradedate, filename):
    """
    Check database state for this date before attempting to load.

    Returns:
      'clean'   -> date not in DB at all, safe to load
      stops     -> exits the script if date is already loaded or partially loaded
    """
    # Check nasdaq_avg (fully processed marker)
    cursor.execute(
        "SELECT COUNT(*) FROM nasdaq_avg WHERE tradedate = :dt",
        dt=tradedate
    )
    avg_count = cursor.fetchone()[0]

    if avg_count > 0:
        stop(
            f"{filename}  ->  date {tradedate} is already fully loaded in nasdaq_avg.",
            cleanup_sql_for_date(tradedate)
        )

    # Check nasdaq_hist (partial load marker — CSV loaded but procs never ran)
    cursor.execute(
        "SELECT COUNT(*) FROM nasdaq_hist WHERE tradedate = :dt",
        dt=tradedate
    )
    hist_count = cursor.fetchone()[0]

    if hist_count > 0:
        stop(
            f"{filename}  ->  PARTIAL LOAD detected.\n"
            f"  {hist_count} rows exist in NASDAQ_HIST for {tradedate}\n"
            f"  but NASDAQ_AVG has no data. Procs did not complete last run.",
            cleanup_sql_for_date(tradedate)
        )

    return 'clean'


def load_csv_to_hist(filepath, tradedate):
    """
    Insert all rows from one CSV file into NASDAQ_HIST.
    Stops the script on any unexpected error.
    Duplicate rows (IntegrityError) are counted and skipped —
    they mean the symbol/date PK already exists.
    """
    inserted = 0
    skipped  = 0
    with open(filepath, encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 7:
                continue
            try:
                cursor.execute(
                    """INSERT INTO NASDAQ_HIST
                       (SYMBOL, TRADEDATE, OPEN, HIGH, LOW, CLOSE, VOLUME)
                       VALUES (:sym, :dt, :op, :hi, :lo, :cl, :vol)""",
                    sym=row[0].strip(),
                    dt=tradedate,
                    op=float(row[2]),
                    hi=float(row[3]),
                    lo=float(row[4]),
                    cl=float(row[5]),
                    vol=int(float(row[6]))
                )
                inserted += 1
            except oracledb.IntegrityError:
                skipped += 1
    connection.commit()
    return inserted, skipped


def run_proc(name, tradedate, params=None):
    """Call a stored procedure. Stops the script if it fails."""
    print(f"    {name:<28} running...")
    try:
        cursor.callproc(name, params or [])
        connection.commit()
    except Exception as exc:
        connection.rollback()
        stop(
            f"Proc {name} failed: {exc}",
            [
                "The proc above failed. Data may be in a partial state.",
                "Check the error, then clean up this date and re-run:",
            ] + cleanup_sql_for_date(tradedate)
        )


# ── Collect and sort all CSV files by date ────────────────────────────────
all_files = sorted(
    glob.glob(os.path.join(CSV_DIR, "NASDAQ_????????.csv")),
    key=lambda f: parse_date_from_filename(f)
)

print("=" * 65)
print("  NASDAQ_BACKFILL.py")
print(f"  Files found : {len(all_files)}")
if all_files:
    print(f"  Date range  : {parse_date_from_filename(all_files[0])}"
          f"  to  {parse_date_from_filename(all_files[-1])}")
print("=" * 65)

if not all_files:
    stop(f"No NASDAQ_YYYYMMDD.csv files found in {CSV_DIR}")

total_loaded = 0

for filepath in all_files:
    tradedate = parse_date_from_filename(filepath)
    filename  = os.path.basename(filepath)

    print(f"\n  [CHECK] {filename}  ({tradedate})")

    # ── Safeguard checks — stops script if date is already loaded ──────────
    check_date_state(tradedate, filename)

    print(f"  [LOAD]  {filename}  ({tradedate})")

    # ── 1. Load OHLCV rows into NASDAQ_HIST ────────────────────────────────
    try:
        inserted, dup = load_csv_to_hist(filepath, tradedate)
        print(f"    NASDAQ_HIST              : {inserted} rows inserted,"
              f" {dup} duplicates skipped")
    except Exception as exc:
        connection.rollback()
        stop(
            f"CSV load failed for {filename}: {exc}",
            cleanup_sql_for_date(tradedate)
        )

    # ── 2. Apply stock splits whose EX_DATE = tradedate ────────────────────
    run_proc('SPLIT_PROC', tradedate, [tradedate])

    # ── 3. Compute moving averages for this specific date ──────────────────
    #    Explicit date is REQUIRED — NULL would use max(tradedate) only
    run_proc('nasdaq_avg_proc_daily', tradedate, [tradedate])

    # ── 4. RSI and Bollinger (no date param — use max = just-loaded date) ──
    run_proc('RSI_proc', tradedate)
    run_proc('BOLLINGER_proc', tradedate)

    # ── 5. Screeners ───────────────────────────────────────────────────────
    run_proc('nasdaq_postive_proc', tradedate)
    run_proc('nasdaq_VOL_proc', tradedate)

    # ── 6. Populate summary / log tables from views ────────────────────────
    view_inserts = [
        'INSERT INTO PE SELECT * FROM P_E',
        'INSERT INTO funda SELECT * FROM fundav',
        'INSERT INTO QUICK_LOOK_LOG SELECT * FROM QUICK_LOOK',
        'INSERT INTO rsi2530_log SELECT * FROM rsi2030',
        'INSERT INTO nasdaq.Down150_vw SELECT * FROM DOWN_150_SELECT_VW',
    ]
    for stmt in view_inserts:
        try:
            cursor.execute(stmt)
        except oracledb.IntegrityError:
            pass
        except Exception as exc:
            connection.rollback()
            stop(
                f"View insert failed [{stmt[:40]}...]: {exc}",
                cleanup_sql_for_date(tradedate)
            )
    connection.commit()

    # ── 7. Analysis procs ──────────────────────────────────────────────────
    run_proc('Analyze_150_proc', tradedate)
    run_proc('observer_proc', tradedate)
    run_proc('Buy_proc', tradedate)

    # ── 8. Move processed file to backup ───────────────────────────────────
    shutil.move(filepath, os.path.join(BACKUP_DIR, filename))
    print(f"    Moved to backup. Day complete.")
    total_loaded += 1

print(f"\n{'='*65}")
print(f"  Backfill complete.  Days loaded : {total_loaded}")
print(f"{'='*65}")
