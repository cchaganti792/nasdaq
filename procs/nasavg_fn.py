"""
nasavg.py  -  Python equivalent of Oracle NASAVG function

Oracle signature:
    NASAVG(in_avgnum NUMBER, in_symbol VARCHAR2, in_TRADEDATE DATE, in_parm VARCHAR2)
    RETURN NUMBER

What it does:
    Returns the N-period average of a price/volume column (in_parm) for a
    symbol, looking backward from in_tradedate.  Uses at most in_avgnum rows.
    Divides sum by actual row count (same as AVG()), then TRUNC to 2 decimals.
    Returns 0.0 if no data.

Called by nasdaq_avg_proc_daily for:
    CLOSE  averages : 5, 20, 50, 150, 200 days
    VOLUME averages : 5, 20, 50, 150 days

Usage (when nasdaq_avg_proc_daily is converted to Python):
    from procs.nasavg import nasavg
    val = nasavg(cursor, 20, 'AAPL', tradedate, 'CLOSE')

Fallback:
    If this Python version has any issue, the Oracle function NASAVG still
    exists in the DB and nasdaq_avg_proc_daily can be called via callproc()
    as before — nothing in production uses this file until you switch the proc.
"""

import math
import oracledb

_VALID_COLS = {'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME'}


def nasavg(cursor, in_avgnum: int, in_symbol: str, in_tradedate, in_parm: str) -> float:
    col = in_parm.upper()
    if col not in _VALID_COLS:
        raise ValueError(f"nasavg: invalid column '{in_parm}' — must be one of {_VALID_COLS}")

    cursor.execute(
        f"SELECT AVG({col}) FROM ("
        f"  SELECT {col} FROM nasdaq_hist"
        f"  WHERE SYMBOL = :sym AND TRADEDATE <= :dt"
        f"  ORDER BY TRADEDATE DESC"
        f") WHERE ROWNUM <= :n",
        sym=in_symbol, dt=in_tradedate, n=in_avgnum
    )
    row = cursor.fetchone()
    if not row or row[0] is None:
        return 0.0
    # Oracle TRUNC(x,2) — truncate toward zero, not round
    return math.trunc(float(row[0]) * 100) / 100


# ── Self-test: compare Python vs Oracle function for several symbols/periods ──
if __name__ == '__main__':
    ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
    oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
    conn = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
    cur  = conn.cursor()

    # Pick 5 symbols that have at least 200 rows so all period tests are meaningful
    cur.execute("""
        SELECT symbol FROM (
            SELECT symbol FROM nasdaq_hist
            GROUP BY symbol
            HAVING COUNT(*) >= 200
            ORDER BY symbol
        ) WHERE ROWNUM <= 5
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
        print(f"  {sym}:")
        for n, col in [(5, 'CLOSE'), (20, 'CLOSE'), (50, 'CLOSE'), (150, 'CLOSE'), (200, 'CLOSE'),
                       (5, 'VOLUME'), (20, 'VOLUME'), (50, 'VOLUME'), (150, 'VOLUME')]:
            py_val  = nasavg(cur, n, sym, tradedate, col)
            cur.execute("SELECT NASAVG(:n, :sym, :dt, :col) FROM dual",
                        n=n, sym=sym, dt=tradedate, col=col)
            ora_row = cur.fetchone()
            ora_val = float(ora_row[0]) if ora_row and ora_row[0] is not None else 0.0
            match   = abs(py_val - ora_val) < 0.01
            if not match:
                all_ok = False
            status  = 'OK' if match else 'MISMATCH <<<'
            print(f"    N={n:3d} {col:<6}  py={py_val:>14.2f}  ora={ora_val:>14.2f}  {status}")
        print()

    print(SEP)
    print(f"  Overall : {'ALL MATCH — safe to use' if all_ok else 'MISMATCHES FOUND — do not switch yet'}")
    print(SEP)
