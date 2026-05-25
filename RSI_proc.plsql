create or replace procedure            RSI_proc  is
  vsymbol varchar2(30);
  vgain   number;
  vloss   number;
  vdate   date;
  vcount  number;
  vrsiu   number;
  vrsid   number;
  v_avgu  number;
  v_avgd  number;
  v_avgd_adj number;
  v_rs    number;
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
DBMS_OUTPUT.put_line ('symbol IS =' || vsymbol );
select count(*) into vcount from(select RSI_AVGU,RSI_AVGD from nasdaq_avg where  symbol=vsymbol and  tradedate<vdate order by tradedate desc) where rownum<2;
if (vcount=0)
then
DBMS_OUTPUT.put_line ('Symbol not found  =' || vsymbol );
else
select count(*) into vcount from (select * from (select RSI_AVGU,RSI_AVGD from nasdaq_avg where  symbol=vsymbol and  tradedate<vdate order by tradedate desc) where rownum<2) where RSI_AVGU is not null and RSI_AVGD is not null;
if (vcount=0)
then
DBMS_OUTPUT.put_line ('first loop but Symbol present, values null  =' || vsymbol );
select round(sum(gain)/14,2),round(sum(loss)/14,2) into vgain,vloss  from (select decode(sign(CURRENTPRICE-PRIVCLOSE),1,CURRENTPRICE-PRIVCLOSE,0) as gain,decode(sign(CURRENTPRICE-PRIVCLOSE),-1,-(CURRENTPRICE-PRIVCLOSE),0) as loss from nasdaq_avg where symbol=vsymbol and  tradedate<vdate order by tradedate desc) where rownum<15;
DBMS_OUTPUT.put_line ('vgain-vlos for symbol  =' || vsymbol||' gain is '||vgain||' loss is '||vloss );
update nasdaq_avg set RSI_AVGU=vgain,RSI_AVGD=vloss where symbol=vsymbol and tradedate=vdate-1 ;
commit;
select RSI_AVGU,RSI_AVGD into vrsiu,vrsid from (select RSI_AVGU,RSI_AVGD from nasdaq_avg where  symbol=vsymbol and  tradedate<vdate order by tradedate desc) where rownum<2;
DBMS_OUTPUT.put_line ('vrsiu-vrisd for symbol  =' || vsymbol||' vrsiu is '||vrsiu||' vrsid is '||vrsid );
select round((decode(sign(CURRENTPRICE-PRIVCLOSE),1,CURRENTPRICE-PRIVCLOSE,0)+13*vrsiu)/14,5) ,round((decode(sign(CURRENTPRICE-PRIVCLOSE),-1,-(CURRENTPRICE-PRIVCLOSE),0)+13*vrsid)/14,5)  into v_avgu,v_avgd  from nasdaq_avg where symbol=vsymbol AND TRADEDATE=vdate;
select decode(v_avgd,0,1,v_avgd) into v_avgd_adj from dual;
v_rs:=v_avgu/v_avgd_adj;
update nasdaq_avg set RSI_AVGU=v_avgu,RSI_AVGD=v_avgd,RSI=round((100-(100/(1+v_rs))),2) where symbol=vsymbol and tradedate=vdate ;
DBMS_OUTPUT.put_line ('second then Symbol present   =' || vrsiu );
commit;
else
select RSI_AVGU,RSI_AVGD into vrsiu,vrsid from (select RSI_AVGU,RSI_AVGD from nasdaq_avg where  symbol=vsymbol and  tradedate<vdate order by tradedate desc) where rownum<2;
--DBMS_OUTPUT.put_line ('vrsiu and vrsid values null  =' || vrsiu||'--'||vrsid );
select round((decode(sign(CURRENTPRICE-PRIVCLOSE),1,CURRENTPRICE-PRIVCLOSE,0)+13*vrsiu)/14,5) ,round((decode(sign(CURRENTPRICE-PRIVCLOSE),-1,-(CURRENTPRICE-PRIVCLOSE),0)+13*vrsid)/14,5) into v_avgu,v_avgd  from nasdaq_avg where symbol=vsymbol AND TRADEDATE=vdate;
DBMS_OUTPUT.put_line ('vavgu and vavgd values null  =' || v_avgu||'--'||v_avgd );
select decode(v_avgd,0,0.1,v_avgd) into v_avgd_adj from dual;
DBMS_OUTPUT.put_line ('vavg_down_adjysted is   =' || v_avgd_adj );
v_rs:=v_avgu/v_avgd_adj;
update nasdaq_avg set RSI_AVGU=v_avgu,RSI_AVGD=v_avgd,RSI=round((100-(100/(1+v_rs))),2) where symbol=vsymbol and tradedate=vdate ;
DBMS_OUTPUT.put_line ('v_rs is  present   =' || v_rs );
commit;
end if;
end if;
END LOOP;
close symbol_cur;
  END LOOP;
  close date_cur;
END;