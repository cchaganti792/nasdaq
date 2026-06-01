"""
Nasdaq_stock_list.py  -  Python 3
Downloads the full Nasdaq-listed stock list and refreshes NASDAQ_STOCK_LIST.

Step 1 : Fetch all stocks from Nasdaq screener API (symbol, name, market cap,
         sector, industry, IPO year, last sale, URL).
Step 2 : Upsert into NASDAQ_STOCK_LIST — inserts new symbols, updates existing.
Step 3 : Fetch OUTSTANDING_SHARES and FLOAT_SHARES from yfinance for every
         symbol in the table (~15 min for 3 000+ symbols at 0.3 s per call).

Run: python Nasdaq_stock_list.py
"""

import time
import requests
import yfinance as yf
import oracledb

# ── Oracle connection ──────────────────────────────────────────────────────
ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
connection = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
cursor = connection.cursor()

# ── Nasdaq screener API ────────────────────────────────────────────────────
SCREENER_URL = "https://api.nasdaq.com/api/screener/stocks"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ── Step 1: Download stock list ────────────────────────────────────────────
print("=" * 65)
print("  Nasdaq_stock_list.py")
print("  Step 1 : Downloading stock list from Nasdaq screener API...")
print("=" * 65)

resp = requests.get(
    SCREENER_URL,
    headers=HEADERS,
    params={"tableonly": "true", "limit": 10000, "download": "true"},
    timeout=30
)
resp.raise_for_status()
rows = resp.json()["data"]["rows"]
print(f"  Stocks received from API : {len(rows)}")

# ── Step 2: Upsert into NASDAQ_STOCK_LIST ─────────────────────────────────
print("\n  Step 2 : Upserting into NASDAQ_STOCK_LIST...")

MERGE_SQL = """
MERGE INTO nasdaq_stock_list dst
USING (SELECT :sym AS symbol FROM dual) src
ON (dst.symbol = src.symbol)
WHEN MATCHED THEN
    UPDATE SET name      = :name,
               lastsale  = :lastsale,
               marketcap = :marketcap,
               ipoyear   = :ipoyear,
               sector    = :sector,
               industry  = :industry,
               url       = :url
WHEN NOT MATCHED THEN
    INSERT (symbol, name, lastsale, marketcap, ipoyear, sector, industry, url)
    VALUES (:sym,  :name, :lastsale, :marketcap, :ipoyear, :sector, :industry, :url)
"""

upserted = 0
for row in rows:
    cursor.execute(MERGE_SQL,
        sym       = row.get('symbol',    '').strip(),
        name      = row.get('name',      '')[:150],
        lastsale  = row.get('lastsale',  '')[:10],
        marketcap = row.get('marketCap', '')[:10],
        ipoyear   = row.get('ipoyear',   '')[:10],
        sector    = row.get('sector',    '')[:30],
        industry  = row.get('industry',  '')[:100],
        url       = row.get('url',       '')[:200],
    )
    upserted += 1

connection.commit()
print(f"  Rows upserted : {upserted}")

# ── Step 3: Fetch outstanding and float shares from yfinance ───────────────
print("\n  Step 3 : Fetching outstanding / float shares from yfinance...")
print("  (approx 15 min for 3 000+ symbols)\n")

cursor.execute("SELECT symbol FROM nasdaq_stock_list ORDER BY symbol")
symbols = [r[0] for r in cursor.fetchall()]
total   = len(symbols)

shares_updated = 0
errors         = 0

for idx, symbol in enumerate(symbols, 1):
    try:
        info    = yf.Ticker(symbol).info
        o_shares = info.get('sharesOutstanding') or info.get('impliedSharesOutstanding')
        f_shares = info.get('floatShares')

        if o_shares or f_shares:
            cursor.execute(
                """UPDATE nasdaq_stock_list
                   SET outstanding_shares = :os,
                       float_shares       = :fs
                   WHERE symbol = :sym""",
                os=int(o_shares) if o_shares else None,
                fs=int(f_shares) if f_shares else None,
                sym=symbol
            )
            shares_updated += 1

        if idx % 100 == 0:
            connection.commit()
            print(f"  [{idx:>5}/{total}]  shares updated: {shares_updated}  errors: {errors}")

        time.sleep(0.3)

    except Exception as exc:
        errors += 1

connection.commit()

# ── Stamp last refreshed date on all rows ──────────────────────────────────
cursor.execute("UPDATE nasdaq_stock_list SET last_refreshed = SYSDATE")
connection.commit()

print(f"\n{'='*65}")
print(f"  Done.")
print(f"  Stocks upserted          : {upserted}")
print(f"  Shares rows updated      : {shares_updated}")
print(f"  Errors (symbol skipped)  : {errors}")
print(f"{'='*65}")
