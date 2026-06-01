"""
NASDAQ_UPLOAD.py  -  Python 3
Daily price data loader — called by Nasdaq_load.py.

Reads each NASDAQ*.csv from Downloads/NASDAQ/, inserts into NASDAQ_HIST,
then runs the full proc chain. If any proc fails, prints cleanup SQL for
that trade date and exits so no partial data is left silently in the DB.
"""

import os
import sys
import csv
import glob
import shutil
import time
import oracledb

# ── Oracle thick mode — required for Oracle 11g ────────────────────────────
ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)

connection = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
cursor     = connection.cursor()

SEP = '=' * 61


def cleanup_sql_for_date(tradedate):
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


def stop(message, tradedate=None):
    print(f"\n  {SEP}")
    print(f"  STOPPED : {message}")
    if tradedate:
        print(f"\n  Run this SQL to clean up, then re-run:")
        for line in cleanup_sql_for_date(tradedate):
            print(f"    {line}")
    print(f"  {SEP}\n")
    sys.exit(1)


def run_proc(name, tradedate, params=None):
    print(f"    {name:<28} running...")
    try:
        cursor.callproc(name, params or [])
        connection.commit()
    except Exception as exc:
        connection.rollback()
        stop(f"Proc {name} failed: {exc}", tradedate)


def insert_db(values):
    try:
        cursor.execute(
            "INSERT INTO NASDAQ_HIST (SYMBOL,TRADEDATE,OPEN,HIGH,LOW,CLOSE,VOLUME) "
            "VALUES (:sym, TO_DATE(:dt,'dd-mon-yy'), TO_NUMBER(:op), "
            "        TO_NUMBER(:hi), TO_NUMBER(:lo), TO_NUMBER(:cl), TO_NUMBER(:vol))",
            sym=values[0], dt=values[1], op=values[2],
            hi=values[3],  lo=values[4], cl=values[5], vol=values[6]
        )
        return True
    except oracledb.IntegrityError:
        return False
    except Exception as exc:
        print(f"    INSERT ERROR : {values[0]} {values[1]} — {exc}")
        return False


def csv_read(filepath):
    flname = os.path.basename(filepath)
    print(f"\n  [LOAD]  {flname}")

    # ── Insert OHLCV rows ──────────────────────────────────────────────────
    inserted = 0
    skipped  = 0
    tradedate = None

    with open(filepath, encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) < 7:
                continue
            if insert_db(row):
                inserted += 1
            else:
                skipped += 1
    connection.commit()

    # ── Determine tradedate from what was just loaded ──────────────────────
    cursor.execute("SELECT MAX(TRADEDATE) FROM NASDAQ_HIST")
    result = cursor.fetchone()
    if not result or not result[0]:
        stop(f"Could not determine tradedate after loading {flname}")
    tradedate = result[0].strftime('%Y-%m-%d')
    skip_str  = f", {skipped} skipped" if skipped else ""
    print(f"    {'NASDAQ_HIST':<28}: {inserted} rows inserted{skip_str}  |  date: {tradedate}")

    # ── Proc chain ────────────────────────────────────────────────────────
    run_proc('SPLIT_PROC',            tradedate)
    run_proc('nasdaq_avg_proc_daily', tradedate)
    run_proc('RSI_proc',              tradedate)
    run_proc('BOLLINGER_proc',        tradedate)
    run_proc('nasdaq_postive_proc',   tradedate)
    run_proc('nasdaq_VOL_proc',       tradedate)

    # ── View snapshot inserts ─────────────────────────────────────────────
    view_inserts = [
        'INSERT INTO PE               SELECT * FROM P_E',
        'INSERT INTO funda            SELECT * FROM fundav',
        'INSERT INTO QUICK_LOOK_LOG   SELECT * FROM QUICK_LOOK',
        'INSERT INTO nasdaq.Down150_vw SELECT * FROM DOWN_150_SELECT_VW',
        'INSERT INTO rsi2530_log      SELECT * FROM rsi2030',
    ]
    for stmt in view_inserts:
        try:
            cursor.execute(stmt)
        except oracledb.IntegrityError:
            pass
        except Exception as exc:
            connection.rollback()
            stop(f"View insert failed [{stmt[:50]}]: {exc}", tradedate)
    connection.commit()

    # ── Analysis procs ────────────────────────────────────────────────────
    run_proc('Analyze_150_proc', tradedate)
    run_proc('observer_proc',    tradedate)
    run_proc('Buy_proc',         tradedate)

    # ── Archive CSV ───────────────────────────────────────────────────────
    try:
        shutil.move(filepath, f"D:\\Nasdaq_loaded\\{flname}")
        print(f"    Moved to D:\\Nasdaq_loaded\\  Day complete.")
    except Exception as exc:
        print(f"    Warning  : could not archive {flname} — {exc}")


# ── Main ──────────────────────────────────────────────────────────────────
list_of_files = glob.glob("C:\\Users\\jenit\\Downloads\\NASDAQ\\NASDAQ*.csv")

if not list_of_files:
    print("  No NASDAQ*.csv files found in Downloads/NASDAQ/")
else:
    for filepath in list_of_files:
        csv_read(filepath)
