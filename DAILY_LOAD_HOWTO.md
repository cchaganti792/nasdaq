# Daily Load — How To Run

## Pre-requisite (manual step)
Download the daily price CSV from your data source (eoddata or similar)
and save it to:

    C:\Users\jenit\Downloads\

Filename must start with NASDAQ, e.g.:  NASDAQ20260531.csv

---

## Command to run

    cd C:\FS\JEN_DAT\UPLOADS\PYTHON_SEL_SCRIPTS\Nasdaq
    python Nasdaq_load.py

That is the ONLY script you run manually. It calls everything else.

---

## What Nasdaq_load.py does

    python Nasdaq_load.py
    │
    ├── Step 1 : python Nasdaq_stock_list.py
    │            Downloads full Nasdaq symbol list from Nasdaq screener API
    │            Upserts new/updated symbols into NASDAQ_STOCK_LIST table
    │            Fetches outstanding + float shares from yfinance (~15 min)
    │
    ├── Step 2 : python SPLIT_INFO_DOWNLOAD_YFINANCE.py
    │            Checks last 7 days of splits from Yahoo Finance
    │            Inserts any new splits into SPLIT_STOCK_DOWNLOAD_CONTENT
    │
    ├── Step 3 : For each NASDAQ*.csv found in Downloads folder:
    │              Move CSV → Downloads\NASDAQ\
    │              python NASDAQ_UPLOAD.py
    │                ├── Insert OHLCV rows → NASDAQ_HIST
    │                ├── SPLIT_PROC            (adjust prices for splits)
    │                ├── nasdaq_avg_proc_daily  (5/20/50/150/200-day averages)
    │                ├── RSI_proc              (14-day RSI)
    │                ├── BOLLINGER_proc        (Bollinger Bands)
    │                ├── nasdaq_postive_proc   (price streak screener)
    │                ├── nasdaq_VOL_proc       (volume spike screener)
    │                ├── View snapshots        (PE, funda, QUICK_LOOK_LOG,
    │                │                          DOWN150_VW, rsi2530_log)
    │                ├── Analyze_150_proc      (stocks near 150-day avg)
    │                ├── observer_proc         (populate observer_log)
    │                └── Buy_proc              (update buy signals)
    │              Archive CSV → Downloads\NASDAQ\Nasdaq_bkp\
    │
    └── Step 4 : python NASDAQ_Analytics.py
                 Signal quality back-testing across all tracked symbols
                 Updates ANALYTICS table

---

## If NASDAQ_UPLOAD.py fails mid-run

The script will print a full cleanup SQL block for the failed date, e.g.:

    DELETE FROM NASDAQ_HIST      WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM NASDAQ_AVG       WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM VOL_TOPPERS_HIST WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM PRI_LOG          WHERE INSERT_DATE = DATE '2026-05-31';
    DELETE FROM PRI2_LOG         WHERE INSERT_DATE = DATE '2026-05-31';
    DELETE FROM VOL_LOG          WHERE INSERT_DATE = DATE '2026-05-31';
    DELETE FROM VOL2_LOG         WHERE INSERT_DATE = DATE '2026-05-31';
    DELETE FROM STRONG_POSITIVE  WHERE INS_DATE    = DATE '2026-05-31';
    DELETE FROM ALL_POSITIVE     WHERE INS_DATE    = DATE '2026-05-31';
    DELETE FROM STRONG_NEGITIVE  WHERE INS_DATE    = DATE '2026-05-31';
    DELETE FROM ALL_NEGITIVE     WHERE INS_DATE    = DATE '2026-05-31';
    DELETE FROM BULLISH          WHERE INS_DATE    = DATE '2026-05-31';
    DELETE FROM POS_VOL          WHERE INSERT_DATE = DATE '2026-05-31';
    DELETE FROM NEG_VOL          WHERE INSERT_DATE = DATE '2026-05-31';
    DELETE FROM PE               WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM FUNDA            WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM QUICK_LOOK_LOG   WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM RSI2530_LOG      WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM DOWN150_VW       WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM OBSERVER_LOG     WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM PRICE_POINTS_LOG WHERE TRADEDATE   = DATE '2026-05-31';
    DELETE FROM BUY_LOG_LOG      WHERE TRADEDATE   = DATE '2026-05-31';
    COMMIT;

Run that SQL in SQL*Plus or SQL Developer, fix the root cause, then
re-run python Nasdaq_load.py.

---

## Other scripts (do NOT run these as part of daily load)

| Script                          | When to run                                      |
|---------------------------------|--------------------------------------------------|
| NASDAQ_BACKFILL.py              | One-time historical load of multiple CSV files   |
| Nasdaq_stock_list.py            | Called automatically by Nasdaq_load.py           |
| SPLIT_INFO_DOWNLOAD_YFINANCE.py | Called automatically by Nasdaq_load.py           |
| NASDAQ_UPLOAD.py                | Called automatically by Nasdaq_load.py           |
| NASDAQ_Analytics.py             | Called automatically by Nasdaq_load.py           |
| NASDAQ_STOCK_FUNDA.py           | Run separately to refresh quarterly fundamentals |
| SEC_EDGAR_FUNDAMENTALS.py       | Alternative fundamentals source (run separately) |
| Earnings_calendar.py            | Run separately to fetch upcoming earnings dates  |
| db_inspect.py                   | Ad-hoc DB queries (SELECT only, read-only)       |
