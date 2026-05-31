# Nasdaq Daily Load — Script Flow

## Entry Point
**`Nasdaq_load.py`** — run manually each trading day after CSV download.

---

## Step-by-Step Flow

```
Nasdaq_load.py
│
├── 1. Glob: C:\Users\jenit\Downloads\NASDAQ*.csv
│         Move each CSV → C:\Users\jenit\Downloads\NASDAQ\<filename>
│
├── 2. DB: call stock_split_status()
│         If SPLIT_STOCK_DOWNLOAD_STATUS has rows with DSTATE='N':
│             → run SPLIT_INFO_DOWNLOAD_YFINANCE.py
│               (downloads split data from yfinance into SPLIT_STOCK_DOWNLOAD_content)
│
├── 3. run: python NASDAQ_UPLOAD.py   ← main daily load
│
├── 4. run: python NASDAQ_Analytics.py
│
└── 5. Move processed CSV → C:\Users\jenit\Downloads\NASDAQ\Nasdaq_bkp\
```

---

## NASDAQ_UPLOAD.py — Detail

Reads each `NASDAQ*.csv` from `C:\Users\jenit\Downloads\NASDAQ\` and for every row:

```
csv_read(file)
│
├── INSERT each OHLCV row → NASDAQ_HIST (symbol, tradedate, open, high, low, close, volume)
│   skip duplicates via cx_Oracle.IntegrityError
│
├── DB proc: SPLIT_PROC
│   Reads SPLIT_STOCK_DOWNLOAD_content where STATE_FLAG='N'
│   Adjusts NASDAQ_HIST + NASDAQ_AVG prices/volumes for splits (retroactively)
│   Sets STATE_FLAG='Y' after applying
│
├── DB proc: nasdaq_avg_proc_daily
│   For each symbol in latest tradedate (symbols with len < 5):
│     Computes 5/20/50/150/200-day moving avg for PRICE and VOLUME
│     Computes prev close (PRIVCLOSE), prcnt_change
│     INSERT → NASDAQ_AVG
│   Then logs top-ranked stocks into:
│     pri_log   (price-momentum by 6 price-level brackets)
│     pri2_log  (secondary price log, same brackets)
│     vol_log   (volume-spike by 6 price-level brackets)
│     vol2_log  (secondary volume log)
│   Deletes entries older than 720 days from all four logs
│
├── DB proc: RSI_proc
│   For latest tradedate in NASDAQ_AVG:
│     Computes 14-period Wilder RSI for each symbol
│     UPDATE NASDAQ_AVG.RSI, RSI_AVGU, RSI_AVGD
│
├── DB proc: BOLLINGER_proc
│   For latest tradedate:
│     Calls bollinger() function → standard deviation over 20 days
│     UPDATE NASDAQ_AVG: SD, BU (upper band = 20avg+2*SD), BD (lower band = 20avg-2*SD)
│
├── DB proc: nasdaq_postive_proc
│   Screens for stocks with 3 consecutive days of positive price action
│   Segments by ONEFIFTYAVGVOL bracket:
│     01=0-1, 15=1-5, 516=5-16, 1625=16-25, 2575=25-75, 75=75-125
│   INSERT into all_positive table variants (one per bracket)
│   Also updates avg prices in all_positive from NASDAQ_AVG
│
├── DB proc: nasdaq_VOL_proc
│   Screens for stocks with 3 consecutive days of volume spikes
│   Same 6 brackets as above
│   INSERT into vol_table variants (nasbull_vol_01 etc.)
│
├── INSERT snapshots (views → log tables):
│     PE            ← from P_E view
│     funda         ← from fundav view
│     QUICK_LOOK_LOG← from QUICK_LOOK view
│     Down150_vw    ← from DOWN_150_SELECT_VW view
│     rsi2530_log   ← from rsi2030 view
│
├── DB proc: Analyze_150_proc
│   (source not in repo) Analyzes stocks trading below 150-day avg
│
├── DB proc: observer_proc
│   (source not in repo) Populates observer_log with latest metrics
│   (CURRENTPRICE, RSI, BU, BD, CURR_FUNDA_POINTS, CURR_PRICE_POINTS, etc.)
│
└── DB proc: Buy_proc   (buy_proc.plsql)
    Loop over Buy_log (CATEGORY='R'):
      If symbol in observer_log → update Buy_log from observer_log
      Else if symbol in NASDAQ_AVG latest date:
        Call Funda_point_fn()  → scores fundamentals (revenue 3yr, net income 3yr, cash flow 3yr)
        Call Price_point_fn()  → scores price vs 150avg, 200avg, 3/2/1-yr lows
        UPDATE Buy_log with new points + PROFIT_LOSS + state='CONTINUE'
      Else → state='NOTFOUND'
    Loop over observer_log new candidates (CATEGORY='R', price<1.03*BD, RSI<35):
      If not already in Buy_log → INSERT new buy with state='NEW'
```

---

## NASDAQ_Analytics.py — Detail

Run after UPLOAD. Computes historical signal quality for each tracked symbol.

```
For each symbol in (pri_log ∪ vol_log, last 60 days), excluding donot_track:
  - pcount / vcount      : how many days appeared in price/vol logs (last 90d)
  - PRNK / VRNK          : rank history string (e.g. "1-3-2-")
  - FIRST/LAST_PDATE/VDATE: first and last signal dates
  - PI_PRICE / VI_PRICE  : entry price at first signal date
  - BASE_PRICE           : PI_PRICE (or VI_PRICE if no price signal)
  - FIRST_GROWTH         : % gain 4 days after last signal
  - SECOND_GROWTH        : % gain 8 days after last signal
  - THIRD_GROWTH         : % gain to current date from base
  - FIFTYAVG / ONEFIFTYAVG: from NASDAQ_AVG
  - RECENT_FALL          : min PRCNT_CHANGE in 2 weeks around first signal
  - EPS / Revenue        : from financials table (latest vs prior quarter)
  - P/E                  : at purchase price and current price
  INSERT or UPDATE → ANALYTICS table (flag=0 for active)
  Prune entries older than 75 days → analytics_deleted
```

---

## Key DB Tables

| Table | Written by | Purpose |
|---|---|---|
| NASDAQ_HIST | NASDAQ_UPLOAD.py | Raw OHLCV daily data |
| NASDAQ_AVG | nasdaq_avg_proc_daily | Moving averages, RSI, Bollinger per symbol/date |
| pri_log / pri2_log | nasdaq_avg_proc_daily | Top price-momentum signals, last 720 days |
| vol_log / vol2_log | nasdaq_avg_proc_daily | Top volume-spike signals, last 720 days |
| SPLIT_STOCK_DOWNLOAD_content | SPLIT_INFO_DOWNLOAD_YFINANCE.py | Split ratios; applied by split_proc |
| all_positive variants | nasdaq_postive_proc | 3-day price streak stocks by vol bracket |
| vol_table variants | nasdaq_VOL_proc | 3-day vol spike stocks by bracket |
| observer_log | observer_proc | Current screening candidates with full metrics |
| Buy_log | Buy_proc | Active buy positions + scoring |
| price_points_log | PRICE_POINT_FN | Price scoring detail per symbol per run |
| ANALYTICS | NASDAQ_Analytics.py | Signal quality back-testing per symbol |
| financials | NASDAQ_STOCK_FUNDA.py | Quarterly revenue/EPS fundamentals |

---

## Supporting Scripts (not in daily load)

| Script | Purpose |
|---|---|
| `Nasdaq_stock_list.py` | Downloads/maintains master list of Nasdaq symbols |
| `NASDAQ_STOCK_FUNDA.py` | Downloads quarterly fundamentals → financials table |
| `NASDAQ_BACKFILL.py` | Backfills historical OHLCV for new symbols |
| `SEC_EDGAR_FUNDAMENTALS.py` | Alternative fundamentals source via SEC EDGAR |
| `Quaterly_quickfs.py` / `Test_quickfs.py` | QuickFS API fundamentals fetch |
| `Earnings_calendar.py` | Fetches upcoming earnings dates |
| `US_STOCK_SPLIT_INFO_DOWNLOAD.py` | Downloads split info (Selenium-based) |
| `SPLIT_INFO_DOWNLOAD_YFINANCE.py` | Downloads split info via yfinance (replacement) |
| `db_inspect.py` | Ad-hoc DB inspection utility |

---

## PL/SQL Functions (called internally by procs)

| Function | Called from | Returns |
|---|---|---|
| `nasavg(avgnum, symbol, tradedate, parm)` | nasdaq_avg_proc_daily | N-day moving avg of price or volume |
| `nas_privclose(symbol, tradedate)` | nasdaq_avg_proc_daily | Previous trading day close |
| `bollinger(symbol, tradedate)` | BOLLINGER_proc | 20-day standard deviation |
| `Funda_point_fn(symbol, ins_script)` | Buy_proc | Fundamentals score (revenue/NI/CF 3yr trend) |
| `PRICE_POINT_FN(symbol, ins_script)` | Buy_proc | Price score vs 150/200 avg + multi-yr lows |
| `Min_Max_Price_fn(symbol, Minmax, years)` | PRICE_POINT_FN | Min or max price over N years |
| `nasdaq_tab(symbol, INS_CODE)` | nasdaq_postive_proc | Target table name for price streak insert |
| `nasdaq_vol_tab(symbol, INS_CODE)` | nasdaq_VOL_proc | Target table name for vol streak insert |
| `tch_cnt(symbol, curr_tab)` | nasdaq_postive_proc | Touch count + sequence for symbol in table |
| `tch_vol_cnt(symbol, curr_tab)` | nasdaq_VOL_proc | Touch count for symbol in vol table |

---

## Known Issues / Notes
- `PRICE_POINT_FN` line 69: `NO_DATA_FOUND` guard added 2026-05-30 — if `points_config`
  has no row covering the computed prcnt, defaults to 0 instead of crashing Buy_proc.
- `NASDAQ_UPLOAD.py` and `Nasdaq_load.py` migrated to Python 3 on 2026-05-30.
- `NASDAQ_Analytics.py` still contains Python 2 print statements — needs migration.
- `points_config` must have catch-all rows (VAL_MAX=9999) for all PARAMETER values
  (PRICE_150, PRICE_200, PRICE_3LOW, PRICE_2LOW, PRICE_1LOW) to handle extreme moves.
