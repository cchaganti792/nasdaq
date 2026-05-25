create or replace procedure     nasdaq_avg_proc_daily (TRADEDATE  IN date default null)
is
in_symbol  varchar2(20);
v_symbol varchar2(60);
v_PRIVCLOSE number;
v_CURRENTPRICE number;
v_OPENPRICE number;
v_CURRENTVOL NUMBER;
v_FIVEDAYAVGPRI number;
v_TWENTYAVGPRI number;
v_FIFTYAVGPRI  number;
v_ONEFIFTYAVGPRI number;
v_TWOHUNAVGPRI number;
v_FIVEDAYVOL number;
v_TWENTYAVGVOL number;
v_FIFTYAVGVOL  number;
v_ONEFIFTYAVGVOL number;
v_tradedate1 date;
v_tradedate  date;
v_level number;
v_count number;
v_rnk   number;

 cursor C0 (v_TRADEDATE1 date) is select distinct symbol from nasdaq.nasdaq_hist where  length(symbol)<5 and tradedate=v_TRADEDATE1  order by 1;


CURSOR C2 (v_TRADEDATE1 date,in_symbol varchar2) is select symbol,open,close,VOLUME from nasdaq.nasdaq_hist where tradedate=v_TRADEDATE1 and symbol=in_symbol ;

begin
if (TRADEDATE is null)
 then
  select max(tradedate) into v_tradedate1  from nasdaq.nasdaq_hist;
  --select current_load_date into v_tradedate1 from nse.load_date;
  else
   v_TRADEDATE1:=TRADEDATE;
end if;

select count(*) into v_count from nasdaq.nasdaq_avg where tradedate=v_tradedate1;
if (v_count=0) then
        open C0(v_tradedate1);
        LOOP
        FETCH C0 into in_symbol;
        EXIT WHEN C0%NOTFOUND;
DBMS_OUTPUT.PUT_LINE('symbol is   '||in_symbol);
v_PRIVCLOSE:=nas_privclose(in_symbol=>in_symbol,in_tradedate=>v_tradedate1);
        v_FIVEDAYAVGPRI:=nasavg(in_avgnum=>5,in_symbol=>in_symbol,in_tradedate=>v_tradedate1,in_parm=>'close');
        v_TWENTYAVGPRI:=nasavg(in_avgnum=>20,in_symbol=>in_symbol,in_tradedate=>v_tradedate1,in_parm=>'close');
        v_FIFTYAVGPRI:=nasavg(in_avgnum=>50,in_symbol=>in_symbol,in_tradedate=>v_tradedate1,in_parm=>'close');
        v_ONEFIFTYAVGPRI:=nasavg(in_avgnum=>150,in_symbol=>in_symbol,in_tradedate=>v_tradedate1,in_parm=>'close');
        v_TWOHUNAVGPRI:=nasavg(in_avgnum=>200,in_symbol=>in_symbol,in_tradedate=>v_tradedate1,in_parm=>'close');
        v_FIVEDAYVOL:=nasavg(in_avgnum=>5,in_symbol=>in_symbol,in_tradedate=>v_tradedate1,in_parm=>'VOLUME');
        v_TWENTYAVGVOL:=nasavg(in_avgnum=>20,in_symbol=>in_symbol,in_tradedate=>v_tradedate1,in_parm=>'VOLUME');
        v_FIFTYAVGVOL:=nasavg(in_avgnum=>50,in_symbol=>in_symbol,in_tradedate=>v_tradedate1,in_parm=>'VOLUME');
        v_ONEFIFTYAVGVOL:=nasavg(in_avgnum=>150,in_symbol=>in_symbol,in_tradedate=>v_tradedate1,in_parm=>'VOLUME');
DBMS_OUTPUT.PUT_LINE('symbol is   '||in_symbol||' '||v_PRIVCLOSE);
        OPEN C2 (v_tradedate1,in_symbol);
            LOOP
            FETCH C2 INTO v_symbol,v_OPENPRICE,v_CURRENTPRICE,v_CURRENTVOL;
            EXIT WHEN C2%NOTFOUND;
            insert into nasdaq.nasdaq_avg (SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FIVEDAYAVGPRI,TWENTYAVGPRI,FIFTYAVGPRI,ONEFIFTYAVGPRI,TWOHUNAVGPRI,CURRENTVOL,FIVEDAYVOL,TWENTYAVGVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL) values (v_symbol,v_tradedate1,v_PRIVCLOSE,v_OPENPRICE,v_CURRENTPRICE,TRUNC(((v_CURRENTPRICE-v_PRIVCLOSE)/v_PRIVCLOSE)*100,2),v_FIVEDAYAVGPRI,v_TWENTYAVGPRI,v_FIFTYAVGPRI,v_ONEFIFTYAVGPRI,v_TWOHUNAVGPRI,v_CURRENTVOL/100000,v_FIVEDAYVOL/100000,v_TWENTYAVGVOL/100000,v_FIFTYAVGVOL/100000,v_ONEFIFTYAVGVOL/100000);
            END LOOP;
            commit;
        close C2;
        END LOOP;
        close C0;
        insert into vol_toppers_hist select * from vol_toppers;
        commit;
        ----Capturing price based  data into log tables ---
        insert into pri_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri_01' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri_01) where rnk<20;
        insert into pri_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri_15' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri_15) where rnk<20;
        insert into pri_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri_516' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri_516) where rnk<20;
        insert into pri_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri_1625' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri_1625) where rnk<20;
        insert into pri_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri_2575' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri_2575) where rnk<20;
        insert into pri_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri_75' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri_75) where rnk<20;
        insert into pri2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri2_01' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri2_01) where rnk<20;
        insert into pri2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri2_15' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri2_15) where rnk<20;
        insert into pri2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri2_516' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri2_516) where rnk<20;
        insert into pri2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri2_1625' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri2_1625) where rnk<20;
        insert into pri2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri2_2575' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri2_2575) where rnk<20;
        insert into pri2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_pri2_75' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,TOTPRICEPRCNT,FFVOLDIFFPRCNT,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,dense_rank() over ( order by  TOTPRICEPRCNT desc) as RNK from nasbull_pri2_75) where rnk<20;
        commit;
        ----- Pulling only part/eligible delivery data into events table ----
        insert into vol_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol_01' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol_01) where rnk<25;
        insert into vol_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol_15' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol_15) where rnk<25;
        insert into vol_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol_516' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol_516) where rnk<25;
        insert into vol_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol_1625' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol_1625) where rnk<25;
        insert into vol_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol_2575' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol_2575) where rnk<25;
        insert into vol_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol_75' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol_75) where rnk<25;
        
        insert into vol2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol2_01' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol2_01) where rnk<20;
        insert into vol2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol2_15' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol2_15) where rnk<20;
        insert into vol2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol2_516' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol2_516) where rnk<20;
        insert into vol2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol2_1625' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol2_1625) where rnk<20;
        insert into vol2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol2_2575' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol2_2575) where rnk<20;
        insert into vol2_log select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,rnk,(select max(tradedate) from nasdaq_hist) as Insert_date,'nasbull_vol2_75' as Inser_script from (select SYMBOL,TRADEDATE,PRIVCLOSE,OPEN,CURRENTPRICE,PRCNT_CHANGE,FFPRICEDIFF,CURRENTVOL,FIFTYAVGVOL,ONEFIFTYAVGVOL,FFVOLDIFFPRCNT,TOTDIFFVOLPRCNT,dense_rank() over ( order by  TOTDIFFVOLPRCNT desc) as RNK from nasbull_vol2_75) where rnk<20;
        commit;
        delete  from pri_log  where Insert_date<sysdate-720;
        delete  from vol_log  where Insert_date<sysdate-720;
        delete  from pri2_log  where Insert_date<sysdate-720;
        delete  from vol2_log  where Insert_date<sysdate-720;
        commit;


else
        null;
end if;
end;