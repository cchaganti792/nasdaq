import sys
import os
import time
import cx_Oracle
import os
##os.environ['ORACLE_HOME'] ="C:\\app\User\product\\11.2.0\client_1"
import cx_Oracle
import os
connection = cx_Oracle.connect("nasdaq", "nasdaq123", "localhost/orcl")
cursor = connection.cursor()
def insert_db(sign,values):
    if sign==01:
        try:
            insert_stmt="insert into BULLISH (SYMBOL,INS_DATE,INS_PRICE,INS_CODE,BULL_CODE,TCH_CNT,UPD_DATE,INS_RNK,VOL_RNK,SEQUENCE) values (:vSYMBOL,to_date(:vINS_DATE,'dd-mon-yy'),to_number(:vINS_PRICE),:vINS_CODE,01,to_number(:vTCH_CNT),to_date(:vUPD_DATE,'dd-mon-yy'),to_number(:vINS_RNK),to_number(:vVOL_RNK),to_number(:vSEQUENCE))"
            cursor.execute(insert_stmt,vSYMBOL=values[0],vINS_DATE=values[1],vINS_PRICE=values[2],vINS_CODE=values[3],vTCH_CNT=values[4],vUPD_DATE=values[1],vINS_RNK=values[6],vVOL_RNK=values[7],vSEQUENCE=values[8])
            connection.commit()
        except cx_Oracle.IntegrityError:
            print values[0],values[4],values[1],values[6],values[7]
            update_stmt="update BULLISH set TCH_CNT=to_number(:vTCH_CNT),UPD_DATE=to_date(:vUPD_DATE,'dd-mon-yy'),INS_RNK=to_number(:vINS_RNK),VOL_RNK=to_number(:vVOL_RNK),SEQUENCE=to_number(:vSEQUENCE) where symbol=:vSYMBOL "
            cursor.execute(update_stmt,vSYMBOL=values[0],vTCH_CNT=values[4],vUPD_DATE=values[1],vINS_RNK=values[6],vVOL_RNK=values[7],vSEQUENCE=values[8])
            connection.commit()
            print values[0]+' row already present'
    if sign==02:
            try:
                update_stmt="update BULLISH set BULL_CODE=BULL_CODE+2 where symbol=:vSYMBOL AND BULL_CODE NOT IN (2,3,6,7)"
                cursor.execute(update_stmt,vSYMBOL=values[0])
                connection.commit()
                update_stmt="update BULLISH set INS_OF_PRCNT=to_number(:vINS_OF_PRCNT),INS_FIF_PRCNT=to_number(:vINS_FIF_PRCNT) where symbol=:vSYMBOL "
                cursor.execute(update_stmt,vSYMBOL=values[0],vINS_OF_PRCNT=values[1],vINS_FIF_PRCNT=values[2])
                connection.commit()
            except cx_Oracle.IntegrityError:
                print values[0]+' row already present'
    if sign==04:
            try:
                update_stmt="update BULLISH set BULL_CODE=BULL_CODE+4 where symbol=:vSYMBOL AND BULL_CODE NOT IN (4,5,6,7)"
                cursor.execute(update_stmt,vSYMBOL=values[0])
                connection.commit()
                update_stmt="update BULLISH set PRNK=:vPRNK,VRNK=:vVRNK,LAST_PDATE=to_date(:vLAST_PDATE,'dd-mon-yy') where symbol=:vSYMBOL "
                cursor.execute(update_stmt,vSYMBOL=values[0],vPRNK=values[1],vVRNK=values[2],vLAST_PDATE=values[3])
                connection.commit()
            except cx_Oracle.IntegrityError:
                print values[0]+' row already present'
    if sign==05:
            try:
                update_stmt="update BULLISH set CURRENTPRICE=to_number(:vCURRENTPRICE),PRCNT_CHANGE=to_number(:vPRCNT_CHANGE),TOT_GROWTH=to_number(:vTOT_GROWTH),FIVEDAYAVGPRI=to_number(:vFIVEDAYAVGPRI),TWENTYAVGPRI=to_number(:vTWENTYAVGPRI),FIFTYAVGPRI=to_number(:vFIFTYAVGPRI),ONEFIFTYAVGPRI=to_number(:vONEFIFTYAVGPRI),PRICED_DATE=to_date(:vPRICED_DATE,'dd-mon-yy') where symbol=:vSYMBOL"
                cursor.execute(update_stmt,vSYMBOL=values[0],vCURRENTPRICE=values[1],vPRCNT_CHANGE=values[2],vTOT_GROWTH=values[3],vFIVEDAYAVGPRI=values[4],vTWENTYAVGPRI=values[5],vFIFTYAVGPRI=values[6],vONEFIFTYAVGPRI=values[7],vPRICED_DATE=values[8])
                connection.commit()
                cursor.execute('UPDATE BULLISH SET CURR_OF_PRCNT=trunc(((CURRENTPRICE-ONEFIFTYAVGPRI)/ONEFIFTYAVGPRI)*100,1),CURR_FIF_PRCNT=trunc(((CURRENTPRICE-FIFTYAVGPRI)/FIFTYAVGPRI)*100,1) WHERE FIFTYAVGPRI<>0 AND ONEFIFTYAVGPRI<>0')
                connection.commit()
            except cx_Oracle.IntegrityError:
                print values[0]+' row already present'
    if sign==06:
            try:
                update_stmt="update BULLISH set PREEPS=to_number(:vPREEPS),CURR_EPS=to_number(:vCURR_EPS),PRER=to_number(:vPRER),CURR_R=to_number(:vCURR_R),CURR_PE=to_number(:vCURR_PE) where symbol=:vSYMBOL"
                cursor.execute(update_stmt,vSYMBOL=values[0],vPREEPS=values[1],vCURR_EPS=values[2],vPRER=values[3],vCURR_R=values[4],vCURR_PE=values[5])
                connection.commit()            
            except cx_Oracle.IntegrityError:
                print values[0]+' row already present'
    if sign==07:
            try:
                update_stmt="update BULLISH set VOLHIGH=to_number(:vVOLHIGH),VH_DATE=to_date(:vVH_DATE,'dd-mon-yy'),VH_PRCNT=to_number(:vVH_PRCNT) where symbol=:vSYMBOL"
                cursor.execute(update_stmt,vSYMBOL=values[0],vVOLHIGH=values[1],vVH_DATE=values[2],vVH_PRCNT=values[3])
                connection.commit()            
            except cx_Oracle.IntegrityError:
                print values[0]+' row already present'
    if sign==00:
            try:
                update_stmt="update bullish set rsi=(SELECT trunc(100-100/(1+TRUNC((SELECT TRUNC(SUM(PRCNT_CHANGE)/14,2) FROM (SELECT * FROM (select * from nasdaq_avg where symbol=:vSYMBOL ORDER BY TRADEDATE DESC ) WHERE ROWNUM<15) WHERE PRCNT_CHANGE>0)/ (SELECT (ABS(SUM(PRCNT_CHANGE)/14)) FROM (SELECT * FROM (select * from nasdaq_avg where symbol=:vSYMBOL ORDER BY TRADEDATE DESC ) WHERE ROWNUM<15) WHERE PRCNT_CHANGE<0),2)),2) FROM DUAL) where symbol=:vSYMBOL"
                cursor.execute(update_stmt,vSYMBOL=values[0])
                connection.commit()            
            except cx_Oracle.IntegrityError:
                print values[0]+' row already present'
## bACKUP INTO BULLISH_LOG ##
cursor.execute('INSERT INTO bullish_LOG  SELECT * FROM BULLISH')
connection.commit()
## All data from all_positive ##
cursor.execute('select SYMBOL,INS_DATE,CURRENTPRICE,INS_CODE,TCH_CNT,INS_DATE,INS_RNK,VOL_RNK,SEQUENCE from all_positive where INS_DATE in (select max(tradedate) from nasdaq_avg)')
data_input=cursor.fetchall()
for row in data_input:
    print row
    insert_db(01,row)
##        symbol_input_lis.append(row[0])
### Symbol who's current_price is less Than 150 avg or fifty avg and raising  from all_positive ## 
cursor.execute('SELECT SYMBOL,trunc(((CURRENTPRICE-ONEFIFTYAVGPRI)/ONEFIFTYAVGPRI)*100) AS OFPRCNT,trunc(((CURRENTPRICE-FIFTYAVGPRI)/FIFTYAVGPRI)*100) AS FIFPRCNT          FROM all_positive where INS_DATE=(select max(tradedate) from nasdaq_avg)  AND ((CURRENTPRICE <=ONEFIFTYAVGPRI) OR (CURRENTPRICE <=FIFTYAVGPRI))  ORDER BY OFPRCNT')
data_input=cursor.fetchall()
for row in data_input:
    print row
    insert_db(02,row)
### Symbol which in intersection of analytics and all_positive meaning top 25 in swim lane  01,02,04 numbering system is to identify where the stock is coming from   ## 
cursor.execute('select SYMBOL,PRNK,VRNK,UDATE from analytics where symbol in (select SYMBOL from analytics where trunc(UDATE) > (select max(tradedate)-10 from nasdaq_avg) and pcount<>0 and VCOUNT<>0 INTERSECT  SELECT SYMBOL FROM all_positive where INS_DATE in (select max(tradedate) from nasdaq_avg) union select SYMBOL from analytics where trunc(UDATE) in (select max(tradedate)-10 from nasdaq_avg) and pcount<>0  INTERSECT  SELECT SYMBOL FROM all_positive where INS_DATE in (select max(tradedate) from nasdaq_avg))')
data_input=cursor.fetchall()
for row in data_input:
    print row
    insert_db(04,row)
### CURRENT price growth calculations ###
cursor.execute('SELECT N.SYMBOL,N.CURRENTPRICE,trunc(N.PRCNT_CHANGE,1),trunc(((N.CURRENTPRICE-B.INS_PRICE)/B.INS_PRICE)*100,1) AS TOT_GROWTH,N.FIVEDAYAVGPRI,N.TWENTYAVGPRI,N.FIFTYAVGPRI,N.ONEFIFTYAVGPRI,N.TRADEDATE FROM NASDAQ_AVG N,BULLISH B WHERE  B.SYMBOL=N.SYMBOL  AND N.TRADEDATE=(SELECT MAX(TRADEDATE) FROM NASDAQ_AVG)')
data_input=cursor.fetchall()
for row in data_input:
    print row
    insert_db(05,row)
### FUNDAMENTAL DATA  ###
cursor.execute('SELECT N.SYMBOL,F.SEPS,F.EPS,F.SREVENUE,F.REVENUE,trunc(N.CURRENTPRICE/F.EPS) AS curr_PE FROM NASDAQ_AVG N,FUNDA F,BULLISH B WHERE F.SYMBOL=N.SYMBOL AND B.SYMBOL=F.SYMBOL AND F.TRADEDATE=N.TRADEDATE AND F.TRADEDATE=(SELECT MAX(TRADEDATE) FROM NASDAQ_AVG)')
data_input=cursor.fetchall()
for row in data_input:
    print row
    insert_db(06,row)
### VOL HIGHS ####
cursor.execute('SELECT DISTINCT  B.SYMBOL,(SELECT COUNT(*) FROM VOL_TOPPERS_HIST WHERE SYMBOL=B.SYMBOL AND PRCNT_CHANGE>0) AS CNT,(SELECT MAX(TRADEDATE) FROM VOL_TOPPERS_HIST WHERE SYMBOL=B.SYMBOL ) AS VHDATE,trunc((select PRCNT_CHANGE from VOL_TOPPERS_HIST where TRADEDATE in (SELECT MAX(TRADEDATE) FROM VOL_TOPPERS_HIST WHERE SYMBOL=B.SYMBOL) and symbol=B.SYMBOL),2) as VH_PRCNT FROM BULLISH B,VOL_TOPPERS_HIST V WHERE B.SYMBOL=V.SYMBOL AND V.TRADEDATE>B.PRICED_DATE-120 ORDER BY B.SYMBOL')
data_input=cursor.fetchall()
for row in data_input:
    print row
    insert_db(07,row)
### Buy  DATA  ###
cursor.execute('UPDATE bullish SET C1=1 WHERE RNK<21')
cursor.execute('UPDATE bullish SET C2=1 WHERE DRNK<11')
cursor.execute('UPDATE bullish SET C3=1 WHERE ins_date=(select max(tradedate) from nasdaq_avg) AND  CURR_R>PRER AND CURR_EPS>PREEPS')
cursor.execute('update bullish set c4=1 where vh_date>(select max(tradedate)-3 from nasdaq_avg) and vh_prcnt>0')
connection.commit()
cursor.execute('UPDATE bullish SET BUY_FLAG=1,BUY_DATE=UPD_DATE,BUY_PRICE=CURRENTPRICE WHERE (c1=1) or (c2=1) or (c3=1) or (c4=1)   AND buy_flag<>1')
connection.commit()
### TOP GROWTH RANKS ####
cursor.execute('update bullish B set B.rnk=(select rnk from (SELECT SYMBOL,INS_DATE,INS_PRICE,TOT_GROWTH,PRICED_DATE,RANK() OVER ( PARTITION BY PRICED_DATE ORDER BY TOT_GROWTH DESC) AS RNK FROM BULLISH ) R where  R.symbol=B.SYMBOL)')
cursor.execute('update bullish B set B.drnk=(select rnk from (SELECT SYMBOL,INS_DATE,INS_PRICE,TOT_GROWTH,PRICED_DATE,RANK() OVER ( PARTITION BY PRICED_DATE ORDER BY TOT_GROWTH DESC) AS RNK FROM BULLISH WHERE INS_DATE>(SELECT MAX(TRADEDATE)-5 FROM NASDAQ_AVG)) R where  R.symbol=B.SYMBOL)')
connection.commit()
### RSI Calculation ###
cursor.execute('SELECT DISTINCT  SYMBOL from bullish')
data_input=cursor.fetchall()
for row in data_input:
    print row
    insert_db(00,row)
### Remove Data ###
#cursor.execute('insert into bullish_deleted select * from bullish where upd_date<sysdate-12 and SEQUENCE+tch_cnt<=1')
#cursor.execute('delete from bullish where upd_date<sysdate-12 and SEQUENCE+tch_cnt<=1')
#cursor.execute('insert into bullish_deleted select * from bullish where upd_date<sysdate-15 and SEQUENCE+tch_cnt<=2')
#cursor.execute('delete from bullish where upd_date<sysdate-15 and SEQUENCE+tch_cnt<=2')
#cursor.execute('insert into bullish_deleted select * from bullish where upd_date<sysdate-19 and SEQUENCE+tch_cnt<=3')
#cursor.execute('delete from bullish where upd_date<sysdate-19 and SEQUENCE+tch_cnt<=3')
#cursor.execute('insert into bullish_deleted select * from bullish where upd_date<sysdate-25 and SEQUENCE+tch_cnt<=5')
#cursor.execute('delete from bullish where upd_date<sysdate-25 and SEQUENCE+tch_cnt<=5')
#cursor.execute('insert into bullish_deleted select * from bullish where upd_date<sysdate-50')
#cursor.execute('delete from bullish where upd_date<sysdate-50')
cursor.execute('insert into bullish_deleted select * from bullish where symbol in (select  distinct b.symbol from bullish b,all_negitive n where n.symbol=b.symbol and n.tch_cnt+n.sequence>b.tch_cnt+b.sequence  and n.ins_date>b.ins_date and b.ins_rnk>20 and b.buy_flag<>1)')
cursor.execute('delete from bullish where symbol in (select  distinct b.symbol from bullish b,all_negitive n where n.symbol=b.symbol and n.tch_cnt+n.sequence>b.tch_cnt+b.sequence  and n.ins_date>b.ins_date and b.ins_rnk>20  and b.buy_flag<>1)')
cursor.execute('insert into bullish_deleted select * from bullish where symbol in (select  distinct b.symbol from bullish b,neg_vol n where n.symbol=b.symbol  and n.insert_date>b.UPD_DATE and b.buy_flag<>1) ')
cursor.execute('delete from bullish where symbol in (select  distinct b.symbol from bullish b,neg_vol n where n.symbol=b.symbol  and n.insert_date>b.UPD_DATE and b.buy_flag<>1)')
cursor.execute('insert into bullish_deleted select * from bullish where priced_date<>(select max(tradedate) from nasdaq_avg)')
cursor.execute('delete from bullish where priced_date<>(select max(tradedate) from nasdaq_avg)')
connection.commit()

