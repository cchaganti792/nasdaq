# Nasdaq Stock Analytics Pipeline — Project Overview

## What This Project Does

A personal stock market data pipeline for Nasdaq-listed stocks.  
Raw daily price CSV files are loaded into an Oracle database, technical indicators
are calculated, fundamental data is scraped from the web, and a scoring/ranking
system identifies the best stocks to watch or buy.

---

## High-Level Architecture

```
Daily CSV files (OHLCV)
        │
        ▼
  Nasdaq_load.py          ← master orchestrator, run this every trading day
        │
        ├─► [if splits pending]
        │      SPLIT_INFO_DOWNLOAD_YFINANCE.py   ← fetch split data (Yahoo Finance)
        │      (OLD: US_STOCK_SPLIT_INFO_DOWNLOAD.py — Fidelity, now paywalled, RETIRED)
        │
        ├─► NASDAQ_UPLOAD.py                     ← load OHLCV rows → NASDAQ_HIST
        │       └─ fires PL/SQL chain (see below)
        │
        └─► NASDAQ_Analytics.py                  ← compute analytics scores per symbol


Web scraping (run separately, less frequently):
  NASDAQ_STOCK_FUNDA.py      ← Morningstar fundamentals
  Earnings_calendar.py       ← Zacks earnings history + call transcripts
  Quaterly_quickfs.py        ← QuickFS quarterly financials
  Nasdaq_stock_list.py       ← Nasdaq company master list (symbol/sector/industry)
```

---

## Oracle Database

- **Instance:** `localhost/orcl`
- **Schema/User:** `nasdaq`
- **Credentials:** nasdaq / nasdaq123
- **Client:** `C:\app\User\product\11.2.0\client_1`

### Key Tables

| Table | What it holds |
|-------|---------------|
| `NASDAQ_HIST` | Raw daily OHLCV prices for every symbol |
| `NASDAQ_AVG` | Computed moving averages + daily % change (5/20/50/150/200-day) |
| `NASDAQ_STOCK_LIST` | Master list of all Nasdaq symbols (name, sector, industry, market cap) |
| `SPLIT_STOCK_DOWNLOAD_CONTENT` | Stock split events (symbol, ratio X:Y, ex_date) |
| `SPLIT_STOCK_DOWNLOAD_STATUS` | Tracks which date-windows of split data have been downloaded |
| `ANALYTICS` | Per-symbol analytics roll-up (growth %, EPS, P/E, ranks) |
| `BULLISH` | Active watchlist of bullish candidates with buy flags |
| `BULLISH_LOG` | Daily backup snapshots of BULLISH table |
| `BULLISH_DELETED` | Removed watchlist entries (audit trail) |
| `ALL_POSITIVE` | Screener output: stocks passing price momentum criteria |
| `ALL_NEGITIVE` | Screener output: stocks failing criteria |
| `NEG_VOL` | Symbols showing negative volume signals |
| `PRI_LOG` | Log of top-ranked price movers per day |
| `VOL_LOG` | Log of top-ranked volume movers per day |
| `FINANCIALS` | Income statement data (annual) |
| `FINANCIALS_TTM` | Income statement trailing 12 months |
| `KR_PROFITABILITY` | Morningstar key ratios — profitability |
| `KR_GROWTH` | Morningstar key ratios — growth rates |
| `KR_CASHFLOW` | Morningstar key ratios — cash flow |
| `KR_FINANCIAL_HEALTH_PR` | Morningstar key ratios — balance sheet |
| `LIQUIDITY_FINANCIAL_HEALTH` | Current ratio, quick ratio, debt/equity |
| `KR_EFFICIENCY_RATIOS` | Asset/inventory turnover, days sales outstanding |
| `PAST_EARNINGS` | Historical EPS estimates vs actuals from Zacks |
| `QUICKFS_QUATERLY` | Quarterly revenue/EPS/margins from QuickFS |
| `FUNDA` | Computed fundamentals view (current EPS, revenue snapshot) |
| `PE` | Computed P/E view |
| `US_STOCK_FUNDA_DOWNLOAD_STATUS` | Tracks fundamentals download status per symbol |
| `EARNINGS_DOWNLOAD_TRACKER` | Tracks earnings data download status per symbol |
| `DONOT_TRACK` | Symbols explicitly excluded from analytics |

---

## PL/SQL Stored Procedures (called by NASDAQ_UPLOAD.py after each file load)

| Procedure | Purpose |
|-----------|---------|
| `SPLIT_PROC` | Adjusts historical prices/volumes in NASDAQ_HIST + NASDAQ_AVG for stock splits |
| `NASDAQ_AVG_PROC_DAILY` | Computes 5/20/50/150/200-day price and volume moving averages into NASDAQ_AVG |
| `RSI_PROC` | Calculates 14-day RSI for each symbol |
| `BOLLINGER_PROC` | Calculates Bollinger Bands |
| `NASDAQ_POSTIVE_PROC` | Screener: populates ALL_POSITIVE with bullish candidates |
| `NASDAQ_VOL_PROC` | Screener: populates volume-based signals |
| `ANALYZE_150_PROC` | Identifies stocks trading below 150-day average |
| `OBSERVER_PROC` | Monitors watchlist candidates |
| `BUY_PROC` | Sets buy flags based on scoring rules |
| `STOCK_SPLIT_STATUS` | Prepopulates SPLIT_STOCK_DOWNLOAD_STATUS for upcoming months |

---

## Python Environment

| Item | Detail |
|------|--------|
| Original Python | 2.7 (`C:\Python27\python`) |
| Target Python | 3.x (migration in progress, one script at a time) |
| Oracle driver | `cx_Oracle` (works in both Py2 and Py3) |
| Browser automation | Selenium + Firefox (geckodriver) — used only in scraping scripts |

---

## Current Status (as of May 2026)

| What | Status |
|------|--------|
| Daily price loading | **PAUSED** — last loaded 11-Nov-2022, backfill in progress |
| Split data source | **FIXED** — replaced Fidelity scraper with `SPLIT_INFO_DOWNLOAD_YFINANCE.py` |
| Python 2→3 migration | **IN PROGRESS** — starting with core pipeline scripts |
| Fundamentals scraping | **BROKEN** — Morningstar export format changed |
| Earnings scraping | **BROKEN** — Zacks page structure changed |
| Buy signal / Bullish logic | **NOT VERIFIED** — needs review after price data is current |

---

## Normal Daily Workflow (once pipeline is healthy)

1. Download the day's Nasdaq OHLCV CSV file and place in `C:\Users\jenit\Downloads\`
2. Run: `python Nasdaq_load.py`
3. It auto-detects the file, checks for splits, uploads prices, runs all PL/SQL, updates analytics

---

## Backfill Plan (Nov 2022 → today)

1. **DONE (or run once):** `python SPLIT_INFO_DOWNLOAD_YFINANCE.py`  
   → loads all stock splits Nov-2022 to today into Oracle
2. Place all daily CSV files into `C:\Users\jenit\Downloads\`
3. Run `Nasdaq_load.py` — it will process them in sequence

---

*Last updated: May 2026 — during Python 3 migration and Nov-2022 backfill*
