"""
bollinger_proc.py  -  Python equivalent of Oracle BOLLINGER_proc procedure

Oracle signature:
    BOLLINGER_proc

What it does:
    For the latest tradedate in nasdaq_avg, loops through every symbol and
    computes the Bollinger stddev (via bollinger_fn). Then updates nasdaq_avg
    SD, BU (upper band), BD (lower band) columns:
        SD = stddev
        BU = TWENTYAVGPRI + 2 * stddev
        BD = TWENTYAVGPRI - 2 * stddev

    Original Oracle proc operates only on MAX(TRADEDATE) FROM nasdaq_avg
    (the latest day), so this matches that behaviour.

Usage (in NASDAQ_UPLOAD.py, replacing run_proc call):
    from procs.bollinger_proc import bollinger_proc
    bollinger_proc(connection, cursor, tradedate)

Fallback:
    Oracle BOLLINGER_proc still exists in the DB.
    In NASDAQ_UPLOAD.py restore: run_proc('BOLLINGER_proc', tradedate)
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procs.bollinger_fn import bollinger


def bollinger_proc(connection, cursor, tradedate=None):
    # ── Resolve tradedate ─────────────────────────────────────────────────
    if tradedate is None:
        cursor.execute("SELECT MAX(TRADEDATE) FROM nasdaq_avg")
        v_date = cursor.fetchone()[0]
    elif isinstance(tradedate, str):
        v_date = datetime.strptime(tradedate, '%Y-%m-%d').date()
    else:
        v_date = tradedate

    # ── Loop every symbol on that tradedate ───────────────────────────────
    cursor.execute(
        "SELECT DISTINCT symbol FROM nasdaq_avg WHERE TRADEDATE = :dt",
        dt=v_date
    )
    symbols = [r[0] for r in cursor.fetchall()]

    updated = 0
    for sym in symbols:
        v_stddev = bollinger(cursor, sym, v_date)
        cursor.execute(
            "UPDATE nasdaq_avg "
            "SET SD = :sd, "
            "    BU = TWENTYAVGPRI + (2 * :sd), "
            "    BD = TWENTYAVGPRI - (2 * :sd) "
            "WHERE SYMBOL = :sym AND TRADEDATE = :dt",
            sd=v_stddev, sym=sym, dt=v_date
        )
        updated += cursor.rowcount

    connection.commit()
    print(f"    {'nasdaq_avg (SD/BU/BD)':<28}: {updated} rows updated  |  date: {v_date}")


# ── Standalone test: run against live DB and show count of updated rows ──────
if __name__ == '__main__':
    import oracledb

    ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
    oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
    conn = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
    cur  = conn.cursor()

    cur.execute("SELECT MAX(TRADEDATE) FROM nasdaq_avg")
    tradedate = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM nasdaq_avg WHERE TRADEDATE = :dt AND SD IS NOT NULL",
        dt=tradedate
    )
    before = cur.fetchone()[0]

    print('=' * 61)
    print(f'  bollinger_proc.py  — test run')
    print(f'  tradedate : {tradedate}')
    print(f'  rows with SD already set (before) : {before}')
    print('=' * 61)

    bollinger_proc(conn, cur, tradedate)

    cur.execute(
        "SELECT COUNT(*) FROM nasdaq_avg WHERE TRADEDATE = :dt AND SD IS NOT NULL",
        dt=tradedate
    )
    after = cur.fetchone()[0]
    print('=' * 61)
    print(f'  rows with SD set (after) : {after}')
    print('=' * 61)
