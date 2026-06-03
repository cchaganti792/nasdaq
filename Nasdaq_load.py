"""
Nasdaq_load.py  -  Daily load entry point

Run once per trading day after downloading the NASDAQ*.csv from eoddata.

Execution order:
  1. Nasdaq_stock_list.py       -- refresh symbol list, insert new symbols
  2. SPLIT_INFO_DOWNLOAD_YFINANCE.py -- pull last-7-days split data from yfinance
  3. For each NASDAQ*.csv in Downloads:
       move CSV -> Downloads/NASDAQ/
       NASDAQ_UPLOAD.py         -- insert OHLCV, run all DB procs, Buy_proc
  4. NASDAQ_Analytics.py        -- signal quality analytics across all symbols
"""

import os
import glob
import shutil
from datetime import date
import oracledb

# Always run from the script's own directory so relative os.system calls work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
connection = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
cursor = connection.cursor()

SEP = '=' * 65

print(SEP)
print('  Nasdaq_load.py')
print(SEP)

# ── Step 1: Refresh Nasdaq symbol list (only if > 21 days since last run) ─
cursor.execute("SELECT MAX(LAST_REFRESHED) FROM nasdaq_stock_list")
last_refreshed = cursor.fetchone()[0]

if last_refreshed is None:
    days_since = None
    run_stock_list = True
else:
    days_since = (date.today() - last_refreshed.date()).days
    run_stock_list = days_since > 21

if run_stock_list:
    print(f'  [Step 1]  symbols   : never refreshed — running Nasdaq_stock_list.py')
    os.system('python Nasdaq_stock_list.py')
else:
    print(f'  [Step 1]  symbols   : skipping — last refreshed {last_refreshed.date()} ({days_since}d ago, next in {21 - days_since}d)')

# ── Step 2: Update stock split data ───────────────────────────────────────
print('  [Step 2]  splits    : running...')
os.system('python SPLIT_INFO_DOWNLOAD_NASDAQ_API.py')

# ── Step 3: Upload daily price CSV(s) ─────────────────────────────────────
list_of_files = glob.glob("C:\\Users\\jenit\\Downloads\\NASDAQ*.csv")

if not list_of_files:
    print('  [Step 3]  upload    : no NASDAQ*.csv in Downloads — skipped')
else:
    print(f'  [Step 3]  upload    : {len(list_of_files)} file(s) found')
    for csv_path in list_of_files:
        flname = csv_path.split("ds\\")[1]
        dest   = "C:\\Users\\jenit\\Downloads\\NASDAQ\\" + flname
        shutil.move(csv_path, dest)
        os.system('python NASDAQ_UPLOAD.py')

# ── Step 4: Analytics ─────────────────────────────────────────────────────
print('  [Step 4]  analytics : running...')
os.system('python NASDAQ_Analytics.py')

# ── Step 5: Sector / industry trend snapshot ──────────────────────────────
print('  [Step 5]  sectors   : running...')
os.system('python SECTOR_TREND_DAILY.py')

print(SEP)
print('  Daily load complete.')
print(SEP)
