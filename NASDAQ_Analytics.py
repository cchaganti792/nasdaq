import os
import re
import requests
import pandas
import csv
import datetime
import time
import glob
import shutil
from datetime import datetime, timedelta
import oracledb

ORACLE_CLIENT_DIR = r"C:\ora_insta_client\instantclient_23_0"
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_DIR)
connection = oracledb.connect(user="nasdaq", password="nasdaq123", dsn="localhost/orcl")
cursor = connection.cursor()

symbol_input_lis = []

## Delete old entries from analytics ##
cursor.execute('insert into analytics_deleted select * from analytics where udate<sysdate-75')
cursor.execute('delete from analytics where udate<sysdate-75')
connection.commit()

## Fetch data for new run
cursor.execute('select symbol from (select distinct symbol from pri_log where INSERT_DATE>sysdate-60 union select distinct symbol from vol_log where INSERT_DATE>sysdate-60) where symbol not in (select symbol from donot_track)')
for row in cursor:
    symbol_input_lis.append(row[0])

print('=' * 65)
print('  NASDAQ_Analytics.py')
print(f'  Symbols to process : {len(symbol_input_lis)}')
print('=' * 65)

for i in symbol_input_lis:
    ## ---- 1. pcount calculation --- ###
    cursor.execute('select count(*)  from pri_log where symbol=:vsymbol and INSERT_DATE>sysdate-90', vsymbol=i)
    pcount = cursor.fetchone()
    ## ---- 2. vcount calculation --- ###
    cursor.execute('select count(*)  from vol_log where symbol=:vsymbol and INSERT_DATE>sysdate-90', vsymbol=i)
    vcount = cursor.fetchone()
    ## ---- 3. prnk calculation --- ###
    cursor.execute('select distinct rnk , insert_date from pri_log where symbol=:vsymbol and INSERT_DATE>sysdate-90 order  by insert_date', vsymbol=i)
    PRNK = cursor.fetchall()
    PRNK_S = ''
    for r in PRNK:
        PRNK_S = PRNK_S + '%s-' % r[0]
    ## ---- 4. vrnk calculation --- ###
    cursor.execute('SELECT DISTINCT RNK,INSERT_DATE FROM VOL_LOG WHERE SYMBOL=:vsymbol AND INSERT_DATE>sysdate-120 GROUP BY  RNK,INSERT_DATE HAVING SUM(PRCNT_CHANGE)>0 UNION SELECT DISTINCT RNK,INSERT_DATE FROM VOL2_LOG WHERE SYMBOL=:vsymbol AND INSERT_DATE>sysdate-120 GROUP BY  RNK,INSERT_DATE HAVING SUM(PRCNT_CHANGE)>0 order  by insert_date', vsymbol=i)
    VRNK = cursor.fetchall()
    VRNK_S = ''
    for r in VRNK:
        VRNK_S = VRNK_S + '%s-' % r[0]
    #print('before cutting ' + VRNK_S)
    #print(len(VRNK_S))
    if len(VRNK_S) > 120:
        a = len(VRNK_S) - 120
        VRNK_S = VRNK_S[a:]
    else:
        VRNK_S = VRNK_S
    #print('after cutting ' + VRNK_S)
    ## ---- 5. FIRST_PDATE calculation --- ###
    cursor.execute(' select min(insert_date) from pri_log where symbol=:vsymbol and INSERT_DATE>sysdate-90', vsymbol=i)
    FIRST_PDATE = cursor.fetchone()
    #print(FIRST_PDATE[0])
    ## ---- 6. FIRST_VDATE calculation --- ###
    cursor.execute(' select min(insert_date) from vol_log where symbol=:vsymbol and INSERT_DATE>sysdate-90', vsymbol=i)
    FIRST_VDATE = cursor.fetchone()
    ## ---- 7. LAST_PDATE calculation --- ###
    cursor.execute(' select max(insert_date) from pri_log where symbol=:vsymbol and INSERT_DATE>sysdate-90', vsymbol=i)
    LAST_PDATE = cursor.fetchone()
    ## ---- 8. LAST_VDATE calculation --- ###
    cursor.execute(' select max(insert_date) from vol_log where symbol=:vsymbol and INSERT_DATE>sysdate-90', vsymbol=i)
    LAST_VDATE = cursor.fetchone()
    ## ---- 9. PI_PRICE calculation --- ###
    cursor.execute('select MAX(CURRENTPRICE) from pri_log where symbol=:vsymbol and insert_date=to_date(:vinsert_date)', vsymbol=i, vinsert_date=FIRST_PDATE[0])
    PI_PRICE = cursor.fetchone()
    ## ---- 10. VI_PRICE calculation --- ###
    cursor.execute('select MAX(CURRENTPRICE) from vol_log where symbol=:vsymbol and insert_date=to_date(:vinsert_date)', vsymbol=i, vinsert_date=FIRST_VDATE[0])
    VI_PRICE = cursor.fetchone()
    #print("count are %s %s %s %s %s  " % (i, FIRST_PDATE[0], FIRST_VDATE[0], PI_PRICE[0], VI_PRICE[0]))
    ## ---- 11. BASE_PRICE calculation --- ###
    if FIRST_PDATE[0] != None and FIRST_VDATE[0] != None:
        BASE_PRICE = PI_PRICE[0]
    elif FIRST_PDATE[0] != None and FIRST_VDATE[0] == None:
        BASE_PRICE = PI_PRICE[0]
        #print('only pdate present')
    elif FIRST_PDATE[0] == None and FIRST_VDATE[0] != None:
        BASE_PRICE = VI_PRICE[0]
        #print('only vdate present')
    else:
        pass
        #print('both none')
    ## ---- 12. GROWTH_DATES calculation --- ###
    #print(BASE_PRICE)
    if LAST_PDATE[0] != None and LAST_VDATE[0] != None:
        FIRST_GROWTH_DATE = LAST_PDATE[0]
        SECOND_GROWTH_DATE = LAST_PDATE[0] + timedelta(days=4)
    elif LAST_PDATE[0] != None and LAST_VDATE[0] == None:
        FIRST_GROWTH_DATE = LAST_PDATE[0]
        SECOND_GROWTH_DATE = LAST_PDATE[0] + timedelta(days=4)
    elif LAST_PDATE[0] == None and LAST_VDATE[0] != None:
        FIRST_GROWTH_DATE = LAST_VDATE[0]
        SECOND_GROWTH_DATE = LAST_VDATE[0] + timedelta(days=4)
        #print('only vdate present')
    else:
        pass
        #print('both none')
    #print(FIRST_GROWTH_DATE)
    #print(SECOND_GROWTH_DATE)
    ## ---- 13. GROWTH calculation --- ###
    cursor.execute('select count(*) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)', vsymbol=i, vinsert_date=FIRST_GROWTH_DATE)
    CNT = cursor.fetchone()
    if CNT[0] == 0:
        cursor.execute("select count(*) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date,'yyyy-mm-dd')+2", vsymbol=i, vinsert_date=FIRST_GROWTH_DATE)
        CNT_TWO = cursor.fetchone()
        if CNT_TWO[0] == 0:
            cursor.execute('select count(*) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)+3', vsymbol=i, vinsert_date=FIRST_GROWTH_DATE)
            CNT_THREE = cursor.fetchone()
            if CNT_THREE[0] == 0:
                FIRST_GROWTH = (0, 0)
                SKIP_FLAG = 10
            else:
                cursor.execute('select round(((CLOSE-:vBASE_PRICE)/:vBASE_PRICE )*100,2) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)+3', vsymbol=i, vinsert_date=FIRST_GROWTH_DATE, vBASE_PRICE=BASE_PRICE)
                FIRST_GROWTH = cursor.fetchone()
        else:
            cursor.execute('select round(((CLOSE-:vBASE_PRICE)/:vBASE_PRICE )*100,2) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)+2', vsymbol=i, vinsert_date=FIRST_GROWTH_DATE, vBASE_PRICE=BASE_PRICE)
            FIRST_GROWTH = cursor.fetchone()
    else:
        cursor.execute('select round(((CLOSE-:vBASE_PRICE)/:vBASE_PRICE )*100,2) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)', vsymbol=i, vinsert_date=FIRST_GROWTH_DATE, vBASE_PRICE=BASE_PRICE)
        FIRST_GROWTH = cursor.fetchone()
    #print('firstgrowth  %s' % FIRST_GROWTH[0])
    ## ---- 14. Second GROWTH calculation --- ###
    cursor.execute('select count(*) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)', vsymbol=i, vinsert_date=SECOND_GROWTH_DATE)
    CNT = cursor.fetchone()
    if CNT[0] == 0:
        cursor.execute("select count(*) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date,'yyyy-mm-dd')+2", vsymbol=i, vinsert_date=SECOND_GROWTH_DATE)
        CNT_TWO = cursor.fetchone()
        if CNT_TWO[0] == 0:
            cursor.execute('select count(*) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)+3', vsymbol=i, vinsert_date=SECOND_GROWTH_DATE)
            CNT_THREE = cursor.fetchone()
            if CNT_THREE[0] == 0:
                SECOND_GROWTH = (0, 0)
                SKIP_FLAG = 10
            else:
                cursor.execute('select round(((CLOSE-:vBASE_PRICE)/:vBASE_PRICE )*100,2) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)+3', vsymbol=i, vinsert_date=SECOND_GROWTH_DATE, vBASE_PRICE=BASE_PRICE)
                SECOND_GROWTH = cursor.fetchone()
        else:
            cursor.execute('select round(((CLOSE-:vBASE_PRICE)/:vBASE_PRICE )*100,2) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)+2', vsymbol=i, vinsert_date=SECOND_GROWTH_DATE, vBASE_PRICE=BASE_PRICE)
            SECOND_GROWTH = cursor.fetchone()
    else:
        cursor.execute('select round(((CLOSE-:vBASE_PRICE)/:vBASE_PRICE )*100,2) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)', vsymbol=i, vinsert_date=SECOND_GROWTH_DATE, vBASE_PRICE=BASE_PRICE)
        SECOND_GROWTH = cursor.fetchone()
    #print('second growth %s' % SECOND_GROWTH[0])
    ## ---- 15. Third GROWTH calculation --- ###
    cursor.execute('select max(tradedate) from nasdaq_hist')
    CURR_DATE = cursor.fetchone()
    cursor.execute('select count(*) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)', vsymbol=i, vinsert_date=CURR_DATE[0])
    CNT = cursor.fetchone()
    if CNT[0] == 0:
        cursor.execute("select count(*) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date,'yyyy-mm-dd')-1", vsymbol=i, vinsert_date=CURR_DATE[0])
        CNT_TWO = cursor.fetchone()
        if CNT_TWO[0] == 0:
            cursor.execute('select count(*) from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)-2', vsymbol=i, vinsert_date=CURR_DATE[0])
            CNT_THREE = cursor.fetchone()
            if CNT_THREE[0] == 0:
                CURR_PRICE = (0, 0)
                SKIP_FLAG = 10
            else:
                cursor.execute('select CLOSE from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)-2', vsymbol=i, vinsert_date=CURR_DATE[0])
                CURR_PRICE = cursor.fetchone()
        else:
            cursor.execute('select CLOSE from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)-1', vsymbol=i, vinsert_date=CURR_DATE[0])
            CURR_PRICE = cursor.fetchone()
    else:
        cursor.execute('select CLOSE from nasdaq_hist where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)', vsymbol=i, vinsert_date=CURR_DATE[0])
        CURR_PRICE = cursor.fetchone()
    #print('current price  %s' % CURR_PRICE[0])
    THIRD_GROWTH = round(((CURR_PRICE[0] - BASE_PRICE) / BASE_PRICE) * 100, 2)
    #print('Third growth %s' % THIRD_GROWTH)
    ## ---- 16. AVG calculation --- ###
    cursor.execute('select count(*) from nasdaq_AVG where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)', vsymbol=i, vinsert_date=CURR_DATE[0])
    CNT_AVG = cursor.fetchone()
    if CNT_AVG[0] == 0:
        cursor.execute("select count(*) from nasdaq_AVG where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date,'yyyy-mm-dd')-1", vsymbol=i, vinsert_date=CURR_DATE[0])
        CNT_AVG_TWO = cursor.fetchone()
        if CNT_AVG_TWO[0] == 0:
            cursor.execute('select count(*) from nasdaq_AVG where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)-2', vsymbol=i, vinsert_date=CURR_DATE[0])
            CNT_AVG_THREE = cursor.fetchone()
            if CNT_AVG_THREE[0] == 0:
                AVG_PRICE = (0, 0)
            else:
                cursor.execute('select FIFTYAVGPRI,ONEFIFTYAVGPRI from nasdaq_AVG where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)-2', vsymbol=i, vinsert_date=CURR_DATE[0])
                AVG_PRICE = cursor.fetchone()
        else:
            cursor.execute('select FIFTYAVGPRI,ONEFIFTYAVGPRI from nasdaq_AVG where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)-1', vsymbol=i, vinsert_date=CURR_DATE[0])
            AVG_PRICE = cursor.fetchone()
    else:
        cursor.execute('select FIFTYAVGPRI,ONEFIFTYAVGPRI from nasdaq_AVG where symbol=:vsymbol and TRADEDATE=to_date(:vinsert_date)', vsymbol=i, vinsert_date=CURR_DATE[0])
        AVG_PRICE = cursor.fetchone()
    ## ---- 17. Recent Fall calculation --- ###
    cursor.execute('select min(PRCNT_CHANGE) from NASDAQ_AVG where symbol=:vsymbol and TRADEDATE between to_date(:vinsert_date)-13 and to_date(:vinsert_date) ', vsymbol=i, vinsert_date=FIRST_PDATE[0])
    RECENT_FALL = cursor.fetchone()
    ## ---- 18. EPS calculation --- ###
    cursor.execute("select EPS from (select REPORT_DATE,SYMBOL,REVENUE,EPS,rank() over (partition by symbol order by REPORT_DATE desc) as rnk from financials where symbol=:vsymbol) where rnk=2", vsymbol=i)
    PRE_EPS = cursor.fetchone()
    if PRE_EPS is None or PRE_EPS[0] is None:
        PRE_EPS = (0, 0)
        #print('entered preeps')
    cursor.execute("select EPS from (select REPORT_DATE,SYMBOL,REVENUE,EPS,rank() over (partition by symbol order by REPORT_DATE desc) as rnk from financials where symbol=:vsymbol) where rnk=1", vsymbol=i)
    CURR_EPS = cursor.fetchone()
    if CURR_EPS is None or CURR_EPS[0] is None:
        CURR_EPS = (0, 0)
        #print('entered curreps')
    ## ---- 19. Revenue calculation --- ###
    cursor.execute("select REVENUE from (select REPORT_DATE,SYMBOL,REVENUE,EPS,rank() over (partition by symbol order by REPORT_DATE desc) as rnk from financials where symbol=:vsymbol) where rnk=2", vsymbol=i)
    PRE_R = cursor.fetchone()
    #print(PRE_R)
    if PRE_R is None or PRE_R[0] is None:
        PRE_R = (0, 0)
        #print('pre_r is none')
    cursor.execute("select REVENUE from (select REPORT_DATE,SYMBOL,REVENUE,EPS,rank() over (partition by symbol order by REPORT_DATE desc) as rnk from financials where symbol=:vsymbol) where rnk=1", vsymbol=i)
    CURR_R = cursor.fetchone()
    if CURR_R is None or CURR_R[0] is None:
        CURR_R = (0, 0)
        #print('entered currr')
    #print('fund growth %s %s %s  ' % (PRE_EPS[0], PRE_R[0], CURR_R[0]))
    ## ---- 20. P/E calculation --- ###
    if CURR_EPS[0] == 0:
        PURCHASE_PE = 0
        CURR_PE = 0
    else:
        PURCHASE_PE = round(BASE_PRICE / CURR_EPS[0], 2)
        CURR_PE = round(CURR_PRICE[0] / CURR_EPS[0], 2)
    #print('entered currr %s %s ' % (PURCHASE_PE, CURR_PE))
    ## ---- 21. Insert into analytics --- ###
    cursor.execute("select count(*) from analytics where symbol=:vsymbol and flag=0", vsymbol=i)
    SYM_CNT = cursor.fetchone()
    cursor.execute("select max(tradedate) from nasdaq_avg ")
    CDATE = cursor.fetchone()
    UDATE = CDATE
    if SYM_CNT[0] == 0:
        insert_stmt = "insert into ANALYTICS (SYMBOL,PCOUNT,VCOUNT,PRNK,VRNK,FIRST_PDATE,LAST_PDATE,PI_PRICE,VI_PRICE,CURR_PRICE,BASE_PRICE,FIFTYAVG,ONEFIFTYAVG,RECENT_FALL,FIRSTGROWTH,SECONDGROWTH,THIRDGROWTH,PREEPS,CURR_EPS,PRER,CURR_R,PURCHASE_PE,CURR_PE,FLAG,CDATE,UDATE) values (:vSYMBOL,:vPCOUNT,:vVCOUNT,:vPRNK,:vVRNK,:vFIRST_PDATE,:vLAST_PDATE,:vPI_PRICE,:vVI_PRICE,:vCURR_PRICE,:vBASE_PRICE,:vFIFTYAVG,:vONEFIFTYAVG,:vRECENT_FALL,:vFIRSTGROWTH,:vSECONDGROWTH,:vTHIRDGROWTH,:vPREEPS,:vCURR_EPS,:vPRER,:vCURR_R,:vPURCHASE_PE,:vCURR_PE,0,:vCDATE,:vUDATE)"
        cursor.execute(insert_stmt, vSYMBOL=i, vPCOUNT=pcount[0], vVCOUNT=vcount[0], vPRNK=PRNK_S, vVRNK=VRNK_S, vFIRST_PDATE=FIRST_PDATE[0], vLAST_PDATE=LAST_PDATE[0], vPI_PRICE=PI_PRICE[0], vVI_PRICE=VI_PRICE[0], vCURR_PRICE=CURR_PRICE[0], vBASE_PRICE=BASE_PRICE, vFIFTYAVG=AVG_PRICE[0], vONEFIFTYAVG=AVG_PRICE[1], vRECENT_FALL=RECENT_FALL[0], vFIRSTGROWTH=FIRST_GROWTH[0], vSECONDGROWTH=SECOND_GROWTH[0], vTHIRDGROWTH=THIRD_GROWTH, vPREEPS=PRE_EPS[0], vCURR_EPS=CURR_EPS[0], vPRER=PRE_R[0], vCURR_R=CURR_R[0], vPURCHASE_PE=PURCHASE_PE, vCURR_PE=CURR_PE, vCDATE=CDATE[0], vUDATE=UDATE[0])
        connection.commit()
        print(f"  {i:<8}  inserted  growth={FIRST_GROWTH[0]}/{SECOND_GROWTH[0]}/{THIRD_GROWTH}%")
    elif SYM_CNT[0] == 1:
        update_stmt = "update ANALYTICS set FIRST_PDATE=:vFIRST_PDATE,PCOUNT=:vPCOUNT,VCOUNT=:vVCOUNT,PRNK=:vPRNK,VRNK=:vVRNK,LAST_PDATE=:vLAST_PDATE,PI_PRICE=:vPI_PRICE,CURR_PRICE=:vCURR_PRICE,BASE_PRICE=:vBASE_PRICE,FIFTYAVG=:vFIFTYAVG,ONEFIFTYAVG=:vONEFIFTYAVG,THIRDGROWTH=:vTHIRDGROWTH,CURR_PE=:vCURR_PE,UDATE=:vUDATE where SYMBOL=:vSYMBOL "
        cursor.execute(update_stmt, vSYMBOL=i, vFIRST_PDATE=FIRST_PDATE[0], vPCOUNT=pcount[0], vVCOUNT=vcount[0], vPRNK=PRNK_S, vVRNK=VRNK_S, vLAST_PDATE=LAST_PDATE[0], vPI_PRICE=PI_PRICE[0], vCURR_PRICE=CURR_PRICE[0], vBASE_PRICE=BASE_PRICE, vFIFTYAVG=AVG_PRICE[0], vONEFIFTYAVG=AVG_PRICE[1], vTHIRDGROWTH=THIRD_GROWTH, vCURR_PE=CURR_PE, vUDATE=UDATE[0])
        connection.commit()
        print(f"  {i:<8}  updated   growth={FIRST_GROWTH[0]}/{SECOND_GROWTH[0]}/{THIRD_GROWTH}%")
    else:
        pass

print('=' * 65)
print('  Analytics complete.')
print('=' * 65)
