"""
bollinger_fn.py  -  Python equivalent of Oracle BOLLINGER function

Oracle signature:
    BOLLINGER(in_symbol VARCHAR2, in_TRADEDATE DATE) RETURN NUMBER

What it does:
    Returns stddev of CURRENTPRICE over the most recent 20 rows in nasdaq_avg
    ending on in_tradedate.
    - Counts rows in a 33-calendar-day window.
    - If count >= 20 : stddev of top-20 (ranked DESC by tradedate) within a
      60-calendar-day window, rounded to 2 decimals.
    - If count <  20 : returns 0.

    Note: uses CURRENTPRICE from nasdaq_avg, not CLOSE from nasdaq_hist.

Called by bollinger_proc.py (Python version) or BOLLINGER_proc (Oracle).

Usage:
    from procs.bollinger_fn import bollinger
    std = bollinger(cursor, 'AAPL', tradedate)

Fallback:
    Oracle BOLLINGER function still exists in the DB. Nothing in production
    uses this file until bollinger_proc switches to call this Python version.
"""

import oracledb


def bollinger(cursor, in_symbol: str, in_tradedate) -> float:
    cursor.execute(
        "SELECT COUNT(*) FROM nasdaq_avg"
        " WHERE SYMBOL = :sym AND TRADEDATE BETWEEN :dt - 33 AND :dt",
        sym=in_symbol, dt=in_tradedate
    )
    rw_cnt = cursor.fetchone()[0]
    if rw_cnt < 20:
        return 0.0

    cursor.execute(
        "SELECT ROUND(STDDEV(CURRENTPRICE), 2) FROM ("
        "  SELECT CURRENTPRICE,"
        "         RANK() OVER (PARTITION BY SYMBOL ORDER BY TRADEDATE DESC) RNK"
        "  FROM nasdaq_avg"
        "  WHERE SYMBOL = :sym AND TRADEDATE BETWEEN :dt - 60 AND :dt"
        ") WHERE RNK < 21",
        sym=in_symbol, dt=in_tradedate
    )
    row = cursor.fetchone()
    if not row or row[0] is None:
        return 0.0
    return float(row[0])


# ── Self-test: compare Python vs Oracle function for several symbols ──────────
if __name__ == '__main__':
    ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
    oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
    conn = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
    cur  = conn.cursor()

    cur.execute("""
        SELECT symbol FROM (
            SELECT symbol FROM nasdaq_avg GROUP BY symbol
            HAVING COUNT(*) >= 20 ORDER BY symbol
        ) WHERE ROWNUM <= 10
    """)
    symbols = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT MAX(TRADEDATE) FROM nasdaq_avg")
    tradedate = cur.fetchone()[0]

    print(f"Test date : {tradedate}")
    print(f"Symbols   : {symbols}")
    print()

    SEP = '-' * 65
    all_ok = True

    for sym in symbols:
        py_val = bollinger(cur, sym, tradedate)
        cur.execute("SELECT BOLLINGER(:sym, :dt) FROM dual", sym=sym, dt=tradedate)
        ora_row = cur.fetchone()
        ora_val = float(ora_row[0]) if ora_row and ora_row[0] is not None else 0.0
        match = abs(py_val - ora_val) < 0.01
        if not match:
            all_ok = False
        status = 'OK' if match else 'MISMATCH <<<'
        print(f"  {sym:<8}  py={py_val:>10.2f}  ora={ora_val:>10.2f}  {status}")

    print()
    print(SEP)
    print(f"  Overall : {'ALL MATCH — safe to use' if all_ok else 'MISMATCHES FOUND — do not switch yet'}")
    print(SEP)
