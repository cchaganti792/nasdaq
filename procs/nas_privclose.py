"""
nas_privclose.py  -  Python equivalent of Oracle NAS_PRIVCLOSE function

Oracle signature:
    NAS_PRIVCLOSE(in_symbol VARCHAR2, in_TRADEDATE DATE)
    RETURN NUMBER

What it does:
    Returns the previous trading day's CLOSE for a symbol.
    Looks in a 20-calendar-day window ending on in_tradedate.
    If >= 2 trading days exist in the window  -> return the 2nd most recent close (rank=2).
    If only 1 trading day in the window       -> return that close (rank=1).
    Returns 0.0 if no data at all.
    Result is TRUNC to 5 decimal places.

Called by nasdaq_avg_proc_daily once per symbol to compute PRCNT_CHANGE
(today's close vs previous close).

Usage (when nasdaq_avg_proc_daily is converted to Python):
    from procs.nas_privclose import nas_privclose
    prev = nas_privclose(cursor, 'AAPL', tradedate)

Fallback:
    If this Python version has any issue, the Oracle function NAS_PRIVCLOSE
    still exists in the DB and nasdaq_avg_proc_daily can be called via
    callproc() as before — nothing in production uses this file until you
    switch the proc.
"""

import math
import oracledb


def nas_privclose(cursor, in_symbol: str, in_tradedate) -> float:
    cursor.execute(
        "SELECT COUNT(*) FROM nasdaq_hist"
        " WHERE SYMBOL = :sym AND TRADEDATE BETWEEN :dt - 20 AND :dt",
        sym=in_symbol, dt=in_tradedate
    )
    rw_cnt = cursor.fetchone()[0]

    if rw_cnt == 0:
        return 0.0

    rnk = 2 if rw_cnt >= 2 else 1

    cursor.execute(
        "SELECT CLOSE FROM ("
        "  SELECT CLOSE, RANK() OVER (ORDER BY TRADEDATE DESC) RNK"
        "  FROM nasdaq_hist"
        "  WHERE SYMBOL = :sym AND TRADEDATE BETWEEN :dt - 20 AND :dt"
        ") WHERE RNK = :rnk",
        sym=in_symbol, dt=in_tradedate, rnk=rnk
    )
    row = cursor.fetchone()
    if not row or row[0] is None:
        return 0.0
    # Oracle TRUNC(x,5) — truncate toward zero, not round
    return math.trunc(float(row[0]) * 100000) / 100000


# ── Self-test: compare Python vs Oracle function for several symbols ──────────
if __name__ == '__main__':
    ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
    oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
    conn = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
    cur  = conn.cursor()

    # Pick 10 symbols that have at least 5 rows so the window has data
    cur.execute("""
        SELECT symbol FROM (
            SELECT symbol FROM nasdaq_hist
            GROUP BY symbol
            HAVING COUNT(*) >= 5
            ORDER BY symbol
        ) WHERE ROWNUM <= 10
    """)
    symbols = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT MAX(TRADEDATE) FROM nasdaq_hist")
    tradedate = cur.fetchone()[0]

    print(f"Test date : {tradedate}")
    print(f"Symbols   : {symbols}")
    print()

    SEP = '-' * 65
    all_ok = True

    for sym in symbols:
        py_val  = nas_privclose(cur, sym, tradedate)
        cur.execute("SELECT NAS_PRIVCLOSE(:sym, :dt) FROM dual",
                    sym=sym, dt=tradedate)
        ora_row = cur.fetchone()
        ora_val = float(ora_row[0]) if ora_row and ora_row[0] is not None else 0.0
        match   = abs(py_val - ora_val) < 0.00001
        if not match:
            all_ok = False
        status  = 'OK' if match else 'MISMATCH <<<'
        print(f"  {sym:<8}  py={py_val:>12.5f}  ora={ora_val:>12.5f}  {status}")

    print()
    print(SEP)
    print(f"  Overall : {'ALL MATCH — safe to use' if all_ok else 'MISMATCHES FOUND — do not switch yet'}")
    print(SEP)
