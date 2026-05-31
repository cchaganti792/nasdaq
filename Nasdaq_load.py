"""
Nasdaq_load.py  -  Daily load entry point

Run once per trading day after downloading the NASDAQ*.csv from eoddata.

Execution order:
  1. Nasdaq_stock_list.py       -- refresh symbol list, insert new symbols
  2. SPLIT_INFO_DOWNLOAD_YFINANCE.py -- pull last-7-days split data from yfinance
  3. For each NASDAQ*.csv in Downloads:
       move CSV -> Downloads\NASDAQ\
       NASDAQ_UPLOAD.py         -- insert OHLCV, run all DB procs, Buy_proc
  4. NASDAQ_Analytics.py        -- signal quality analytics across all symbols
"""

import os
import glob
import shutil

SEP = '=' * 60

# ── Step 1: Refresh Nasdaq symbol list ────────────────────────────────────
print(SEP)
print('  Step 1 : Nasdaq symbol list update')
print(SEP)
os.system('python Nasdaq_stock_list.py')

# ── Step 2: Update stock split data ───────────────────────────────────────
print(SEP)
print('  Step 2 : Stock split data update')
print(SEP)
os.system('python SPLIT_INFO_DOWNLOAD_YFINANCE.py')

# ── Step 3: Upload daily price CSV(s) ─────────────────────────────────────
print(SEP)
print('  Step 3 : Daily price data upload')
print(SEP)

list_of_files = glob.glob("C:\\Users\\jenit\\Downloads\\NASDAQ*.csv")

if not list_of_files:
    print('  No NASDAQ*.csv files found in Downloads folder. Skipping upload.')
else:
    print(f'  Found {len(list_of_files)} file(s) to process.')
    for csv_path in list_of_files:
        flname = csv_path.split("ds\\")[1]
        dest   = "C:\\Users\\jenit\\Downloads\\NASDAQ\\" + flname
        shutil.move(csv_path, dest)
        print(f'  Processing : {flname}')
        os.system('python NASDAQ_UPLOAD.py')
        try:
            shutil.move(dest, "C:\\Users\\jenit\\Downloads\\NASDAQ\\Nasdaq_bkp\\" + flname)
            print(f'  Archived   : {flname}')
        except IOError:
            print(f'  Warning    : could not archive {flname}')

# ── Step 4: Analytics ─────────────────────────────────────────────────────
print(SEP)
print('  Step 4 : NASDAQ Analytics')
print(SEP)
os.system('python NASDAQ_Analytics.py')

print(SEP)
print('  Daily load complete.')
print(SEP)
