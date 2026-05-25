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
import locale
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
##os.environ['ORACLE_HOME'] ="C:\\app\User\product\\11.2.0\client_1"
import cx_Oracle
import os
print ('****** starting split script ********* ')
connection = cx_Oracle.connect("nasdaq", "nasdaq123", "localhost/orcl")
cursor = connection.cursor()
browser = webdriver.Firefox()
time.sleep(5)
global vERROR_MSG
global ercode
def download(DDATE):
        global vERROR_MSG
        global ercode
        ercode=0
        vERROR_MSG='Good'
        try:
                a='https://eresearch.fidelity.com/eresearch/conferenceCalls.jhtml?tab=splits&begindate='+DDATE+''
                print (a)
                browser.get(a)
                ##element = browser.find_element_by_link_text("Export")
                element = browser.find_element_by_id("messageTable4").find_elements_by_tag_name('tr')
                ##print element
                ##element.click()
                time.sleep(5)
                list_rows = []
                for items in element:
                    list_cells = []
                    for item in items.find_elements_by_tag_name('td'):
                        list_cells.append(item.text.strip('%').strip('$'))
                    print (list_cells)
                    if len(list_cells)==0 :
                            print ('zero length')
                    else :
                            insert_split_data(DDATE,list_cells)
                    list_rows.append(list_cells)
                #print len(list_rows)
                ##insert_split_data(list_rows)
        except NoSuchElementException:
                print ('symbol not present in screener')
                vERROR_MSG='symbol not present in screener'
                print (vERROR_MSG)
                ercode=3
        except ValueError as e:
                print (e)
                vERROR_MSG=('%s  Down') %(e)
                print (vERROR_MSG)
                ercode=3
def insert_split_data(DDATE,values):
    try:
        print (values)
        insert_stmt="insert into split_stock_download_content (SYMBOL,SPLIT_RATIO,ANNOUNCEMENT_DATE,RECORD_DATE,EX_DATE,DOWNLOAD_MON) values (:vSYMBOL,:vSPLIT_RATIO,to_date(:vANNOUNCEMENT_DATE,'mm-dd-yy'),to_date(:vRECORD_DATE,'mm-dd-yy'),to_date(:vEX_DATE,'mm-dd-yy'),to_date(:vDOWNLOAD_MON,'mm-dd-yy'))"
        cursor.execute(insert_stmt,vSYMBOL=values[0],vSPLIT_RATIO=values[1],vANNOUNCEMENT_DATE=(values[2]),vRECORD_DATE=(values[3]),vEX_DATE=(values[4]),vDOWNLOAD_MON=DDATE)
        connection.commit()
        cursor.execute('Update nasdaq.SPLIT_STOCK_DOWNLOAD_STATUS set DSTATE=:vSTATE where DOWNLOAD_MON=:vDDATE',vDDATE=i,vSTATE='Y')
        connection.commit()
    except cx_Oracle.IntegrityError:
        print ('split_stock_download_content row already present')
        cursor.execute('Update nasdaq.SPLIT_STOCK_DOWNLOAD_STATUS set DSTATE=:vERR where DOWNLOAD_MON=:vDDATE',vDDATE=i,vERR='err1')
        connection.commit()
    except IndexError as e:
        print (e)
        vERROR_MSG=('%s  Down') %(e)
        print (vERROR_MSG)
        cursor.execute('Update nasdaq.SPLIT_STOCK_DOWNLOAD_STATUS set DSTATE=:vERR where DOWNLOAD_MON=:vDDATE',vDDATE=i,vERR='err2')
        connection.commit()
        ercode=2
split_mon_input_lis=[]
cursor.execute("select DOWNLOAD_MON from nasdaq.SPLIT_STOCK_DOWNLOAD_STATUS where DSTATE=:vSTATE ",vSTATE='N')
for row in cursor:
    split_mon_input_lis.append(row[0])
print (split_mon_input_lis)
##symbol_input_lis='GMLPP'
for i in split_mon_input_lis:
    print ('#################### Openning page for month  %s ########################' %i)
    download(i)
    print ('INSERT %s .' %ercode)
    err=' %s' %vERROR_MSG
    print (err)
##    cursor.execute('Update nasdaq.SPLIT_STOCK_DOWNLOAD_STATUS set DSTATE=:vERR where DOWNLOAD_MON=:vDDATE',vDDATE=i,vERR='err')
##    connection.commit()
##print 'opening page'
##download('12/1/2020')
