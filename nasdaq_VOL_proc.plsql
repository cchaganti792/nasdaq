create or replace procedure     nasdaq_VOL_proc (TRADEDATE  IN date default null)
is
type string_list is table of varchar2(500);
my_list string_list := string_list('nasbull_vol_01','nasbull_vol_15','nasbull_vol_516','nasbull_vol_1625','nasbull_vol_2575','nasbull_vol_75');
in_symbol  varchar2(20);
v_symbol varchar2(60);
v_CURRENTVOL NUMBER;
v_TRADEDATE DATE;
v_CURRENTPRICE NUMBER;
v_PRCNT_CHANGE NUMBER;
v_TOTDIFFVOLPRCNT NUMBER;
v_FFVOLDIFFPRCNT NUMBER;
v_INSERT_DATE DATE;
v_Insert_cnt number;
v_insert_CURRENTPRICE number;
max_tradedate date;
v_TRADEDATE1 date;
v_interim_tradedate1  date;
v_interim_tradedate2  date;
v_interim_tradedate3  date;
v_INS_CODE char(30);
in_INS_CODE char(30);
in_INS_CODE2 varchar2(30);
v_level number;
v_count number;
createtempstmt VARCHAR2(2000);
inserttempstmt VARCHAR2(2000);
tempstmt VARCHAR2(2000);
v_curr_table varchar2(15);
v_DAY_WISE_GRTH varchar2(50);
v_DAY_VOL_PRCNT varchar2(50);
v_TOT_PRICE_PRCNT number;
v_TCH_CNT number;
v_VOL_RNK number;
v_RNK number;


CURSOR C0 (in_INS_CODE varchar2) is select distinct symbol from VOL_VIEW WHERE INSER_SCRIPT=in_INS_CODE  ;
CURSOR C1 (in_INS_CODE varchar2,v_SYMBOL varchar2) is select SYMBOL,TRADEDATE,CURRENTPRICE ,PRCNT_CHANGE,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,RNK,INSERT_DATE from VOL_VIEW WHERE INSER_SCRIPT=in_INS_CODE and symbol=v_SYMBOL ORDER BY TRADEDATE DESC ;


--CURSOR C2 (in_INS_CODE varchar2,v_SYMBOL varchar2) is select * from PRICE_INTERIM WHERE INS_CODE=in_INS_CODE and symbol=v_SYMBOL ORDER BY TRADEDATE DESC ;

begin
if (TRADEDATE is null)
 then
  select max(tradedate) into v_tradedate1  from nasdaq.nasdaq_hist;
  --select current_load_date into v_tradedate1 from nse.load_date;
  else
   v_TRADEDATE1:=TRADEDATE;
end if;
dbms_output.put_line('Tradedate1 is '|| v_TRADEDATE1);
select tradedate into v_interim_tradedate1 from (select tradedate,ROW_NUMBER()OVER(order by  tradedate desc) RowNo  from (select distinct tradedate from VOL_VIEW order by tradedate)) where rowno=1;
select tradedate into v_interim_tradedate2 from (select tradedate,ROW_NUMBER()OVER(order by  tradedate desc) RowNo  from (select distinct tradedate from VOL_VIEW order by tradedate)) where rowno=2;
select tradedate into v_interim_tradedate3 from (select tradedate,ROW_NUMBER()OVER(order by  tradedate desc) RowNo  from (select distinct tradedate from VOL_VIEW order by tradedate)) where rowno=3;

for v_INS_CODE in my_list.first .. my_list.last loop
DBMS_OUTPUT.PUT_LINE('insert code   is   '||v_INS_CODE);
in_INS_CODE:=my_list(v_INS_CODE);
open C0(in_INS_CODE);
        LOOP
        FETCH C0 into v_SYMBOL;
        DBMS_OUTPUT.PUT_LINE('symbol is   '||v_SYMBOL||'-'||in_INS_CODE);
        EXIT WHEN C0%NOTFOUND;
select count(*) into v_count from VOL_VIEW WHERE INSER_SCRIPT=in_INS_CODE and symbol=v_SYMBOL;
        select max(tradedate) into max_tradedate from VOL_VIEW WHERE INSER_SCRIPT=in_INS_CODE and symbol=v_SYMBOL;
        if (v_count=3 and max_tradedate=v_interim_tradedate1 )then
v_Insert_cnt:=0;
v_DAY_WISE_GRTH:='';
v_DAY_VOL_PRCNT:='';
v_TOT_PRICE_PRCNT:=0;
v_curr_table:=nasdaq_vol_tab(in_symbol=>v_SYMBOL,in_INS_CODE=>in_INS_CODE);
if (v_curr_table<>'dummy') then
v_TCH_CNT:=tch_vol_cnt(in_symbol=>v_SYMBOL,in_curr_tab=>v_curr_table);
            open C1(in_INS_CODE,v_SYMBOL) ;
            LOOP
            FETCH C1 into v_SYMBOL,v_TRADEDATE,v_CURRENTPRICE,v_PRCNT_CHANGE,v_FFVOLDIFFPRCNT,v_TOTDIFFVOLPRCNT,v_RNK,v_INSERT_DATE;
            EXIT WHEN C1%NOTFOUND;
            if (v_Insert_cnt<1) then
v_insert_CURRENTPRICE:=v_CURRENTPRICE;
v_Insert_cnt:=v_Insert_cnt+1;
end if;
v_DAY_WISE_GRTH:=concat(v_DAY_WISE_GRTH,concat('+',round(v_PRCNT_CHANGE,1)));
v_DAY_VOL_PRCNT:=concat(v_DAY_VOL_PRCNT,concat('+',round(v_FFVOLDIFFPRCNT,1)));
v_TOT_PRICE_PRCNT:=v_TOT_PRICE_PRCNT+v_PRCNT_CHANGE;
            end loop;
DBMS_OUTPUT.PUT_LINE('insert symbol is : '||v_SYMBOL);
DBMS_OUTPUT.PUT_LINE('growth is : '||v_DAY_WISE_GRTH);
DBMS_OUTPUT.PUT_LINE('insert symbol is : '||v_SYMBOL||'--INS DATE :'||v_INSERT_DATE||'--INS SCRIPT IS :'||in_INS_CODE2);
tempstmt:='insert into '||v_curr_table||' (SYMBOL,INSERT_DATE,INSERT_SCRIPT,INS_RNK,CURRENTPRICE,DAY_WISE_GRTH,DAY_VOL_PRCNT,TOTDIFFVOLPRCNT,TOT_PRICE_PRCNT,TCH_CNT) values (:v_SYMBOL,:INSERT_DATE,:INSERT_SCRIPT,:INS_RNK,:CURRENTPRICE,:DAY_WISE_GRTH,:DAY_VOL_PRCNT,:TOTDIFFVOLPRCNT,:TOT_PRICE_PRCNT,:TCH_CNT)';
--DBMS_OUTPUT.PUT_LINE('insert state: '||tempstmt);
EXECUTE IMMEDIATE tempstmt using v_SYMBOL,v_INSERT_DATE,in_INS_CODE,v_RNK,v_CURRENTPRICE,v_DAY_WISE_GRTH,v_DAY_VOL_PRCNT,v_TOTDIFFVOLPRCNT,v_TOT_PRICE_PRCNT,v_TCH_CNT;
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
end loop;



end;