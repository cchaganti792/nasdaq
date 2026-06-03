"""
nasdaq_avg_proc_daily.py  -  Python equivalent of Oracle nasdaq_avg_proc_daily procedure

Oracle signature:
    nasdaq_avg_proc_daily(TRADEDATE IN DATE DEFAULT NULL)

What it does:
    Phase 1 — nasdaq_avg insert:
        For each symbol (length < 5) in nasdaq_hist on the given tradedate,
        compute PRIVCLOSE + 9 moving averages (5/20/50/150/200-day price,
        5/20/50/150-day volume) using nas_privclose() and nasavg(), then
        insert one row into nasdaq_avg. Skips entirely if nasdaq_avg already
        has rows for that date (idempotent).

    Phase 2 — vol_toppers snapshot:
        INSERT INTO vol_toppers_hist SELECT * FROM vol_toppers

    Phase 3 — signal log inserts:
        Top-ranked rows from 6 nasbull_pri_* views  -> pri_log  (rank < 20)
        Top-ranked rows from 6 nasbull_pri2_* views -> pri2_log (rank < 20)
        Top-ranked rows from 6 nasbull_vol_* views  -> vol_log  (rank < 25)
        Top-ranked rows from 6 nasbull_vol2_* views -> vol2_log (rank < 20)

    Phase 4 — cleanup:
        DELETE log rows older than 720 days from pri_log, vol_log, pri2_log, vol2_log

Usage (in NASDAQ_UPLOAD.py, replacing run_proc call):
    from procs.nasdaq_avg_proc_daily import nasdaq_avg_proc_daily
    nasdaq_avg_proc_daily(connection, cursor, tradedate)

Fallback:
    If this Python version has any issue, the Oracle proc still exists in the DB.
    In NASDAQ_UPLOAD.py restore: run_proc('nasdaq_avg_proc_daily', tradedate)
"""

import math
import sys
import os
from datetime import datetime

# allow running as __main__ from project root or from procs/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procs.nasavg_fn import nasavg
from procs.nas_privclose_fn import nas_privclose


_PRI_VIEWS = [
    'nasbull_pri_01', 'nasbull_pri_15', 'nasbull_pri_516',
    'nasbull_pri_1625', 'nasbull_pri_2575', 'nasbull_pri_75',
]
_PRI2_VIEWS = [
    'nasbull_pri2_01', 'nasbull_pri2_15', 'nasbull_pri2_516',
    'nasbull_pri2_1625', 'nasbull_pri2_2575', 'nasbull_pri2_75',
]
_VOL_VIEWS = [
    'nasbull_vol_01', 'nasbull_vol_15', 'nasbull_vol_516',
    'nasbull_vol_1625', 'nasbull_vol_2575', 'nasbull_vol_75',
]
_VOL2_VIEWS = [
    'nasbull_vol2_01', 'nasbull_vol2_15', 'nasbull_vol2_516',
    'nasbull_vol2_1625', 'nasbull_vol2_2575', 'nasbull_vol2_75',
]


def nasdaq_avg_proc_daily(connection, cursor, tradedate=None):
    # ── Resolve tradedate ─────────────────────────────────────────────────
    if tradedate is None:
        cursor.execute("SELECT MAX(TRADEDATE) FROM nasdaq_hist")
        v_date = cursor.fetchone()[0]
    elif isinstance(tradedate, str):
        v_date = datetime.strptime(tradedate, '%Y-%m-%d').date()
    else:
        v_date = tradedate

    # ── Idempotency guard ─────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM nasdaq_avg WHERE TRADEDATE = :dt", dt=v_date)
    if cursor.fetchone()[0] > 0:
        print(f"    {'nasdaq_avg_proc_daily':<28} already loaded for {v_date} — skipped")
        return

    # ── Phase 1: compute averages and insert into nasdaq_avg ──────────────
    cursor.execute(
        "SELECT DISTINCT symbol FROM nasdaq_hist "
        "WHERE LENGTH(symbol) < 5 AND TRADEDATE = :dt ORDER BY symbol",
        dt=v_date
    )
    symbols = [r[0] for r in cursor.fetchall()]

    inserted = 0
    for sym in symbols:
        privclose = nas_privclose(cursor, sym, v_date)
        avg5p     = nasavg(cursor, 5,   sym, v_date, 'CLOSE')
        avg20p    = nasavg(cursor, 20,  sym, v_date, 'CLOSE')
        avg50p    = nasavg(cursor, 50,  sym, v_date, 'CLOSE')
        avg150p   = nasavg(cursor, 150, sym, v_date, 'CLOSE')
        avg200p   = nasavg(cursor, 200, sym, v_date, 'CLOSE')
        avg5v     = nasavg(cursor, 5,   sym, v_date, 'VOLUME')
        avg20v    = nasavg(cursor, 20,  sym, v_date, 'VOLUME')
        avg50v    = nasavg(cursor, 50,  sym, v_date, 'VOLUME')
        avg150v   = nasavg(cursor, 150, sym, v_date, 'VOLUME')

        cursor.execute(
            "SELECT OPEN, CLOSE, VOLUME FROM nasdaq_hist "
            "WHERE TRADEDATE = :dt AND SYMBOL = :sym",
            dt=v_date, sym=sym
        )
        row = cursor.fetchone()
        if not row:
            continue
        open_price, close_price, volume = float(row[0]), float(row[1]), float(row[2])

        # NVL(TRUNC(((CURRENTPRICE - PRIVCLOSE) / NULLIF(PRIVCLOSE, 0)) * 100, 2), 0)
        if privclose == 0:
            prcnt_change = 0.0
        else:
            prcnt_change = math.trunc(((close_price - privclose) / privclose) * 10000) / 100

        cursor.execute(
            "INSERT INTO nasdaq_avg "
            "(SYMBOL, TRADEDATE, PRIVCLOSE, OPEN, CURRENTPRICE, PRCNT_CHANGE, "
            " FIVEDAYAVGPRI, TWENTYAVGPRI, FIFTYAVGPRI, ONEFIFTYAVGPRI, TWOHUNAVGPRI, "
            " CURRENTVOL, FIVEDAYVOL, TWENTYAVGVOL, FIFTYAVGVOL, ONEFIFTYAVGVOL) "
            "VALUES (:sym, :dt, :priv, :opn, :curr, :prcnt, "
            "        :avg5p, :avg20p, :avg50p, :avg150p, :avg200p, "
            "        :cvol, :avg5v, :avg20v, :avg50v, :avg150v)",
            sym=sym, dt=v_date, priv=privclose, opn=open_price, curr=close_price,
            prcnt=prcnt_change,
            avg5p=avg5p, avg20p=avg20p, avg50p=avg50p, avg150p=avg150p, avg200p=avg200p,
            cvol=volume/100000,
            avg5v=avg5v/100000, avg20v=avg20v/100000,
            avg50v=avg50v/100000, avg150v=avg150v/100000,
        )
        inserted += 1

    connection.commit()
    print(f"    {'nasdaq_avg':<28}: {inserted} rows inserted  |  date: {v_date}")

    # ── Phase 2: vol_toppers snapshot ─────────────────────────────────────
    cursor.execute("INSERT INTO vol_toppers_hist SELECT * FROM vol_toppers")
    connection.commit()
    print(f"    {'vol_toppers_hist':<28}: snapshot done")

    # ── Phase 3: signal log inserts ───────────────────────────────────────
    pri_sel = (
        "SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,"
        "TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,"
        "(SELECT MAX(TRADEDATE) FROM nasdaq_hist) AS Insert_date"
    )
    vol_sel = (
        "SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,"
        "FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,"
        "FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,"
        "(SELECT MAX(TRADEDATE) FROM nasdaq_hist) AS Insert_date"
    )

    def _log_insert(table, views, sel_cols, rank_col, rank_limit):
        rows = 0
        for view in views:
            cursor.execute(
                f"INSERT INTO {table} "
                f"SELECT {sel_cols}, '{view}' AS Inser_script "
                f"FROM (SELECT {sel_cols.replace(f',rnk,', ',')}"
                f"            ,DENSE_RANK() OVER (ORDER BY {rank_col} DESC) AS rnk"
                f"      FROM {view}) "
                f"WHERE rnk < {rank_limit}"
            )
            rows += cursor.rowcount
        return rows

    pri_rows  = _log_insert('pri_log',  _PRI_VIEWS,  pri_sel, 'TOTPRICEPRCNT',   20)
    pri2_rows = _log_insert('pri2_log', _PRI2_VIEWS, pri_sel, 'TOTPRICEPRCNT',   20)
    vol_rows  = _log_insert('vol_log',  _VOL_VIEWS,  vol_sel, 'TOTDIFFVOLPRCNT', 25)
    vol2_rows = _log_insert('vol2_log', _VOL2_VIEWS, vol_sel, 'TOTDIFFVOLPRCNT', 20)
    connection.commit()
    print(f"    {'pri_log/pri2_log':<28}: {pri_rows}/{pri2_rows} rows")
    print(f"    {'vol_log/vol2_log':<28}: {vol_rows}/{vol2_rows} rows")

    # ── Phase 4: cleanup logs older than 720 days ─────────────────────────
    cursor.execute("DELETE FROM pri_log  WHERE Insert_date < SYSDATE - 720")
    cursor.execute("DELETE FROM vol_log  WHERE Insert_date < SYSDATE - 720")
    cursor.execute("DELETE FROM pri2_log WHERE Insert_date < SYSDATE - 720")
    cursor.execute("DELETE FROM vol2_log WHERE Insert_date < SYSDATE - 720")
    connection.commit()


# ── Standalone test: run against live DB and compare nasdaq_avg row counts ────
if __name__ == '__main__':
    import oracledb

    ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
    oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
    conn = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
    cur  = conn.cursor()

    cur.execute("SELECT MAX(TRADEDATE) FROM nasdaq_hist")
    tradedate = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM nasdaq_avg WHERE TRADEDATE = :dt", dt=tradedate)
    before = cur.fetchone()[0]

    print('=' * 61)
    print(f'  nasdaq_avg_proc_daily.py  — test run')
    print(f'  tradedate : {tradedate}')
    print(f'  nasdaq_avg rows before : {before}')
    print('=' * 61)

    nasdaq_avg_proc_daily(conn, cur, tradedate)

    cur.execute("SELECT COUNT(*) FROM nasdaq_avg WHERE TRADEDATE = :dt", dt=tradedate)
    after = cur.fetchone()[0]
    print('=' * 61)
    print(f'  nasdaq_avg rows after  : {after}')
    print('=' * 61)
