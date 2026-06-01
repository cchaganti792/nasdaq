"""
SPLIT_INFO_DOWNLOAD_NASDAQ_API.py  -  Python 3
Fetches upcoming/recent stock splits from the Nasdaq public API in ONE call
and loads new rows into SPLIT_STOCK_DOWNLOAD_CONTENT.

Replaces the per-ticker yfinance approach for the daily load — one HTTP call
instead of ~5000.  The yfinance script (SPLIT_INFO_DOWNLOAD_YFINANCE.py) is
kept as a fallback for historical backfill or when the API is unreachable.

Nasdaq API:  https://api.nasdaq.com/api/calendar/splits
Response  :  data.rows[] — symbol, name, ratio ("6 : 5"), executionDate ("6/18/2026")

Table     :  SPLIT_STOCK_DOWNLOAD_CONTENT
PK        :  (SYMBOL, EX_DATE) — duplicates are silently skipped
STATE_FLAG:  'N' on insert — split_proc reads this and sets 'Y' after processing
SCRIPT_NAME: 'NASDAQ_API' — identifies which script inserted the row
"""

import requests
import oracledb
from datetime import datetime

# ── Oracle thick mode — required for Oracle 11g ────────────────────────────
ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)

connection = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
cursor     = connection.cursor()

API_URL = "https://api.nasdaq.com/api/calendar/splits"
HEADERS = {
    "accept":     "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SEP = '=' * 65

print(SEP)
print('  SPLIT_INFO_DOWNLOAD_NASDAQ_API.py')
print(SEP)

# ── Fetch from Nasdaq API ─────────────────────────────────────────────────
try:
    resp = requests.get(API_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
except Exception as exc:
    print(f"  ERROR : API request failed — {exc}")
    print(SEP)
    raise SystemExit(1)

rows = (payload.get("data") or {}).get("rows") or []
if not rows:
    print("  API returned no rows — nothing to insert.")
    print(SEP)
    raise SystemExit(0)

print(f"  Splits received from API : {len(rows)}")

# ── Insert each split ─────────────────────────────────────────────────────
inserted = 0
skipped  = 0
errors   = 0

for row in rows:
    symbol  = (row.get("symbol") or "").strip()
    ratio   = (row.get("ratio")  or "").replace(" ", "")   # "6 : 5" -> "6:5"
    ex_raw  = (row.get("executionDate") or "").strip()      # "6/18/2026"

    if not symbol or not ratio or not ex_raw:
        errors += 1
        continue

    try:
        ex_date = datetime.strptime(ex_raw, "%m/%d/%Y").date()
    except ValueError:
        print(f"  SKIP  {symbol:<8}  bad date format: {ex_raw!r}")
        errors += 1
        continue

    try:
        cursor.execute(
            """INSERT INTO split_stock_download_content
               (SYMBOL, SPLIT_RATIO, ANNOUNCEMENT_DATE, RECORD_DATE, EX_DATE,
                DOWNLOAD_MON, STATE_FLAG, INS_DATE, SCRIPT_NAME)
               VALUES (:sym, :ratio, :ex, :ex, :ex, :ex, 'N', SYSDATE, 'NASDAQ_API')""",
            sym=symbol, ratio=ratio, ex=ex_date
        )
        connection.commit()
        print(f"  INSERTED  {symbol:<8}  {ratio:<6}  ex_date={ex_date}")
        inserted += 1
    except oracledb.IntegrityError:
        skipped += 1
    except Exception as exc:
        print(f"  ERROR     {symbol:<8}  {exc}")
        errors += 1

print(SEP)
print(f"  Splits from API      : {len(rows)}")
print(f"  Inserted             : {inserted}")
print(f"  Skipped (duplicate)  : {skipped}")
print(f"  Errors               : {errors}")
print(SEP)
