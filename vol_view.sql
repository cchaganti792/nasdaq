--------------------------------------------------------
--  File created - Monday-May-25-2026   
--------------------------------------------------------
--------------------------------------------------------
--  DDL for View VOL_VIEW
--------------------------------------------------------

  CREATE OR REPLACE FORCE VIEW "NASDAQ"."VOL_VIEW" ("SYMBOL", "TRADEDATE", "PRIVCLOSE", "OPEN", "CURRENTPRICE", "PRCNT_CHANGE", "FFPRICEDIFF", "CURRENTVOL", "FIFTYAVGVOL", "ONEFIFTYAVGVOL", "FFVOLDIFFPRCNT", "TOTDIFFVOLPRCNT", "RNK", "INSERT_DATE", "INSER_SCRIPT") AS 
  SELECT "SYMBOL","TRADEDATE","PRIVCLOSE","OPEN","CURRENTPRICE","PRCNT_CHANGE","FFPRICEDIFF","CURRENTVOL","FIFTYAVGVOL","ONEFIFTYAVGVOL","FFVOLDIFFPRCNT","TOTDIFFVOLPRCNT","RNK","INSERT_DATE","INSER_SCRIPT" FROM VOL_LOG WHERE INSERT_DATE IN (SELECT MAX(TRADEDATE) FROM NASDAQ_AVG)
