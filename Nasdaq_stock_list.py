import sys
import os
import selenium
import re
import xlrd
from selenium import webdriver
import pandas
import csv
import xlsx2csv
import time
import glob
import shutil
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
os.environ['ORACLE_HOME'] ="C:\\app\User\product\\11.2.0\client_1"
import cx_Oracle
import os
connection = cx_Oracle.connect("nasdaq", "nasdaq123", "localhost/orcl")
cursor = connection.cursor()
def insert_db(values):
        try:
                insert_stmt="insert into nasdaq_stock_list (SYMBOL,NAME,LASTSALE,MARKETCAP,IPOYEAR,SECTOR,INDUSTRY,URL) values (:vSYMBOL,:vNAME,:vLASTSALE,:vMARKETCAP,:vIPOYEAR,:vSECTOR,:vINDUSTRY,:vURL)"
                cursor.execute(insert_stmt,vSYMBOL=values[0],vNAME=values[1],vLASTSALE=values[2],vMARKETCAP=values[3],vIPOYEAR=values[4],vSECTOR=values[5],vINDUSTRY=values[6],vURL=values[7])
                connection.commit()
        except cx_Oracle.IntegrityError:
                print values[0]+' '+values[1]+' row already present'
def csv_read(file):
        lis=[]
        csv1 = file
        with open(csv1) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                    print row[0]
                    if row[0]!='Symbol':
                            insert_db(row)
                csvfile.close()
#                time.sleep(3)
### clear download directory ###
#for file in (glob.glob("C:\Users\User\Downloads\\companylist*.csv")):
#        flname=file.split("ds\\")[1]
#        shutil.move(file,"C:\\Users\\User\\Downloads\\stock_funda_temp\\"+flname)
#symbol_input_lis=[]
##cursor.execute('select NSECODE from NSESTOCK where NSECODE NOT IN (SELECT NSECODE FROM NSESTOCK_INDX union SELECT NSECODE FROM funda_download_status where status=1) and rownum<50 order by nsecode')
##cursor.execute('select distinct symbol as nsecode from nsehist_nf where tradedate=:vDATE and symbol NOT IN (SELECT NSECODE FROM NSESTOCK_INDX union SELECT NSECODE FROM funda_download_status where status in (1)) and rownum<350 order by nsecode',vDATE='24-NOV-17')
##cursor.execute('select NSECODE from NSESTOCK where NSECODE=:code',code='ANDHRABANK')
list_of_files = glob.glob("C:\Users\User\Downloads\\companylist*.csv")
#latest_file = max(list_of_files, key=os.path.getctime)
#print list_of_files
print len(list_of_files)
for i in range(0, len(list_of_files)):
    print list_of_files[i]
    print i
    csv_read(list_of_files[i])
