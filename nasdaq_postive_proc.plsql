create or replace procedure     nasdaq_postive_proc (TRADEDATE  IN date default null)
is
in_symbol  varchar2(20);
v_symbol varchar2(60);
v_PRIVCLOSE number;
v_OPENPRICE number;
v_CURRENTVOL NUMBER;
v_FIVEDAYAVGPRI number;
v_TWENTYAVGPRI number;
v_FIFTYAVGPRI  number;
v_ONEFIFTYAVGPRI number;
v_FIVEDAYVOL number;
v_TWENTYAVGVOL number;
v_FIFTYAVGVOL  number;
v_ONEFIFTYAVGVOL number;
v_TRADEDATE DATE;
v_CURRENTPRICE NUMBER;
v_PRCNT_CHANGE NUMBER;
v_TOTPRICEPRCNT NUMBER;
v_SEPS NUMBER;
v_EPS NUMBER;
v_SREVENUE NUMBER;
v_REVENUE NUMBER;
v_RNK NUMBER;
v_INSERT_DATE DATE;
v_Insert_cnt number;
v_insert_CURRENTPRICE number;
--v_INS_CODE CHAR(6);
--v_tradedate1 date;
max_tradedate date;
v_TRADEDATE1 date;
v_interim_tradedate1  date;
v_interim_tradedate2  date;
v_interim_tradedate3  date;
begin_bound number;
end_bound  number;
v_INS_CODE varchar2(6);
in_INS_CODE varchar2(6);
in_INS_CODE2 varchar2(30);
v_level number;
v_count number;
createtempstmt VARCHAR2(2000);
inserttempstmt VARCHAR2(2000);
tempstmt VARCHAR2(2000);
upstmt VARCHAR2(2000);
rnk_stmnt VARCHAR2(2000);
v_curr_table varchar2(15);
v_DAY_WISE_GRTH varchar2(20);
v_TCH_CNT number;
v_SEQ_CNT number;
v_VOL_RNK number;
v_CNT1 number;

CURSOR C0 (in_INS_CODE varchar2) is select distinct symbol from PRICE_INTERIM WHERE INS_CODE=in_INS_CODE  ;
CURSOR C1 (in_INS_CODE varchar2,v_SYMBOL varchar2) is select * from PRICE_INTERIM WHERE INS_CODE=in_INS_CODE and symbol=v_SYMBOL ORDER BY TRADEDATE DESC ;


--CURSOR C2 (in_INS_CODE varchar2,v_SYMBOL varchar2) is select * from PRICE_INTERIM WHERE INS_CODE=in_INS_CODE and symbol=v_SYMBOL ORDER BY TRADEDATE DESC ;

begin
if (TRADEDATE is null)
 then
  select max(tradedate) into v_tradedate1  from nasdaq.nasdaq_hist;
  --select current_load_date into v_tradedate1 from nse.load_date;
  else
   v_TRADEDATE1:=TRADEDATE;
end if;
--createtempstmt:='CREATE  table PRICE_INTERIM  ON COMMIT PRESERVE ROWS as select SYMBOL,TRADEDATE,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,SEPS,EPS,SREVENUE,REVENUE,rnk,(select sysdate from dual) as Insert_date,(SELECT 'ABCDEF' FROM DUAL) AS INS_CODE  from (select SYMBOL,TRADEDATE,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,SEPS,EPS,SREVENUE,REVENUE,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from (select p.symbol,p.TRADEDATE,p.CURRENTPRICE,p.PRCNT_CHANGE,p.TOTPRICEPRCNT,f.SEPS,f.EPS,f.SREVENUE,f.REVENUE,p.CURRENTVOL,p.ONEFIFTYAVGVOL from (select symbol,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,SUM(PRCNT_CHANGE) over (partition by symbol) TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL from ( select symbol,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,CURRENTVOL,((CURRENTVOL-FIFTYAVGVOL)/FIFTYAVGVOL)*100 as FFVOLDIFFPRCNT,FIFTYAVGVOL,ONEFIFTYAVGVOL,RANK() OVER (PARTITION BY symbol ORDER BY tradedate DESC) RNK       from nasdaq_avg where round(ONEFIFTYAVGVOL)>0 and round(ONEFIFTYAVGVOL)<=1 and FIFTYAVGVOL<>0 and symbol not in (select symbol from donot_track) and tradedate between sysdate-6 and sysdate ) where rnk<4 ) p left outer join (select SYMBOL,SEPS,EPS,SREVENUE,REVENUE,TRADEDATE from funda ) f on p.symbol=f.symbol and p.tradedate=f.tradedate order by TOTPRICEPRCNT,SYMBOL,tradedate)) ';
dbms_output.put_line('Tradedate1 is '|| v_TRADEDATE1);
--EXECUTE IMMEDIATE createtempstmt ;

inserttempstmt:='insert into  PRICE_INTERIM    select SYMBOL,TRADEDATE,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,SEPS,EPS,SREVENUE,REVENUE,rnk,(select :v_TRADEDATE1 from dual) as Insert_date,(SELECT :v_INS_CODE FROM DUAL) AS INS_CODE from (select SYMBOL,TRADEDATE,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,SEPS,EPS,SREVENUE,REVENUE,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from (select p.symbol,p.TRADEDATE,p.CURRENTPRICE,p.PRCNT_CHANGE,p.TOTPRICEPRCNT,f.SEPS,f.EPS,f.SREVENUE,f.REVENUE,p.CURRENTVOL,p.ONEFIFTYAVGVOL from (select symbol,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,SUM(PRCNT_CHANGE) over (partition by symbol) TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL from ( select symbol,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,CURRENTVOL,((CURRENTVOL-FIFTYAVGVOL)/FIFTYAVGVOL)*100 as FFVOLDIFFPRCNT,FIFTYAVGVOL,ONEFIFTYAVGVOL,RANK() OVER (PARTITION BY symbol ORDER BY tradedate DESC) RNK       from nasdaq_avg where round(ONEFIFTYAVGVOL)>:begin_bound and round(ONEFIFTYAVGVOL)<=:end_bound and FIFTYAVGVOL<>0 and symbol not in (select symbol from donot_track) and length(symbol)<5 and tradedate between :v_TRADEDATE2 and :v_TRADEDATE1 ) where rnk<4 ) p left outer join (select SYMBOL,SEPS,EPS,SREVENUE,REVENUE,TRADEDATE from funda ) f on p.symbol=f.symbol and p.tradedate=f.tradedate order by TOTPRICEPRCNT,SYMBOL,tradedate)) ';
EXECUTE IMMEDIATE 'TRUNCATE TABLE PRICE_INTERIM ';
for i in 1..6 loop
if (i=1) then
begin_bound:=0;
end_bound:=1;
v_INS_CODE:='01';
elsif (i=2) then
begin_bound:=1;
end_bound:=5;
v_INS_CODE:='15';
elsif (i=3) then
begin_bound:=5;
end_bound:=16;
v_INS_CODE:='516';
elsif (i=4) then
begin_bound:=16;
end_bound:=25;
v_INS_CODE:='1625';
elsif (i=5) then
begin_bound:=25;
end_bound:=75;
v_INS_CODE:='2575';
else
begin_bound:=75;
end_bound:=125;
v_INS_CODE:='75';
end if;
DBMS_OUTPUT.PUT_LINE('insert code   is   '||v_INS_CODE);
EXECUTE IMMEDIATE inserttempstmt USING  v_TRADEDATE1,v_INS_CODE,begin_bound,end_bound,v_TRADEDATE1-6,v_TRADEDATE1;
commit;
end loop;
select tradedate into v_interim_tradedate1 from (select tradedate,ROW_NUMBER()OVER(order by  tradedate desc) RowNo  from (select distinct tradedate from PRICE_INTERIM order by tradedate)) where rowno=1;
select tradedate into v_interim_tradedate2 from (select tradedate,ROW_NUMBER()OVER(order by  tradedate desc) RowNo  from (select distinct tradedate from PRICE_INTERIM order by tradedate)) where rowno=2;
select tradedate into v_interim_tradedate3 from (select tradedate,ROW_NUMBER()OVER(order by  tradedate desc) RowNo  from (select distinct tradedate from PRICE_INTERIM order by tradedate)) where rowno=3;
DBMS_OUTPUT.PUT_LINE('v_interim_tradedate1 is   '||v_interim_tradedate1);
for i in 1..6 loop
if (i=1) then
in_INS_CODE:='01';
elsif (i=2) then
in_INS_CODE:='15';
elsif (i=3) then
in_INS_CODE:='516';
elsif (i=4) then
in_INS_CODE:='1625';
elsif (i=5) then
in_INS_CODE:='2575';
else
in_INS_CODE:='75';
end if;
-- start reading from PRICE_INTERIM  -----
open C0(in_INS_CODE);
--open C0 ;
        LOOP
        FETCH C0 into v_SYMBOL;
        DBMS_OUTPUT.PUT_LINE('symbol is   '||v_SYMBOL||'-'||in_INS_CODE);
        EXIT WHEN C0%NOTFOUND;
select count(*) into v_count from PRICE_INTERIM WHERE INS_CODE=in_INS_CODE and symbol=v_SYMBOL;
        select max(tradedate) into max_tradedate from PRICE_INTERIM WHERE INS_CODE=in_INS_CODE and symbol=v_SYMBOL;
        if (v_count=3 and max_tradedate=v_interim_tradedate1 )then
    v_Insert_cnt:=0;
v_DAY_WISE_GRTH:='';
v_curr_table:=nasdaq_tab(in_symbol=>v_SYMBOL,in_INS_CODE=>in_INS_CODE);
if (v_curr_table<>'dummy') then
v_TCH_CNT:=tch_cnt(in_symbol=>v_SYMBOL,in_curr_tab=>v_curr_table).TCH_CNT;
v_SEQ_CNT:=tch_cnt(in_symbol=>v_SYMBOL,in_curr_tab=>v_curr_table).SEQ;
            open C1(in_INS_CODE,v_SYMBOL) ;
            LOOP
            FETCH C1 into v_SYMBOL,v_TRADEDATE,v_CURRENTPRICE,v_PRCNT_CHANGE,v_TOTPRICEPRCNT,v_SEPS,v_EPS,v_SREVENUE,v_REVENUE,v_RNK,v_INSERT_DATE,v_INS_CODE;
            EXIT WHEN C1%NOTFOUND;
            if (v_Insert_cnt<1) then
v_insert_CURRENTPRICE:=v_CURRENTPRICE;
v_Insert_cnt:=v_Insert_cnt+1;
end if;
v_DAY_WISE_GRTH:=concat(v_DAY_WISE_GRTH,concat('+',round(v_PRCNT_CHANGE,1)));
            end loop;
DBMS_OUTPUT.PUT_LINE('insert symbol is : '||v_SYMBOL);
DBMS_OUTPUT.PUT_LINE('growth is : '||v_DAY_WISE_GRTH);
in_INS_CODE2:=concat('nasbull_vol_',in_INS_CODE);
DBMS_OUTPUT.PUT_LINE('insert symbol is : '||v_SYMBOL||'--INS DATE :'||v_INSERT_DATE||'--INS SCRIPT IS :'||in_INS_CODE2);
select count(*) into v_CNT1  from vol_log where symbol=v_SYMBOL and insert_date=v_INSERT_DATE and INSER_SCRIPT=in_INS_CODE2;
DBMS_OUTPUT.PUT_LINE('rank row cnt is : '||v_CNT1);
if (v_CNT1>=0) then
rnk_stmnt:='select MIN(rnk)  FROM (SELECT DISTINCT  RNK,INSERT_DATE from vol_log where symbol='''||v_SYMBOL||''' and insert_date='''||v_INSERT_DATE||''' GROUP BY  RNK,INSERT_DATE HAVING SUM(PRCNT_CHANGE)>0 UNION SELECT DISTINCT RNK,INSERT_DATE from vol2_log where symbol='''||v_SYMBOL||''' and insert_date='''||v_INSERT_DATE||''' GROUP BY  RNK,INSERT_DATE HAVING SUM(PRCNT_CHANGE)>0)';
DBMS_OUTPUT.PUT_LINE('rank state: '||rnk_stmnt);
EXECUTE IMMEDIATE rnk_stmnt into v_VOL_RNK ;
null;
else
v_VOL_RNK:=0;
end if;
tempstmt:='insert into '||v_curr_table||' (SYMBOL,INS_DATE,INS_CODE,INS_RNK,VOL_RNK,DAY_WISE_GRTH,TOT_GROWTH,TCH_CNT,CURRENTPRICE,PREEPS,CURR_EPS,PRER,CURR_R,SEQUENCE) values (:v_SYMBOL,:INS_DATE,:INS_CODE,:INS_RNK,:VOL_RNK,:DAY_WISE_GRTH,:TOT_GROWTH,:TCH_CNT,:CURRENTPRICE,:PREEPS,:CURR_EPS,:PRER,:CURR_R,:SEQUENCE)';
DBMS_OUTPUT.PUT_LINE('insert state: '||tempstmt);
EXECUTE IMMEDIATE tempstmt using v_SYMBOL,v_INSERT_DATE,v_INS_CODE,v_RNK,v_VOL_RNK,v_DAY_WISE_GRTH,v_TOTPRICEPRCNT,v_TCH_CNT,v_insert_CURRENTPRICE,v_SEPS,v_EPS,v_SREVENUE,v_REVENUE,v_SEQ_CNT;
commit;
upstmt:='UPDATE (SELECT A.FIVEDAYAVGPRI FDAVG1,A.TWENTYAVGPRI TDAVG1,A.FIFTYAVGPRI FIFAVG1,A.ONEFIFTYAVGPRI OFAVG1,P.FIVEDAYAVGPRI FDAVG2,P.TWENTYAVGPRI TDAVG2,P.FIFTYAVGPRI FIFAVG2,P.ONEFIFTYAVGPRI OFAVG2 FROM NASDAQ_AVG A ,all_positive P WHERE P.INS_DATE=A.TRADEDATE AND A.SYMBOL=P.SYMBOL AND P.SYMBOL=:v_SYMBOL ) SET FDAVG2=FDAVG1,TDAVG2=TDAVG1,FIFAVG2=FIFAVG1,OFAVG2=OFAVG1';
EXECUTE IMMEDIATE upstmt using v_SYMBOL;
commit;
            close C1;
end if;
elsif (v_count=3 and max_tradedate<v_interim_tradedate1) then
DBMS_OUTPUT.PUT_LINE('Tradedate is old for symbol '||v_SYMBOL||'-'||max_tradedate||'-'||in_INS_CODE);
elsif (v_count=2 and max_tradedate<=v_interim_tradedate1) then
DBMS_OUTPUT.PUT_LINE('Fetching from entire table symbol '||v_SYMBOL||'-'||in_INS_CODE);
elsif (v_count=1 ) then
DBMS_OUTPUT.PUT_LINE('Doing nothing as cnt is one '||v_SYMBOL||'-'||in_INS_CODE);
else
DBMS_OUTPUT.PUT_LINE('Entered else part '||v_SYMBOL||'-'||in_INS_CODE);
null;
end if;
end loop;
close C0;
DBMS_OUTPUT.PUT_LINE('close is   ');
end loop;
end;