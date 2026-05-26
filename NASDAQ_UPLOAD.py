import sys
import os
import selenium
import re
from selenium import webdriver
import pandas
import csv
import xlsx2csv
import time
import glob
import shutil
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import cx_Oracle
import os
#os.environ['ORACLE_HOME'] ="D:\app\User\product\11.2.0\dbhome_1\BIN"
import cx_Oracle
import os
connection = cx_Oracle.connect("nasdaq", "nasdaq123", "localhost/orcl")
cursor = connection.cursor()
def insert_db(values):
        try:
                insert_stmt="insert into NASDAQ_HIST (SYMBOL,TRADEDATE,OPEN,HIGH,LOW,CLOSE,VOLUME) values (:vSYMBOL,to_date(:vTRADEDATE,'dd-mon-yy'),to_number(:vOPEN),to_number(:vHIGH),to_number(:vLOW),to_number(:vCLOSE),to_number(:vVOLUME))"
                cursor.execute(insert_stmt,vSYMBOL=values[0],vTRADEDATE=values[1],vOPEN=values[2],vHIGH=values[3],vLOW=values[4],vCLOSE=values[5],vVOLUME=values[6])
                connection.commit()
        except cx_Oracle.IntegrityError:
                print values[0]+' '+values[1]+' row already present'
def csv_read(file):
        lis=[]
        csv1 = file
        with open(csv1) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                    print row
                    insert_db(row)
                csvfile.close()
                time.sleep(5)
                cursor.callproc('SPLIT_PROC',())
                cursor.callproc('nasdaq_avg_proc_daily',())
                cursor.callproc('RSI_proc',())
                cursor.callproc('BOLLINGER_proc',())
                cursor.callproc('nasdaq_postive_proc',())
                cursor.callproc('nasdaq_VOL_proc',())
                cursor.execute('insert into PE select * from P_E')
                cursor.execute('insert into funda select * from fundav')
                cursor.execute('insert into QUICK_LOOK_LOG select * from QUICK_LOOK')
                cursor.execute('insert into nasdaq.Down150_vw select * from  DOWN_150_SELECT_VW')
                cursor.execute('insert into rsi2530_log select * from rsi2030')
                connection.commit()
                print '******************* Executing 150 down Proc sleep **********'
                #time.sleep(150)
                print '******************* Executing 150 down Proc **********'
                cursor.callproc('Analyze_150_proc',())
                print '******************* observer Proc start **********'
                cursor.callproc('observer_proc',())
                print '******************* observer Proc end **********'
                print '******************* But Proc start **********'
                cursor.callproc('Buy_proc',())
                print '******************* Buy Proc end **********'
                connection.commit()
                move_files(file)
def move_files(file):
       print file
       flname=file.split("NASDAQ\\")[1]
       print flname
       shutil.move(file,"C:\\Users\\jenit\\Downloads\\NASDAQ\\Nasdaq_bkp\\"+flname)
#       shutil.move(file,"C:\\Users\\jenit\\Downloads\\NASDAQ\\Nasdaq_bkp\\"+flname)
list_of_files = glob.glob("C:\\Users\\jenit\\Downloads\\NASDAQ\\NASDAQ*.csv")
#latest_file = max(list_of_files, key=os.path.getctime)
#print list_of_files
print len(list_of_files)
for i in range(0, len(list_of_files)):
    print list_of_files[i]
    print i
    csv_read(list_of_files[i])
