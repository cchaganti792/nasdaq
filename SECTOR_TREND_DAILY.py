"""
SECTOR_TREND_DAILY.py  -  Python 3
Daily sector / industry trend snapshot.

For the latest TRADEDATE in nasdaq_avg, aggregates 5 trend signals per
(SECTOR, INDUSTRY) by joining nasdaq_avg with nasdaq_stock_list.  Also
inserts one rollup row per SECTOR with INDUSTRY='ALL' so the broad
sector trend is queryable in a single filter.

Signals (all per industry):
    AVG_PCT_CHANGE  - avg of today's PRCNT_CHANGE
    BREADTH_PCT     - % of stocks that closed up
    VOLUME_SURGE    - avg of (CURRENTVOL / TWENTYAVGVOL); 1.5 = 50% above avg
    AVG_RSI         - avg RSI
    PCT_ABOVE_50MA  - % of stocks where CURRENTPRICE > FIFTYAVGPRI

Filters:
    - Only industries with >= MIN_STOCKS_PER_INDUSTRY listed stocks are kept.
    - Re-runnable: DELETEs existing rows for the tradedate before INSERT.

Output table — RUN ONCE in SQL Developer before first run:

    CREATE TABLE SECTOR_TREND_DAILY (
        TRADEDATE         DATE          NOT NULL,
        SECTOR            VARCHAR2(30)  NOT NULL,
        INDUSTRY          VARCHAR2(100) NOT NULL,
        STOCK_COUNT       NUMBER,
        AVG_PCT_CHANGE    NUMBER(8,2),
        BREADTH_PCT       NUMBER(5,2),
        VOLUME_SURGE      NUMBER(8,2),
        AVG_RSI           NUMBER(5,2),
        PCT_ABOVE_50MA    NUMBER(5,2),
        INS_DATE          DATE DEFAULT SYSDATE,
        CONSTRAINT SECTOR_TREND_DAILY_PK PRIMARY KEY (TRADEDATE, SECTOR, INDUSTRY)
    );
"""

import oracledb

ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)

connection = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
cursor     = connection.cursor()

MIN_STOCKS_PER_INDUSTRY = 5
SEP = '=' * 95

print(SEP)
print('  SECTOR_TREND_DAILY.py')

# ── Resolve tradedate ─────────────────────────────────────────────────────
cursor.execute("SELECT MAX(TRADEDATE) FROM nasdaq_avg")
tradedate = cursor.fetchone()[0]
if tradedate is None:
    print('  No data in nasdaq_avg — nothing to do.')
    print(SEP)
    raise SystemExit(0)

print(f'  tradedate : {tradedate.date()}')
print(SEP)

# ── Idempotent re-run: clear existing rows for this tradedate ─────────────
cursor.execute("DELETE FROM SECTOR_TREND_DAILY WHERE TRADEDATE = :dt", dt=tradedate)
deleted = cursor.rowcount

# ── Industry-level rows ───────────────────────────────────────────────────
cursor.execute(
    """INSERT INTO SECTOR_TREND_DAILY
       (TRADEDATE, SECTOR, INDUSTRY, STOCK_COUNT, AVG_PCT_CHANGE,
        BREADTH_PCT, VOLUME_SURGE, AVG_RSI, PCT_ABOVE_50MA, INS_DATE)
       SELECT
           a.TRADEDATE,
           sl.SECTOR,
           sl.INDUSTRY,
           COUNT(*) AS STOCK_COUNT,
           ROUND(AVG(a.PRCNT_CHANGE), 2) AS AVG_PCT_CHANGE,
           ROUND(SUM(CASE WHEN a.PRCNT_CHANGE > 0 THEN 1 ELSE 0 END) * 100
                 / COUNT(*), 2) AS BREADTH_PCT,
           ROUND(AVG(CASE WHEN a.TWENTYAVGVOL > 0
                          THEN a.CURRENTVOL / a.TWENTYAVGVOL
                          ELSE NULL END), 2) AS VOLUME_SURGE,
           ROUND(AVG(a.RSI), 2) AS AVG_RSI,
           ROUND(SUM(CASE WHEN a.CURRENTPRICE > a.FIFTYAVGPRI THEN 1 ELSE 0 END) * 100
                 / COUNT(*), 2) AS PCT_ABOVE_50MA,
           SYSDATE
       FROM nasdaq_avg a
       JOIN nasdaq_stock_list sl ON sl.SYMBOL = a.SYMBOL
       WHERE a.TRADEDATE = :dt
         AND sl.SECTOR   IS NOT NULL
         AND sl.INDUSTRY IS NOT NULL
       GROUP BY a.TRADEDATE, sl.SECTOR, sl.INDUSTRY
       HAVING COUNT(*) >= :min_cnt""",
    dt=tradedate, min_cnt=MIN_STOCKS_PER_INDUSTRY
)
industry_rows = cursor.rowcount

# ── Sector-level rollup rows (INDUSTRY='ALL') ─────────────────────────────
cursor.execute(
    """INSERT INTO SECTOR_TREND_DAILY
       (TRADEDATE, SECTOR, INDUSTRY, STOCK_COUNT, AVG_PCT_CHANGE,
        BREADTH_PCT, VOLUME_SURGE, AVG_RSI, PCT_ABOVE_50MA, INS_DATE)
       SELECT
           a.TRADEDATE,
           sl.SECTOR,
           'ALL' AS INDUSTRY,
           COUNT(*) AS STOCK_COUNT,
           ROUND(AVG(a.PRCNT_CHANGE), 2) AS AVG_PCT_CHANGE,
           ROUND(SUM(CASE WHEN a.PRCNT_CHANGE > 0 THEN 1 ELSE 0 END) * 100
                 / COUNT(*), 2) AS BREADTH_PCT,
           ROUND(AVG(CASE WHEN a.TWENTYAVGVOL > 0
                          THEN a.CURRENTVOL / a.TWENTYAVGVOL
                          ELSE NULL END), 2) AS VOLUME_SURGE,
           ROUND(AVG(a.RSI), 2) AS AVG_RSI,
           ROUND(SUM(CASE WHEN a.CURRENTPRICE > a.FIFTYAVGPRI THEN 1 ELSE 0 END) * 100
                 / COUNT(*), 2) AS PCT_ABOVE_50MA,
           SYSDATE
       FROM nasdaq_avg a
       JOIN nasdaq_stock_list sl ON sl.SYMBOL = a.SYMBOL
       WHERE a.TRADEDATE = :dt
         AND sl.SECTOR IS NOT NULL
       GROUP BY a.TRADEDATE, sl.SECTOR
       HAVING COUNT(*) >= :min_cnt""",
    dt=tradedate, min_cnt=MIN_STOCKS_PER_INDUSTRY
)
sector_rows = cursor.rowcount
connection.commit()

if deleted:
    print(f'  Cleared prior rows       : {deleted}')
print(f'  Industry rows inserted   : {industry_rows}')
print(f'  Sector rollup rows       : {sector_rows}')

# ── Print helpers ─────────────────────────────────────────────────────────
def _fmt_val(v, suffix=''):
    if v is None:
        return f'{"-":>6}'
    if suffix == '%':
        return f'{v:>5.1f}%'
    if suffix == 'x':
        return f'{v:>4.2f}x'
    return f'{v:>+5.2f}'

def _print_table(rows, sector_w=22, industry_w=32):
    hdr = (f"    {'Sector':<{sector_w}}{'Industry':<{industry_w}}"
           f"{'stocks':>7}  {'chg%':>6}  {'brdth':>6}  {'vol×':>5}  {'RSI':>4}  {'>50MA':>6}")
    print(hdr)
    print('    ' + '-' * (len(hdr) - 4))
    for r in rows:
        sec, ind, cnt, chg, brd, vol, rsi, pma = r
        sec_s = (sec or '')[:sector_w].ljust(sector_w)
        ind_s = (ind or '')[:industry_w].ljust(industry_w)
        print(f"    {sec_s}{ind_s}"
              f"{cnt:>7}  {_fmt_val(chg):>6}  {_fmt_val(brd, '%'):>6}  "
              f"{_fmt_val(vol, 'x'):>5}  {_fmt_val(rsi):>4}  {_fmt_val(pma, '%'):>6}")

# ── Top 10 trending up (by AVG_PCT_CHANGE, industry-level) ────────────────
cursor.execute(
    """SELECT SECTOR, INDUSTRY, STOCK_COUNT, AVG_PCT_CHANGE, BREADTH_PCT,
              VOLUME_SURGE, AVG_RSI, PCT_ABOVE_50MA
       FROM SECTOR_TREND_DAILY
       WHERE TRADEDATE = :dt AND INDUSTRY <> 'ALL'
       ORDER BY AVG_PCT_CHANGE DESC NULLS LAST
       FETCH FIRST 10 ROWS ONLY""",
    dt=tradedate
)
top_up = cursor.fetchall()

print()
print('  Top 10 trending UP (industry, by avg % change):')
_print_table(top_up)

# ── Top 10 volume surge (institutional rotation signal) ───────────────────
cursor.execute(
    """SELECT SECTOR, INDUSTRY, STOCK_COUNT, AVG_PCT_CHANGE, BREADTH_PCT,
              VOLUME_SURGE, AVG_RSI, PCT_ABOVE_50MA
       FROM SECTOR_TREND_DAILY
       WHERE TRADEDATE = :dt AND INDUSTRY <> 'ALL'
       ORDER BY VOLUME_SURGE DESC NULLS LAST
       FETCH FIRST 10 ROWS ONLY""",
    dt=tradedate
)
top_vol = cursor.fetchall()

print()
print('  Top 10 volume surge (institutional rotation signal):')
_print_table(top_vol)

# ── Sector rollup snapshot (all 11 broad sectors) ─────────────────────────
cursor.execute(
    """SELECT SECTOR, INDUSTRY, STOCK_COUNT, AVG_PCT_CHANGE, BREADTH_PCT,
              VOLUME_SURGE, AVG_RSI, PCT_ABOVE_50MA
       FROM SECTOR_TREND_DAILY
       WHERE TRADEDATE = :dt AND INDUSTRY = 'ALL'
       ORDER BY AVG_PCT_CHANGE DESC NULLS LAST""",
    dt=tradedate
)
sector_summary = cursor.fetchall()

print()
print(f'  Sector rollup ({len(sector_summary)} broad sectors, sorted by avg % change):')
_print_table(sector_summary)

print(SEP)
