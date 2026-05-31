"""
SEC_EDGAR_FUNDAMENTALS.py  -  Python 3
Downloads fundamental financial data from SEC EDGAR XBRL API.

Free, no API key required. Will not break — SEC EDGAR is a US government
system that companies are legally required to file with.

SEC fair-use: identify yourself in User-Agent, stay under 10 req/sec.

Step 1 : Download ticker->CIK mapping from SEC  ->  SEC_CIK_MAP
Step 2 : For each symbol fetch companyfacts JSON ->  SEC_FINANCIALS
         Extracts last 5 years of 10-Q (quarterly) and 10-K (annual):
         Revenue, Gross Profit, Operating Income, Net Income,
         EPS Basic, EPS Diluted, Dividend per Share, Shares Outstanding

Run: python SEC_EDGAR_FUNDAMENTALS.py
"""

import time
import requests
import oracledb
from datetime import date, timedelta

# ── Oracle connection ──────────────────────────────────────────────────────
ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
connection = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
cursor = connection.cursor()

# ── SEC requires you identify yourself in User-Agent ───────────────────────
SEC_HEADERS = {"User-Agent": "NasdaqPipeline cchaganti792@gmail.com"}

# ── Only load last 5 years ─────────────────────────────────────────────────
CUTOFF_DATE = date.today() - timedelta(days=5 * 365)

# ── Revenue has many possible XBRL tags — try in this order ───────────────
REVENUE_TAGS = [
    'RevenueFromContractWithCustomerExcludingAssessedTax',
    'Revenues',
    'SalesRevenueNet',
    'RevenueFromContractWithCustomerIncludingAssessedTax',
    'SalesRevenueGoodsNet',
    'RegulatedAndUnregulatedOperatingRevenue',
]
DIVIDEND_TAGS = [
    'CommonStockDividendsPerShareDeclared',
    'CommonStockDividendsPerShareCashPaid',
]


# ── Step 1: Download ticker->CIK mapping ──────────────────────────────────
print("=" * 65)
print("  SEC_EDGAR_FUNDAMENTALS.py")
print("  Step 1 : Downloading ticker->CIK mapping from SEC...")
print("=" * 65)

resp = requests.get(
    "https://www.sec.gov/files/company_tickers.json",
    headers=SEC_HEADERS,
    timeout=30
)
resp.raise_for_status()

cik_map = {}
for entry in resp.json().values():
    sym  = entry['ticker'].upper().strip()
    cik  = str(entry['cik_str']).zfill(10)
    name = entry.get('title', '')[:200]
    cik_map[sym] = (cik, name)

print(f"  CIK entries received : {len(cik_map)}")

MERGE_CIK = """
MERGE INTO sec_cik_map dst
USING (SELECT :sym AS symbol FROM dual) src
ON (dst.symbol = src.symbol)
WHEN MATCHED THEN
    UPDATE SET cik = :cik, name = :name, updated = SYSDATE
WHEN NOT MATCHED THEN
    INSERT (symbol, cik, name, updated)
    VALUES (:sym,  :cik, :name, SYSDATE)
"""
for sym, (cik, name) in cik_map.items():
    cursor.execute(MERGE_CIK, sym=sym, cik=cik, name=name)
connection.commit()
print(f"  SEC_CIK_MAP upserted : {len(cik_map)} rows")


# ── Step 2: Symbols to process ────────────────────────────────────────────
# Only symbols that exist in both nasdaq_hist and sec_cik_map
cursor.execute("""
    SELECT n.symbol, m.cik
    FROM   (SELECT DISTINCT symbol FROM nasdaq_hist) n
    JOIN   sec_cik_map m ON m.symbol = n.symbol
    ORDER  BY n.symbol
""")
symbols = cursor.fetchall()
total   = len(symbols)
print(f"\n  Symbols matched to CIK : {total}")
print(f"  Step 2 : Fetching company facts from EDGAR...")
print(f"  (approx {total // 400} min)\n")


def get_company_facts(cik):
    """Fetch all XBRL facts for one CIK. Returns us-gaap dict or None."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    r   = requests.get(url, headers=SEC_HEADERS, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json().get('facts', {}).get('us-gaap', {})


def extract_metric(usgaap, tags, units_key='USD'):
    """
    Try each tag in order. Return dict keyed by (period_end, form_type) -> value.
    Filters:
      - 10-Q and 10-K forms only
      - Last 5 years
      - Single-period only (skip YTD cumulative rows by checking duration)
    """
    for tag in tags:
        node = usgaap.get(tag, {})
        raw  = node.get('units', {}).get(units_key, [])
        if not raw:
            continue

        result = {}
        for item in raw:
            form = item.get('form', '')
            if form not in ('10-Q', '10-K'):
                continue
            try:
                end_dt = date.fromisoformat(item['end'])
            except (KeyError, ValueError):
                continue
            if end_dt < CUTOFF_DATE:
                continue

            # Skip cumulative YTD rows — only keep single-period rows
            if 'start' in item:
                try:
                    days = (end_dt - date.fromisoformat(item['start'])).days
                    if form == '10-Q' and not (60 <= days <= 110):
                        continue
                    if form == '10-K' and not (340 <= days <= 390):
                        continue
                except ValueError:
                    continue

            key = (end_dt, form)
            result[key] = item['val']   # last value wins if duplicates

        if result:
            return result
    return {}


MERGE_FIN = """
MERGE INTO sec_financials dst
USING (SELECT :sym AS symbol, :pend AS period_end, :ft AS form_type FROM dual) src
ON (dst.symbol = src.symbol
    AND dst.period_end = src.period_end
    AND dst.form_type  = src.form_type)
WHEN MATCHED THEN
    UPDATE SET revenue            = :rev,
               gross_profit       = :gp,
               oper_income        = :oi,
               net_income         = :ni,
               eps_basic          = :epsb,
               eps_diluted        = :epsd,
               dividend_per_share = :div,
               shares_outstanding = :shr,
               inserted_date      = SYSDATE
WHEN NOT MATCHED THEN
    INSERT (symbol, cik, period_end, form_type,
            revenue, gross_profit, oper_income, net_income,
            eps_basic, eps_diluted, dividend_per_share, shares_outstanding,
            inserted_date)
    VALUES (:sym, :cik, :pend, :ft,
            :rev, :gp, :oi, :ni,
            :epsb, :epsd, :div, :shr,
            SYSDATE)
"""

rows_written = 0
errors       = 0

for idx, (symbol, cik) in enumerate(symbols, 1):
    try:
        usgaap = get_company_facts(cik)
        if usgaap is None:
            errors += 1
            continue

        rev  = extract_metric(usgaap, REVENUE_TAGS)
        gp   = extract_metric(usgaap, ['GrossProfit'])
        oi   = extract_metric(usgaap, ['OperatingIncomeLoss'])
        ni   = extract_metric(usgaap, ['NetIncomeLoss'])
        epsb = extract_metric(usgaap, ['EarningsPerShareBasic'],   'USD/shares')
        epsd = extract_metric(usgaap, ['EarningsPerShareDiluted'], 'USD/shares')
        div  = extract_metric(usgaap, DIVIDEND_TAGS,               'USD/shares')
        shr  = extract_metric(usgaap, ['CommonStockSharesOutstanding'], 'shares')

        all_periods = set(rev) | set(gp) | set(oi) | set(ni) | set(epsb) | set(epsd)

        for key in all_periods:
            end_date, form_type = key
            cursor.execute(MERGE_FIN,
                sym  = symbol,
                cik  = cik,
                pend = end_date,
                ft   = form_type,
                rev  = rev.get(key),
                gp   = gp.get(key),
                oi   = oi.get(key),
                ni   = ni.get(key),
                epsb = epsb.get(key),
                epsd = epsd.get(key),
                div  = div.get(key),
                shr  = shr.get(key),
            )
            rows_written += 1

        connection.commit()

        if idx % 100 == 0:
            print(f"  [{idx:>5}/{total}]  rows written: {rows_written:>8}  errors: {errors}")

        time.sleep(0.15)   # ~6 req/sec — well under SEC's 10 req/sec limit

    except Exception as exc:
        errors += 1
        connection.rollback()
        if idx % 100 == 0:
            print(f"  [{idx:>5}/{total}]  ERROR {symbol}: {exc}")

print(f"\n{'='*65}")
print(f"  Done.")
print(f"  Symbols processed        : {idx}")
print(f"  Rows inserted/updated    : {rows_written}")
print(f"  Errors (symbol skipped)  : {errors}")
print(f"{'='*65}")
