"""
SPLIT_INFO_DOWNLOAD_YFINANCE.py  -  Python 3
Replaces US_STOCK_SPLIT_INFO_DOWNLOAD.py (Fidelity scraper, now paywalled).

Fetches historical stock split data from Yahoo Finance (yfinance) for every
symbol tracked in nasdaq_hist and loads it into SPLIT_STOCK_DOWNLOAD_CONTENT.

Use cases:
  1. One-time backfill  : loads all splits from 11-Nov-2022 to today
  2. Ongoing daily use  : called by Nasdaq_load.py instead of the old script

Requirements:
  pip install yfinance cx_Oracle

How split data flows into Oracle:
  This script  -->  SPLIT_STOCK_DOWNLOAD_CONTENT (STATE_FLAG='N' explicitly set — no DB default)
  split_proc   -->  reads STATE_FLAG='N' rows, adjusts nasdaq_hist + nasdaq_avg prices/volumes
                    then sets STATE_FLAG='Y'
"""

import os
import time
import cx_Oracle
import yfinance as yf
from fractions import Fraction
from datetime import date

# ── Oracle connection ──────────────────────────────────────────────────────
os.environ['ORACLE_HOME'] = "C:\\app\\User\\product\\11.2.0\\client_1"
connection = cx_Oracle.connect("nasdaq", "nasdaq123", "localhost/orcl")
cursor = connection.cursor()

# ── Date range for this run ────────────────────────────────────────────────
# Change BACKFILL_START to move the window forward after first run
BACKFILL_START = date(2022, 11, 11)
RUN_END        = date.today()


def ratio_to_str(ratio_float):
    """
    Convert a yfinance split ratio float to the 'X:Y' string format
    that split_proc.plsql expects.

    Examples:
        4.0  -->  '4:1'   (4-for-1 forward split)
        2.0  -->  '2:1'
        0.5  -->  '1:2'   (1-for-2 reverse split)
        1.5  -->  '3:2'
    """
    frac = Fraction(ratio_float).limit_denominator(1000)
    return f"{frac.numerator}:{frac.denominator}"


def insert_split(symbol, ratio_str, ex_date):
    """
    Insert one split row into SPLIT_STOCK_DOWNLOAD_CONTENT.
    STATE_FLAG must be explicitly set to 'N' — no default exists in the table.
    split_proc filters WHERE STATE_FLAG='N', so NULL would be silently ignored.
    ANNOUNCEMENT_DATE and RECORD_DATE are stored as EX_DATE (split_proc doesn't use them).
    """
    try:
        cursor.execute(
            """INSERT INTO split_stock_download_content
               (SYMBOL, SPLIT_RATIO, ANNOUNCEMENT_DATE, RECORD_DATE, EX_DATE, DOWNLOAD_MON,
                STATE_FLAG, INS_DATE)
               VALUES (:sym, :ratio, :ex, :ex, :ex, :ex, 'N', SYSDATE)""",
            sym=symbol, ratio=ratio_str, ex=ex_date
        )
        connection.commit()
        print(f"  INSERTED   {symbol:<8}  {ratio_str:<6}  ex_date={ex_date}")
    except cx_Oracle.IntegrityError:
        print(f"  SKIP       {symbol:<8}  already present for {ex_date}")


# ── Step 1: get all symbols we actually have price data for ────────────────
symbol_list = []
cursor.execute(
    "SELECT DISTINCT symbol FROM nasdaq_hist "
    "WHERE tradedate >= :start ORDER BY symbol",
    start=BACKFILL_START
)
for row in cursor:
    symbol_list.append(row[0])

total = len(symbol_list)
print("=" * 65)
print(f"  SPLIT_INFO_DOWNLOAD_YFINANCE.py")
print(f"  Symbols to check : {total}")
print(f"  Date range       : {BACKFILL_START}  to  {RUN_END}")
print("=" * 65)

# ── Step 2: fetch splits from Yahoo Finance and insert ─────────────────────
splits_inserted = 0
errors          = 0

for idx, symbol in enumerate(symbol_list, 1):
    try:
        ticker = yf.Ticker(symbol)
        splits = ticker.splits          # pandas Series  index=Timestamp, value=float ratio

        if splits.empty:
            print(f"[{idx:>5}/{total}] {symbol:<8}  no split history")
            continue

        # Filter to our date window
        in_range = splits[
            (splits.index.date >= BACKFILL_START) &
            (splits.index.date <= RUN_END)
        ]

        if in_range.empty:
            print(f"[{idx:>5}/{total}] {symbol:<8}  no splits in range")
            continue

        print(f"[{idx:>5}/{total}] {symbol:<8}  {len(in_range)} split(s) found")
        for split_ts, ratio in in_range.items():
            ratio_str = ratio_to_str(float(ratio))
            insert_split(symbol, ratio_str, split_ts.date())
            splits_inserted += 1

        time.sleep(0.3)     # avoid hammering Yahoo Finance

    except Exception as exc:
        print(f"[{idx:>5}/{total}] {symbol:<8}  ERROR: {exc}")
        errors += 1

# ── Step 3: mark all processed months as done in the status table ──────────
# This prevents Nasdaq_load.py from trying to re-download split data
# for months we have already covered via yfinance.
cursor.execute(
    "UPDATE SPLIT_STOCK_DOWNLOAD_STATUS "
    "SET DSTATE = 'Y' "
    "WHERE DSTATE = 'N' AND DOWNLOAD_MON <= SYSDATE"
)
rows_updated = cursor.rowcount
connection.commit()

print("=" * 65)
print(f"  Finished.")
print(f"  Symbols checked            : {total}")
print(f"  Split rows inserted        : {splits_inserted}")
print(f"  Errors (symbol skipped)    : {errors}")
print(f"  Status table rows closed   : {rows_updated}")
print("=" * 65)
