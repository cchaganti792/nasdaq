# Script Map — Functions, Inputs, Outputs, and Relations

## Quick Reference — Who Calls Who

```
Nasdaq_load.py
  ├── calls  SPLIT_INFO_DOWNLOAD_YFINANCE.py   (Python 3 — CURRENT)
  │          [OLD: US_STOCK_SPLIT_INFO_DOWNLOAD.py — RETIRED]
  ├── calls  NASDAQ_UPLOAD.py
  │            └── calls Oracle procs: SPLIT_PROC → NASDAQ_AVG_PROC_DAILY
  │                                  → RSI_PROC → BOLLINGER_PROC
  │                                  → NASDAQ_POSTIVE_PROC → NASDAQ_VOL_PROC
  │                                  → ANALYZE_150_PROC → OBSERVER_PROC → BUY_PROC
  └── calls  NASDAQ_Analytics.py

Run separately (not called by Nasdaq_load.py):
  Nasdaq_stock_list.py
  NASDAQ_STOCK_FUNDA.py
  Earnings_calendar.py         uses Page.py (shared browser)
  Quaterly_quickfs.py          uses Page.py (shared browser)
```

---

## Script Details

---

### `Nasdaq_load.py`
**Role:** Master pipeline orchestrator. Run this every trading day.  
**Python:** 3 compatible (already uses `print()`)  
**Status:** Working — updated to call new split script

**What it does:**
1. Globs for `NASDAQ*.csv` in `C:\Users\jenit\Downloads\`
2. Moves each file to `C:\Users\jenit\Downloads\NASDAQ\`
3. Calls `stock_split_status` Oracle proc (prepopulates split status table)
4. Checks `SPLIT_STOCK_DOWNLOAD_STATUS where DSTATE='N'`
5. If splits pending → runs `SPLIT_INFO_DOWNLOAD_YFINANCE.py`
6. Runs `NASDAQ_UPLOAD.py`
7. Runs `NASDAQ_Analytics.py`
8. Moves processed file to `Nasdaq_bkp\`

**Reads from DB:** `SPLIT_STOCK_DOWNLOAD_STATUS`  
**Calls scripts:** `SPLIT_INFO_DOWNLOAD_YFINANCE.py`, `NASDAQ_UPLOAD.py`, `NASDAQ_Analytics.py`

---

### `SPLIT_INFO_DOWNLOAD_YFINANCE.py`  ← NEW (May 2026)
**Role:** Download stock split data from Yahoo Finance. Replaces retired Fidelity scraper.  
**Python:** 3  
**Status:** NEW — written May 2026, replaces `US_STOCK_SPLIT_INFO_DOWNLOAD.py`  
**Dependencies:** `pip install yfinance cx_Oracle`

**What it does:**
1. Connects to Oracle
2. Reads all distinct symbols from `nasdaq_hist` (symbols we actually track)
3. For each symbol: calls `yfinance.Ticker(symbol).splits`
4. Filters splits to BACKFILL_START (11-Nov-2022) → today
5. Converts float ratio (e.g. 4.0) to "X:Y" string (e.g. "4:1") using `Fraction`
6. Inserts into `SPLIT_STOCK_DOWNLOAD_CONTENT`
7. Updates `SPLIT_STOCK_DOWNLOAD_STATUS` → `DSTATE='Y'` for all processed months

**Reads from DB:** `NASDAQ_HIST` (to get symbol list)  
**Writes to DB:** `SPLIT_STOCK_DOWNLOAD_CONTENT`, `SPLIT_STOCK_DOWNLOAD_STATUS`  
**Called by:** `Nasdaq_load.py`

**Key function:**
- `ratio_to_str(float)` — converts yfinance ratio float to "X:Y" string
- `insert_split(symbol, ratio_str, ex_date)` — inserts one split row, skips on duplicate

---

### `US_STOCK_SPLIT_INFO_DOWNLOAD.py`  ← RETIRED
**Role:** Old Fidelity-based split scraper.  
**Python:** 2 (mixed)  
**Status:** RETIRED — Fidelity website now requires subscription. Replaced by `SPLIT_INFO_DOWNLOAD_YFINANCE.py`

**Was doing:** Opened Firefox, scraped `eresearch.fidelity.com/eresearch/conferenceCalls.jhtml?tab=splits`  
**Replaced by:** `SPLIT_INFO_DOWNLOAD_YFINANCE.py`

---

### `NASDAQ_UPLOAD.py`
**Role:** Load one day's OHLCV CSV into `NASDAQ_HIST` and fire the full PL/SQL analytics chain.  
**Python:** 2 — **needs migration to Python 3**  
**Status:** Working on Python 2, migration pending

**What it does:**
1. Globs `NASDAQ*.csv` in `C:\Users\jenit\Downloads\NASDAQ\`
2. For each row in CSV → inserts into `NASDAQ_HIST` (SYMBOL, TRADEDATE, OPEN, HIGH, LOW, CLOSE, VOLUME)
3. After insert, calls Oracle proc chain:
   - `SPLIT_PROC` — apply any splits
   - `NASDAQ_AVG_PROC_DAILY` — compute moving averages
   - `RSI_PROC` — compute RSI
   - `BOLLINGER_PROC` — compute Bollinger Bands
   - `NASDAQ_POSTIVE_PROC` — run screener
   - `NASDAQ_VOL_PROC` — volume screener
   - `ANALYZE_150_PROC`, `OBSERVER_PROC`, `BUY_PROC` — signal generation
4. Also inserts into PE, FUNDA, QUICK_LOOK_LOG, RSI2530_LOG, DOWN150_VW views
5. Moves processed file to `Nasdaq_bkp\`

**Input:** CSV format: `SYMBOL, TRADEDATE(dd-mon-yy), OPEN, HIGH, LOW, CLOSE, VOLUME`  
**Writes to DB:** `NASDAQ_HIST`  
**Calls Oracle procs:** Full chain (see above)  
**Called by:** `Nasdaq_load.py`

**Python 2 syntax to fix for migration:**
- `print values` → `print(values)`
- cx_Oracle named bind params (`:vSYMBOL` style) — works fine in Py3

---

### `NASDAQ_Analytics.py`
**Role:** Compute 20+ analytics metrics per symbol and store in `ANALYTICS` table.  
**Python:** 2 — **needs migration to Python 3**  
**Status:** Working on Python 2, migration pending

**What it does:**  
For each symbol active in the last 60 days (from `PRI_LOG` and `VOL_LOG`):
1. Price/volume appearance count (pcount, vcount)
2. Price rank history string (PRNK) and volume rank string (VRNK)
3. First/last appearance dates for price and volume signals
4. Base price (price when first signalled)
5. Growth at 3 time points: +0 days, +4 days, current
6. 50-day and 150-day moving averages
7. Recent maximum drawdown (RECENT_FALL)
8. Previous and current EPS from `FINANCIALS`
9. Previous and current Revenue
10. P/E at purchase and current P/E
11. Insert new record or update existing in `ANALYTICS`
12. Deletes entries older than 75 days (archives to `ANALYTICS_DELETED`)

**Reads from DB:** `PRI_LOG`, `VOL_LOG`, `NASDAQ_HIST`, `NASDAQ_AVG`, `FINANCIALS`, `DONOT_TRACK`  
**Writes to DB:** `ANALYTICS`, `ANALYTICS_DELETED`  
**Called by:** `Nasdaq_load.py`

---

### `Nasdaq_Bullish.py`
**Role:** Maintain the `BULLISH` watchlist — stocks actively being monitored for buy signals.  
**Python:** 2 — **needs migration to Python 3**  
**Status:** Working on Python 2, migration pending

**What it does (sign system):**
- sign=01 → Insert from `ALL_POSITIVE` screener (new candidates)
- sign=02 → Tag stocks below their 50/150-day average (potential bounce candidates)
- sign=04 → Tag intersection of `ANALYTICS` and `ALL_POSITIVE` (doubly confirmed)
- sign=05 → Update with current price, % change, total growth, moving averages
- sign=06 → Update with EPS, Revenue, P/E from `FUNDA`
- sign=07 → Update volume high data from `VOL_TOPPERS_HIST`
- sign=00 → Calculate RSI for each bullish stock
- Final → Set BUY_FLAG, compute top growth ranks, prune stale/negative stocks

**BULL_CODE bitmask:** 1=from price screener, 2=below avg, 4=in analytics+positive intersection  
**Reads from DB:** `ALL_POSITIVE`, `ANALYTICS`, `NASDAQ_AVG`, `FUNDA`, `VOL_TOPPERS_HIST`, `ALL_NEGITIVE`, `NEG_VOL`  
**Writes to DB:** `BULLISH`, `BULLISH_LOG`, `BULLISH_DELETED`

---

### `Nasdaq_stock_list.py`
**Role:** Load Nasdaq company master list (symbol, name, sector, industry, market cap).  
**Python:** 2 — **needs migration to Python 3**  
**Status:** Working on Python 2, migration pending

**What it does:**
- Reads `companylist*.csv` files from `C:\Users\User\Downloads\`
- Inserts into `NASDAQ_STOCK_LIST` (skips duplicates)

**Input CSV columns:** Symbol, Name, LastSale, MarketCap, IPOYear, Sector, Industry, URL  
**Writes to DB:** `NASDAQ_STOCK_LIST`  
**Run:** Manually, when new companies are listed or master list needs refreshing

---

### `NASDAQ_STOCK_FUNDA.py`
**Role:** Scrape Morningstar key ratios and financial statements for each symbol.  
**Python:** 2 — **needs migration to Python 3**  
**Status:** BROKEN — Morningstar changed export format/availability  

**What it does:**
- Opens Firefox, navigates to `financials.morningstar.com/ratios/r.html?t=SYMBOL`
- Clicks "Export" button to download CSV
- Parses CSV for 8 sections: Financials, Profitability, Growth, CashFlow, FinancialHealth, Liquidity, EfficiencyRatios
- Inserts into corresponding Oracle tables (with TTM and historical variants)
- Tracks status in `US_STOCK_FUNDA_DOWNLOAD_STATUS`

**Writes to DB:** `FINANCIALS`, `FINANCIALS_TTM`, `KR_PROFITABILITY`, `KR_GROWTH`, `KR_CASHFLOW`, `KR_FINANCIAL_HEALTH_PR`, `LIQUIDITY_FINANCIAL_HEALTH`, `KR_EFFICIENCY_RATIOS`  
**Reads from DB:** `US_STOCK_FUNDA_DOWNLOAD_STATUS`

---

### `Earnings_calendar.py`
**Role:** Scrape past earnings announcements and call transcripts from Zacks.  
**Python:** 2 — **needs migration to Python 3**  
**Status:** BROKEN — Zacks page structure/XPath changed  
**Uses:** `Page.py` (shared Selenium Firefox browser instance)

**What it does:**
1. Merges new symbols into `EARNINGS_DOWNLOAD_TRACKER`
2. For each pending symbol: opens `zacks.com/stock/research/SYMBOL/earnings-announcements`
3. Scrapes earnings table: date, period, estimated EPS, reported EPS, surprise %
4. Also downloads earnings call transcripts as `.txt` files to `C:\FS\JEN_DAT\UPLOADS\Earnings\SYMBOL\`
5. Tracks status in `EARNINGS_DOWNLOAD_TRACKER`

**Writes to DB:** `PAST_EARNINGS`, `EARNINGS_DOWNLOAD_TRACKER`  
**Writes files:** Earnings call transcripts as UTF-8 `.txt` files

---

### `Quaterly_quickfs.py`
**Role:** Scrape quarterly financial data from QuickFS.net.  
**Python:** 2 — **needs migration to Python 3**  
**Status:** Likely broken — QuickFS page structure may have changed  
**Uses:** `Page.py` (shared Selenium Firefox browser instance)

**What it does:**
- Opens `quickfs.net/company/SYMBOL`
- Switches to Quarterly view
- Scrapes table: Revenue, Gross Profit, Operating Profit, EPS + growth %, ROA, ROE, ROIC
- Inserts into `QUICKFS_QUATERLY`

**Writes to DB:** `QUICKFS_QUATERLY`  
**Reads from DB:** `US_STOCK_FUNDA_DOWNLOAD_STATUS`

---

### `Page.py`
**Role:** Shared Selenium browser singleton used by Earnings_calendar and Quaterly_quickfs.  
**Python:** 2 — **needs migration to Python 3**  
**Status:** Working (just a browser wrapper)

**Exports:** `browser` (global Firefox WebDriver instance), `open(url)` function

---

## PL/SQL Files (stored procedures — stored in Oracle, files here are source copies)

| File | Procedure | What it does |
|------|-----------|--------------|
| `split_proc.plsql` | `SPLIT_PROC` | For each split in `SPLIT_STOCK_DOWNLOAD_CONTENT` where `EX_DATE=tradedate` and `STATE_FLAG='N'`: multiply all prior CLOSE/OPEN/HIGH/LOW by (second/first) and VOLUME by (first/second). Sets STATE_FLAG='Y' after applying. |
| `nasdaq_avg_proc_daily.plsql` | `NASDAQ_AVG_PROC_DAILY` | For each symbol on today's date: computes 5/20/50/150/200-day price averages and 5/20/50/150-day volume averages. Inserts into `NASDAQ_AVG`. Also populates `PRI_LOG`, `VOL_LOG` with daily top movers. |
| `RSI_proc.plsql` | `RSI_PROC` | Computes 14-day RSI using Wilder's method |
| `BOLLINGER_proc.plsql` | `BOLLINGER_PROC` | Computes Bollinger Bands (20-day SMA ± 2 stddev) |
| `nasdaq_postive_proc.plsql` | `NASDAQ_POSTIVE_PROC` | Identifies symbols passing price momentum criteria → `ALL_POSITIVE` |
| `nasdaq_VOL_proc.plsql` | `NASDAQ_VOL_PROC` | Identifies symbols with high volume activity → screener tables |

---

## Data Flow Diagram

```
Yahoo Finance ──► SPLIT_INFO_DOWNLOAD_YFINANCE.py
                         │
                         ▼
                 SPLIT_STOCK_DOWNLOAD_CONTENT
                         │
                         ▼ (read by SPLIT_PROC)

Daily CSV files ──► NASDAQ_UPLOAD.py ──► NASDAQ_HIST
                                              │
                                         SPLIT_PROC ──► adjusts NASDAQ_HIST + NASDAQ_AVG
                                              │
                                    NASDAQ_AVG_PROC_DAILY ──► NASDAQ_AVG, PRI_LOG, VOL_LOG
                                              │
                                         RSI_PROC ──► RSI in NASDAQ_AVG
                                              │
                                      BOLLINGER_PROC ──► Bollinger in NASDAQ_AVG
                                              │
                                   NASDAQ_POSTIVE_PROC ──► ALL_POSITIVE
                                              │
                                      NASDAQ_VOL_PROC ──► ALL_NEGITIVE, NEG_VOL
                                              │
                                    ANALYZE_150_PROC, OBSERVER_PROC, BUY_PROC
                                              │
                                              ▼
                                   NASDAQ_Analytics.py ──► ANALYTICS
                                              │
                                   Nasdaq_Bullish.py ──► BULLISH (watchlist + buy flags)


Morningstar ──► NASDAQ_STOCK_FUNDA.py ──► FINANCIALS, KR_* tables
Zacks       ──► Earnings_calendar.py  ──► PAST_EARNINGS + .txt transcript files
QuickFS     ──► Quaterly_quickfs.py   ──► QUICKFS_QUATERLY
Nasdaq.com  ──► Nasdaq_stock_list.py  ──► NASDAQ_STOCK_LIST
```

---

## Migration Status Tracker

| Script | Python 3 ready | Status |
|--------|---------------|--------|
| `Nasdaq_load.py` | YES (was already compatible) | Active |
| `SPLIT_INFO_DOWNLOAD_YFINANCE.py` | YES | Active — new script |
| `US_STOCK_SPLIT_INFO_DOWNLOAD.py` | — | RETIRED |
| `NASDAQ_UPLOAD.py` | NO | Next to migrate |
| `NASDAQ_Analytics.py` | NO | Pending |
| `Nasdaq_Bullish.py` | NO | Pending |
| `Nasdaq_stock_list.py` | NO | Pending |
| `NASDAQ_STOCK_FUNDA.py` | NO | Pending + broken (Morningstar) |
| `Earnings_calendar.py` | NO | Pending + broken (Zacks XPath) |
| `Quaterly_quickfs.py` | NO | Pending + may be broken |
| `Page.py` | NO | Pending |

---

*Last updated: May 2026 — SPLIT_INFO_DOWNLOAD_YFINANCE.py added, US_STOCK_SPLIT_INFO_DOWNLOAD.py retired*
