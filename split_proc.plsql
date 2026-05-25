create or replace procedure            split_proc (TRADEDATE  IN date default null)  is
  vsymbol varchar2(60);
  v_TRADEDATE1 date;
  v_date date;
  v_first number;
  v_second number;
  vcount number;
  v_pf number;  -- price factor
  v_vf number;  -- volume factor

  --CURSOR date_cur (in_date date) IS select distinct tradedate from nasdaq_hist where  tradedate=in_date  order by tradedate asc ;
  CURSOR date_cur (in_date date) IS select distinct tradedate from nasdaq_hist where  tradedate>=in_date  order by tradedate asc ;
  CURSOR split_cur (v_date date)IS select SYMBOL,TO_NUMBER(SUBSTR(SPLIT_RATIO,1,INSTR(SPLIT_RATIO,':')-1)) AS FIRST_HALF,TO_NUMBER(SUBSTR(SPLIT_RATIO,INSTR(SPLIT_RATIO,':')+1)) AS SEC_HALF from nasdaq.SPLIT_STOCK_DOWNLOAD_content where symbol not like '%:CA' and EX_DATE=v_date and STATE_FLAG='N' ;
BEGIN
if (TRADEDATE is null)
 then
  select max(tradedate) into v_tradedate1  from nasdaq.nasdaq_hist;
  else
   v_TRADEDATE1:=TRADEDATE;
end if;
  open date_cur(v_TRADEDATE1);
LOOP
FETCH date_cur into v_date;
EXIT WHEN date_cur%NOTFOUND;
DBMS_OUTPUT.put_line ('DATE IS =' || v_date );
open split_cur(v_date);
LOOP
FETCH split_cur into vsymbol,v_first,v_second;
EXIT WHEN split_cur%NOTFOUND;
DBMS_OUTPUT.put_line ('symbol IS =' || vsymbol||' first: '||v_first||' second : '|| v_second);
v_pf:=(v_second/v_first);
v_vf:=(v_first/v_second);
select count(*) into vcount from nasdaq_hist where  symbol=vsymbol and  tradedate<v_date ;
if (vcount=0)
then
DBMS_OUTPUT.put_line ('Symbol not found  in nasdaq_hist=' || vsymbol );
update nasdaq.SPLIT_STOCK_DOWNLOAD_content set STATE_FLAG='NYSE',SPLIT_APPLY_DATE=sysdate,used_split_first=v_first,used_split_second=v_second where SYMBOL=vsymbol and EX_DATE=v_date;
commit;
else
update nasdaq_hist set open=open*v_pf,HIGH=HIGH*v_pf,LOW=LOW*v_pf,CLOSE=CLOSE*v_pf,VOLUME=VOLUME*v_vf  where TRADEDATE<v_date and symbol=vsymbol;
update nasdaq_avg set PRIVCLOSE=PRIVCLOSE*v_pf,OPEN=OPEN*v_pf,CURRENTPRICE=CURRENTPRICE*v_pf,FIVEDAYAVGPRI=FIVEDAYAVGPRI*v_pf,TWENTYAVGPRI=TWENTYAVGPRI*v_pf,FIFTYAVGPRI=FIFTYAVGPRI*v_pf,ONEFIFTYAVGPRI=ONEFIFTYAVGPRI*v_pf,CURRENTVOL=CURRENTVOL*v_vf,FIVEDAYVOL=FIVEDAYVOL*v_vf,TWENTYAVGVOL=TWENTYAVGVOL*v_vf,FIFTYAVGVOL=FIFTYAVGVOL*v_vf,ONEFIFTYAVGVOL=ONEFIFTYAVGVOL*v_vf where symbol=vsymbol and TRADEDATE<v_date;
update nasdaq.SPLIT_STOCK_DOWNLOAD_content set STATE_FLAG='Y',SPLIT_APPLY_DATE=sysdate,used_split_first=v_first,used_split_second=v_second where SYMBOL=vsymbol and EX_DATE=v_date;
commit;
end if;
END LOOP;
close split_cur;
END LOOP;
close date_cur;
END;