create or replace procedure            BOLLINGER_proc  is
  vsymbol varchar2(30);
  v_stddev   number;
  v_bolinge_median   number;
  vdate   date;
  vcount  number;
  --CURSOR symbol_cur (vdate date)IS select distinct symbol from nasdaq_avg where  tradedate=vdate order by symbol;
  --CURSOR date_cur IS select distinct tradedate from nasdaq_avg where  tradedate>trunc(sysdate)-27  order by tradedate asc ;
  --CURSOR date_cur IS select distinct tradedate from nasdaq_avg where  tradedate=trunc(sysdate)-128 ;
  --CURSOR symbol_cur (vdate date)IS select distinct symbol from nasdaq_avg where symbol in ('AAPL') and   tradedate=vdate ;
  CURSOR date_cur IS select distinct tradedate from nasdaq_avg where  tradedate in (select max(tradedate) from nasdaq_avg)  order by tradedate asc ;
  CURSOR symbol_cur (vdate date)IS select distinct symbol from nasdaq_avg where  tradedate=vdate ;
BEGIN
  open date_cur;
  LOOP
  FETCH date_cur into vdate;
  EXIT WHEN date_cur%NOTFOUND;
  DBMS_OUTPUT.put_line ('DATE IS =' || vdate );
  open symbol_cur(vdate);
LOOP
FETCH symbol_cur into vsymbol;
EXIT WHEN symbol_cur%NOTFOUND;
DBMS_OUTPUT.put_line ('symbol IS =' || vsymbol||'-- date is '||vdate );
v_stddev:=bollinger(in_symbol=>vsymbol,in_TRADEDATE=>vdate);
update nasdaq_avg set SD=v_stddev,BU=(TWENTYAVGPRI+(2*v_stddev)),BD=(TWENTYAVGPRI-(2*v_stddev)) where symbol=vsymbol and tradedate=vdate ;
commit;
END LOOP;
close symbol_cur;
  END LOOP;
  close date_cur;
END;
