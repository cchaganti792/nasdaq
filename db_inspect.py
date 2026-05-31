"""
db_inspect.py  -  Python 3
Read-only Oracle query tool for Claude to inspect the database.
SELECT queries only — no data or schema changes.

Usage:
    python db_inspect.py "SELECT COUNT(*) FROM nasdaq_hist"
    python db_inspect.py "SELECT table_name FROM user_tables ORDER BY table_name"
"""

import sys
import oracledb

ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)

connection = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
cursor = connection.cursor()

if len(sys.argv) < 2:
    print("Usage: python db_inspect.py \"SELECT ...\"")
    sys.exit(1)

sql = sys.argv[1].strip().rstrip(";")

if sql.split()[0].upper() != "SELECT":
    print("BLOCKED: only SELECT statements are allowed.")
    sys.exit(1)

cursor.execute(sql)
cols = [d[0] for d in cursor.description]
rows = cursor.fetchall()

if not rows:
    print("(no rows returned)")
    sys.exit(0)

widths = [len(c) for c in cols]
str_rows = []
for row in rows:
    str_row = [str(v) if v is not None else "NULL" for v in row]
    for i, val in enumerate(str_row):
        widths[i] = max(widths[i], len(val))
    str_rows.append(str_row)

sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
print(sep)
print("| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cols)) + " |")
print(sep)
for str_row in str_rows:
    print("| " + " | ".join(v.ljust(widths[i]) for i, v in enumerate(str_row)) + " |")
print(sep)
print(f"{len(rows)} row(s)")
