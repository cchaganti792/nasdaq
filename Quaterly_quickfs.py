import sys
import Page
from Page import browser
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import os
import locale
import time
#os.environ['ORACLE_HOME'] ="C:\\app\User\product\\11.2.0\client_1"
import cx_Oracle
connection = cx_Oracle.connect("nasdaq", "nasdaq123", "localhost/orcl")
cursor = connection.cursor()
#Page.open('file:///C:/Users/User/Desktop/test.html')
def num(i):
    import locale
    locale.setlocale( locale.LC_ALL, 'english_USA' )
    if '.' in i :
        b=locale.atof(i)
    elif ',' in i :
        b=locale.atoi(i)
    elif i=='-' :
        b=0
    else :
        b=i
    return b
def download(symbol):
    global vERROR_MSG
    global ercode
    ercode=0
    vERROR_MSG='Good'
    try:
        Page.open('https://quickfs.net/company/'+symbol+'')
        browser.find_element_by_xpath("/html/body/app-root/app-company/div/div/div[2]/div/company-overview/div[2]/div[2]/div/company-financial-table/div/select-period-dropdown/div/button").click()
#browser.find_element_by_xpath("/html/body/app-root/app-company/div/div/div[2]/div/company-overview/div[2]/div[2]/div/company-financial-table/div/select-period-dropdown/div/button").send_keys("Quarterl")
        browser.find_element_by_xpath('//*[@id="Quarterly"]').click()
        time.sleep(10)
        tab_data = browser.find_element_by_xpath('/html/body/app-root/app-company/div/div/div[2]/div/company-overview/div[2]/div[2]/div/company-financial-table/div/div/table').find_elements_by_tag_name('tr')
        list_rows = []
        for items in tab_data:
                list_cells = []
                for item in items.find_elements_by_tag_name('td'):
                        list_cells.append(item.text.strip('%').strip('$'))
                print list_cells
                list_rows.append(list_cells)
        print len(list_rows)
        GIP=zip(*list_rows)
        del GIP[0]
        print GIP
        for data in GIP:
            print data
            insert_quickfs_quaterly(symbol,data)
    except NoSuchElementException:
        print 'symbol not present in screener'
        vERROR_MSG='symbol not present in screener'
        print vERROR_MSG
        ercode=2
    except ValueError as e:
        print e
        vERROR_MSG=('%s  Down') %(e)
        print vERROR_MSG
        ercode=2
def insert_quickfs_quaterly(symbol,values):
    try:
        print symbol
        print values
        insert_stmt="insert into quickfs_quaterly (SYMBOL,REPORT_QUATER,REVENUE,REVENUE_GROWTH_PRCNT,GROSS_PROFIT,GROSS_MARGIN_PRCNT,OPER_PROFIT,OPER_MARGIN_PRCNT,EPS,EPS_GROWTH_PRCNT,ROA,ROE,ROIC) values (:vSYMBOL,to_date(:vREPORT_QUATER,'mon-yyyy'),to_number(:vREVENUE),to_number(:vREVENUE_GROWTH_PRCNT),to_number(:vGROSS_PROFIT),to_number(:vGROSS_MARGIN_PRCNT),to_number(:vOPER_PROFIT),to_number(:vOPER_MARGIN_PRCNT),to_number(:vEPS),to_number(:vEPS_GROWTH_PRCNT),to_number(:vROA),to_number(:vROE),to_number(:vROIC))"
        cursor.execute(insert_stmt,vSYMBOL=symbol,vREPORT_QUATER=values[0],vREVENUE=num(values[1]),vREVENUE_GROWTH_PRCNT=num(values[2]),vGROSS_PROFIT=num(values[3]),vGROSS_MARGIN_PRCNT=num(values[4]),vOPER_PROFIT=num(values[5]),vOPER_MARGIN_PRCNT=num(values[6]),vEPS=num(values[7]),vEPS_GROWTH_PRCNT=num(values[8]),vROA=num(values[9]),vROE=num(values[10]),vROIC=num(values[11]))
        connection.commit()
    except cx_Oracle.IntegrityError:
        print 'quickfs_quaterly row already present'
    except IndexError as e:
        print e
        vERROR_MSG=('%s  Down') %(e)
        print vERROR_MSG
        ercode=2      
symbol_input_lis=[]
global vERROR_MSG
global ercode
vERROR_MSG='Good'
ercode=0
cursor.execute('select DISTINCT STOCKCODE  from US_STOCK_funda_download_status where (STATUS=5 or STATUS is null) and rownum<250 ')
for row in cursor:
    symbol_input_lis.append(row[0])
print symbol_input_lis
##symbol_input_lis='GMLPP'
for i in symbol_input_lis:
    print '#################### New symbol %s ########################' %i
    download(i)
    print 'INSERT %s .' %ercode
    err=' %s' %vERROR_MSG
    print err
    cursor.execute('merge into US_STOCK_funda_download_status using dual on (STOCKCODE=:vSYMBOL) WHEN MATCHED THEN UPDATE SET status=:vSTATUS,ERROR_MSG=:vvERROR_MSG  WHEN NOT MATCHED THEN INSERT (STOCKCODE,stream,status,ERROR_MSG) values (:vSYMBOL,:vSTREAM,:vSTATUS,:vvERROR_MSG)',vSYMBOL=i,vSTREAM='NAS',vSTATUS=ercode,vvERROR_MSG=err)
    connection.commit()




