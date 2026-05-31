create or replace procedure   Buy_proc  is
  vsymbol varchar2(30);
  v_ins_price number;
  vgain   number;
  vloss   number;
  vdate   date;
  v_cnt    number;
  vcount  number;
  vrsiu   number;
  vrsid   number;
  v_avgu  number;
  v_avgd  number;
  v_avgd_adj number;
  v_rs    number;
  v_funda_points number;
  v_CATEGORY  varchar2(10);
  v_SUBCATEGORY varchar2(10);
  v_price_points number;
  v_CURRENTPRICE number;
  v_TRADEDATE    date;
  v_PRCNT_CHANGE number;
  v_FIVEDAYAVGPRI number;
  v_BU number;
  v_TWENTYAVGPRI number;
  v_BD number;
  v_FIFTYAVGPRI number;
  v_ONEFIFTYAVGPRI number;
  v_CURR_FUNDA_POINTS number;
  v_CURR_PRICE_POINTS number;
  v_TWOHUNAVGPRI number;
  v_CURRENTVOL number;
  v_FIVEDAYVOL number;
  v_TWENTYAVGVOL number;
  v_RSI number;
  v_SREVENUE number;
  v_REVENUE number;
  v_SEPS number;
  v_EPS number;
  v_MN3 number;
  v_MN2 number;
  v_MN1 number;
  v_MX3 number;
  v_MX2 number;
  v_MX1 number;
  v_1min_price number;
  v_2min_price number;
  v_3min_price number;
  v_1max_price number;
  v_2max_price number;
  v_3max_price number;
  v_1min_date date;
  v_2min_date date;
  v_3min_date date;
  v_1max_date date;
  v_2max_date date;
  v_3max_date date;
  --v_FUNDA_POINTS number;
  --v_PRICE_POINTS number;

  CURSOR buy_cur IS select SYMBOL from nasdaq.Buy_log where CATEGORY='R';
  CURSOR New_buy_cur IS select SYMBOL from nasdaq.observer_log where CATEGORY='R' and CURRENTPRICE<1.03*BD and RSI<35;
  CURSOR close_buy_cur IS select SYMBOL from nasdaq.Buy_log where CATEGORY='R';
  BEGIN
  insert into buy_log_log select * from buy_log;
  commit;
  open buy_cur;
  LOOP
  FETCH buy_cur into vsymbol;
  EXIT WHEN buy_cur%NOTFOUND;
  select INS_PRICE into v_ins_price from nasdaq.Buy_log where symbol=vsymbol ;
  select count(*) into v_cnt from nasdaq.observer_log where symbol=vsymbol;
  DBMS_OUTPUT.put_line ('SYMBOL IS =' || vsymbol||'cnt is '||v_cnt);
  if (v_cnt=1) then
select TRADEDATE,CURR_FUNDA_POINTS,CURR_PRICE_POINTS,CURRENTPRICE,PRCNT_CHANGE,FIVEDAYAVGPRI,BU,TWENTYAVGPRI,BD,FIFTYAVGPRI,ONEFIFTYAVGPRI,TWOHUNAVGPRI,CURRENTVOL,FIVEDAYVOL,TWENTYAVGVOL,RSI into v_TRADEDATE,v_CURR_FUNDA_POINTS,v_CURR_PRICE_POINTS,v_CURRENTPRICE,v_PRCNT_CHANGE,v_FIVEDAYAVGPRI,v_BU,v_TWENTYAVGPRI,v_BD,v_FIFTYAVGPRI,v_ONEFIFTYAVGPRI,v_TWOHUNAVGPRI,v_CURRENTVOL,v_FIVEDAYVOL,v_TWENTYAVGVOL,v_RSI from nasdaq.observer_log where symbol=vsymbol ;
update nasdaq.Buy_log set TRADEDATE=v_TRADEDATE,CURR_FUNDA_POINTS=v_CURR_FUNDA_POINTS,CURR_PRICE_POINTS=v_CURR_PRICE_POINTS,CURRENTPRICE=v_CURRENTPRICE,PRCNT_CHANGE=v_PRCNT_CHANGE,PROFIT_LOSS=trunc(((v_CURRENTPRICE-v_ins_price)/v_ins_price)*100,2),FIVEDAYAVGPRI=v_FIVEDAYAVGPRI,BU=v_BU,TWENTYAVGPRI=v_TWENTYAVGPRI,BD=v_BD,FIFTYAVGPRI=v_FIFTYAVGPRI,ONEFIFTYAVGPRI=v_ONEFIFTYAVGPRI,TWOHUNAVGPRI=v_TWOHUNAVGPRI,CURRENTVOL=v_CURRENTVOL,FIVEDAYVOL=v_FIVEDAYVOL,TWENTYAVGVOL=v_TWENTYAVGVOL,RSI=v_RSI,state='CONTINUE' where symbol=vsymbol;
--update nasdaq.buy_log set state='CONTINUE' where symbol=vsymbol and INS_DATE<>(select max(tradedate) from nasdaq_avg) ;
commit;

  else
select count(*) into v_cnt from nasdaq.NASDAQ_AVG where symbol=vsymbol and tradedate=(select max(tradedate) from nasdaq_avg);
if (v_cnt=1) then
select CURRENTPRICE,TRADEDATE,PRCNT_CHANGE,FIVEDAYAVGPRI,BU,TWENTYAVGPRI,BD,FIFTYAVGPRI,ONEFIFTYAVGPRI,TWOHUNAVGPRI,CURRENTVOL,FIVEDAYVOL,TWENTYAVGVOL,RSI into v_CURRENTPRICE,v_TRADEDATE,v_PRCNT_CHANGE,v_FIVEDAYAVGPRI,v_BU,v_TWENTYAVGPRI,v_BD,v_FIFTYAVGPRI,v_ONEFIFTYAVGPRI,v_TWOHUNAVGPRI,v_CURRENTVOL,v_FIVEDAYVOL,v_TWENTYAVGVOL,v_RSI from nasdaq.nasdaq_avg where symbol=vsymbol and tradedate=(select max(tradedate) from nasdaq_avg);
v_funda_points:=Funda_point_fn(symbol=>vsymbol,ins_script=>'R150');
v_price_points:=Price_point_fn(symbol=>vsymbol,ins_script=>'R150-Price');
update nasdaq.Buy_log set TRADEDATE=v_TRADEDATE,CURR_FUNDA_POINTS=v_funda_points,CURR_PRICE_POINTS=v_price_points,CURRENTPRICE=v_CURRENTPRICE,PRCNT_CHANGE=v_PRCNT_CHANGE,PROFIT_LOSS=trunc(((v_CURRENTPRICE-v_ins_price)/v_ins_price)*100,2),FIVEDAYAVGPRI=v_FIVEDAYAVGPRI,BU=v_BU,TWENTYAVGPRI=v_TWENTYAVGPRI,BD=v_BD,FIFTYAVGPRI=v_FIFTYAVGPRI,ONEFIFTYAVGPRI=v_ONEFIFTYAVGPRI,TWOHUNAVGPRI=v_TWOHUNAVGPRI,CURRENTVOL=v_CURRENTVOL,FIVEDAYVOL=v_FIVEDAYVOL,TWENTYAVGVOL=v_TWENTYAVGVOL,RSI=v_RSI,state='CONTINUE' where symbol=vsymbol;
commit;
ELSE
update nasdaq.BUY_log set state='NOTFOUND' where symbol=vsymbol;
        commit;
end if ;
   end if ;
  END LOOP;
  close buy_cur;
  open New_buy_cur;
  LOOP
  FETCH New_buy_cur into vsymbol;
  EXIT WHEN New_buy_cur%NOTFOUND;
  select count(*) into v_cnt from nasdaq.buy_log where symbol=vsymbol;
  if (v_cnt=1) then
  null;
  else
  select CURRENTPRICE,CURR_FUNDA_POINTS,CURR_PRICE_POINTS,CATEGORY,SUBCATEGORY,TRADEDATE,PRCNT_CHANGE,FIVEDAYAVGPRI,BU,TWENTYAVGPRI,BD,FIFTYAVGPRI,ONEFIFTYAVGPRI,TWOHUNAVGPRI,CURRENTVOL,FIVEDAYVOL,TWENTYAVGVOL,RSI,SREVENUE,REVENUE,SEPS,EPS,MN3,MN2,MN1,MX3,MX2,MX1 into v_CURRENTPRICE,v_CURR_FUNDA_POINTS,v_CURR_PRICE_POINTS,v_CATEGORY,v_SUBCATEGORY,v_TRADEDATE,v_PRCNT_CHANGE,v_FIVEDAYAVGPRI,v_BU,v_TWENTYAVGPRI,v_BD,v_FIFTYAVGPRI,v_ONEFIFTYAVGPRI,v_TWOHUNAVGPRI,v_CURRENTVOL,v_FIVEDAYVOL,v_TWENTYAVGVOL,v_RSI,v_SREVENUE,v_REVENUE,v_SEPS,v_EPS,v_MN3,v_MN2,v_MN1,v_MX3,v_MX2,v_MX1 from observer_log where symbol=vsymbol;
  insert into nasdaq.buy_log (SYMBOL,INS_DATE,INS_PRICE,CURRENTPRICE,INS_FUNDA_POINTS,INS_PRICE_POINTS,CURR_FUNDA_POINTS,CURR_PRICE_POINTS,CATEGORY,SUBCATEGORY,TRADEDATE,PRCNT_CHANGE,PROFIT_LOSS,FIVEDAYAVGPRI,BU,TWENTYAVGPRI,BD,FIFTYAVGPRI,ONEFIFTYAVGPRI,TWOHUNAVGPRI,CURRENTVOL,FIVEDAYVOL,TWENTYAVGVOL,RSI,SREVENUE,REVENUE,SEPS,EPS,MN3,MN2,MN1,MX3,MX2,MX1,STATE) values (vsymbol,v_TRADEDATE,v_CURRENTPRICE,v_CURRENTPRICE,v_CURR_FUNDA_POINTS,v_CURR_PRICE_POINTS,v_CURR_FUNDA_POINTS,v_CURR_PRICE_POINTS,v_CATEGORY,v_SUBCATEGORY,v_TRADEDATE,v_PRCNT_CHANGE,0,v_FIVEDAYAVGPRI,v_BU,v_TWENTYAVGPRI,v_BD,v_FIFTYAVGPRI,v_ONEFIFTYAVGPRI,v_TWOHUNAVGPRI,v_CURRENTVOL,v_FIVEDAYVOL,v_TWENTYAVGVOL,v_RSI,v_SREVENUE,v_REVENUE,v_SEPS,v_EPS,v_MN3,v_MN2,v_MN1,v_MX3,v_MX2,v_MX1,'NEW');
  commit;
  end if;
  END LOOP;
  close New_buy_cur;
END;