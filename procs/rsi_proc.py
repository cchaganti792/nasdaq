"""
rsi_proc.py  -  Python equivalent of Oracle RSI_proc procedure

Oracle signature:
    RSI_proc

What it does:
    Computes Wilder's 14-period RSI for every symbol on the latest tradedate
    in nasdaq_avg, then updates nasdaq_avg.RSI / RSI_AVGU / RSI_AVGD.

    For each symbol:
      - If no prior nasdaq_avg row exists  : skip.
      - If prior RSI_AVGU/AVGD are NULL    : COLD START
            * sum gain/loss over prior 14 rows -> seed AVGU/AVGD
            * store seed at tradedate = vdate-1 (matches existing Oracle behaviour)
            * then apply today's smoothed update:
                v_avgu = (today_gain + 13*prev_avgu) / 14
                v_avgd = (today_loss + 13*prev_avgd) / 14
            * if v_avgd = 0 use 1 (cold-start divisor — Oracle quirk)
      - Else (warm path):
            * fetch prior avgu/avgd
            * v_avgu = (today_gain + 13*prev_avgu) / 14
            * v_avgd = (today_loss + 13*prev_avgd) / 14
            * if v_avgd = 0 use 0.1 (warm-path divisor — Oracle quirk)
      - RSI = round(100 - 100/(1 + v_avgu/v_avgd_adj), 2)

    Cold-start vs warm-start use different zero-divisor fudge values
    (1 vs 0.1). This matches the Oracle proc exactly.

Usage (in NASDAQ_UPLOAD.py, replacing run_proc call):
    from procs.rsi_proc import rsi_proc
    rsi_proc(connection, cursor, tradedate)

Fallback:
    Oracle RSI_proc still exists in the DB.
    In NASDAQ_UPLOAD.py restore: run_proc('RSI_proc', tradedate)
"""

import sys
import os
from datetime import datetime, timedelta


def rsi_proc(connection, cursor, tradedate=None):
    # ── Resolve tradedate ─────────────────────────────────────────────────
    if tradedate is None:
        cursor.execute("SELECT MAX(TRADEDATE) FROM nasdaq_avg")
        v_date = cursor.fetchone()[0]
    elif isinstance(tradedate, str):
        v_date = datetime.strptime(tradedate, '%Y-%m-%d').date()
    else:
        v_date = tradedate

    # ── Symbols on that tradedate ─────────────────────────────────────────
    cursor.execute(
        "SELECT DISTINCT symbol FROM nasdaq_avg WHERE TRADEDATE = :dt",
        dt=v_date
    )
    symbols = [r[0] for r in cursor.fetchall()]

    rows_updated = 0
    skipped      = 0

    for sym in symbols:
        # 1. Most recent prior row (any)
        cursor.execute(
            "SELECT RSI_AVGU, RSI_AVGD FROM ("
            "  SELECT RSI_AVGU, RSI_AVGD FROM nasdaq_avg "
            "  WHERE SYMBOL = :sym AND TRADEDATE < :dt "
            "  ORDER BY TRADEDATE DESC"
            ") WHERE ROWNUM < 2",
            sym=sym, dt=v_date
        )
        prior = cursor.fetchone()
        if prior is None:
            skipped += 1
            continue

        prev_avgu, prev_avgd = prior

        # 2. Cold start vs warm path
        if prev_avgu is None or prev_avgd is None:
            # ── COLD START ────────────────────────────────────────────────
            cursor.execute(
                "SELECT ROUND(SUM(gain)/14, 2), ROUND(SUM(loss)/14, 2) FROM ("
                "  SELECT "
                "    CASE WHEN CURRENTPRICE > PRIVCLOSE THEN CURRENTPRICE - PRIVCLOSE ELSE 0 END AS gain,"
                "    CASE WHEN CURRENTPRICE < PRIVCLOSE THEN PRIVCLOSE - CURRENTPRICE ELSE 0 END AS loss"
                "  FROM nasdaq_avg "
                "  WHERE SYMBOL = :sym AND TRADEDATE < :dt "
                "  ORDER BY TRADEDATE DESC"
                ") WHERE ROWNUM < 15",
                sym=sym, dt=v_date
            )
            seed_row = cursor.fetchone()
            if seed_row is None or seed_row[0] is None:
                skipped += 1
                continue
            vgain, vloss = float(seed_row[0]), float(seed_row[1])

            # Seed the prior day (matches Oracle: tradedate = vdate - 1)
            cursor.execute(
                "UPDATE nasdaq_avg SET RSI_AVGU = :u, RSI_AVGD = :d "
                "WHERE SYMBOL = :sym AND TRADEDATE = :dt - 1",
                u=vgain, d=vloss, sym=sym, dt=v_date
            )
            connection.commit()

            # Re-read the now-seeded prior row
            cursor.execute(
                "SELECT RSI_AVGU, RSI_AVGD FROM ("
                "  SELECT RSI_AVGU, RSI_AVGD FROM nasdaq_avg "
                "  WHERE SYMBOL = :sym AND TRADEDATE < :dt "
                "  ORDER BY TRADEDATE DESC"
                ") WHERE ROWNUM < 2",
                sym=sym, dt=v_date
            )
            prior2 = cursor.fetchone()
            if prior2 is None or prior2[0] is None or prior2[1] is None:
                skipped += 1
                continue
            vrsiu, vrsid = float(prior2[0]), float(prior2[1])

            # Today's smoothed update — cold start uses 1 as zero-divisor fudge
            cursor.execute(
                "SELECT "
                "  ROUND((CASE WHEN CURRENTPRICE > PRIVCLOSE THEN CURRENTPRICE - PRIVCLOSE ELSE 0 END + 13*:u)/14, 5),"
                "  ROUND((CASE WHEN CURRENTPRICE < PRIVCLOSE THEN PRIVCLOSE - CURRENTPRICE ELSE 0 END + 13*:d)/14, 5) "
                "FROM nasdaq_avg WHERE SYMBOL = :sym AND TRADEDATE = :dt",
                u=vrsiu, d=vrsid, sym=sym, dt=v_date
            )
            row = cursor.fetchone()
            if row is None or row[0] is None:
                skipped += 1
                continue
            v_avgu, v_avgd = float(row[0]), float(row[1])
            v_avgd_adj = 1 if v_avgd == 0 else v_avgd

        else:
            # ── WARM PATH ─────────────────────────────────────────────────
            vrsiu, vrsid = float(prev_avgu), float(prev_avgd)
            cursor.execute(
                "SELECT "
                "  ROUND((CASE WHEN CURRENTPRICE > PRIVCLOSE THEN CURRENTPRICE - PRIVCLOSE ELSE 0 END + 13*:u)/14, 5),"
                "  ROUND((CASE WHEN CURRENTPRICE < PRIVCLOSE THEN PRIVCLOSE - CURRENTPRICE ELSE 0 END + 13*:d)/14, 5) "
                "FROM nasdaq_avg WHERE SYMBOL = :sym AND TRADEDATE = :dt",
                u=vrsiu, d=vrsid, sym=sym, dt=v_date
            )
            row = cursor.fetchone()
            if row is None or row[0] is None:
                skipped += 1
                continue
            v_avgu, v_avgd = float(row[0]), float(row[1])
            v_avgd_adj = 0.1 if v_avgd == 0 else v_avgd

        # 3. Update today's RSI
        v_rs = v_avgu / v_avgd_adj
        v_rsi = round(100 - (100 / (1 + v_rs)), 2)
        cursor.execute(
            "UPDATE nasdaq_avg "
            "SET RSI_AVGU = :u, RSI_AVGD = :d, RSI = :rsi "
            "WHERE SYMBOL = :sym AND TRADEDATE = :dt",
            u=v_avgu, d=v_avgd, rsi=v_rsi, sym=sym, dt=v_date
        )
        rows_updated += cursor.rowcount

    connection.commit()
    skip_str = f", {skipped} skipped" if skipped else ""
    print(f"    {'nasdaq_avg (RSI)':<28}: {rows_updated} rows updated{skip_str}  |  date: {v_date}")


# ── Standalone test: run against live DB ──────────────────────────────────────
if __name__ == '__main__':
    import oracledb

    ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
    oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
    conn = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
    cur  = conn.cursor()

    cur.execute("SELECT MAX(TRADEDATE) FROM nasdaq_avg")
    tradedate = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM nasdaq_avg WHERE TRADEDATE = :dt AND RSI IS NOT NULL",
        dt=tradedate
    )
    before = cur.fetchone()[0]

    print('=' * 61)
    print(f'  rsi_proc.py  — test run')
    print(f'  tradedate : {tradedate}')
    print(f'  rows with RSI set (before) : {before}')
    print('=' * 61)

    rsi_proc(conn, cur, tradedate)

    cur.execute(
        "SELECT COUNT(*) FROM nasdaq_avg WHERE TRADEDATE = :dt AND RSI IS NOT NULL",
        dt=tradedate
    )
    after = cur.fetchone()[0]
    print('=' * 61)
    print(f'  rows with RSI set (after) : {after}')
    print('=' * 61)
