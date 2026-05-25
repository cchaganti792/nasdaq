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
import codecs
os.environ['ORACLE_HOME'] ="C:\\app\User\product\\11.2.0\client_1"
import cx_Oracle
connection = cx_Oracle.connect("nasdaq", "nasdaq123", "localhost/orcl")
cursor = connection.cursor()
def num(i):
	import locale
	locale.setlocale( locale.LC_ALL, 'english_USA' )
	if '.' in i :
		b=locale.atof(i)
	elif ',' in i :
		b=locale.atoi(i)
	else :
		b=i
	return b
def download(symbol):
    global vERROR_MSG
    global ercode
    vERROR_MSG='Good'
    ercode=9 ### this used to be 0 but made 9 so that it does not download part of earnings report 
    try:
        Page.open('https://www.zacks.com/stock/research/'+symbol+'/earnings-announcements')
        time.sleep(2)
        tab_data = browser.find_element_by_xpath('/html[1]/body[1]/div[3]/div[3]/div[5]/section[1]/div[1]/div[1]/div[3]/div[2]/div[2]/table[1]/tbody[1]').find_elements_by_tag_name('tr')
        #print tab_data
        earnings_table = []
        for items in tab_data:
            list_cells = []
            for item in items.find_elements_by_tag_name('td'):
                list_cells.append(item.text.strip('%').strip('$').strip('--').strip(','))
            #    print list_cells
            earnings_table.append(list_cells)
        print len(earnings_table)
        print earnings_table
        filename=''
        DOW_STATUS=8
        for i in earnings_table:
                try:
                        insert_stmt="insert into PAST_EARNINGS (SYMBOL,EARNINGS_DATE,PERIOD_ENDING,ESTIMATE_EPS,REPORTED_EPS,SURPRISE,PERCNT_SURPRISE,TIME,FILE_NAME,SOURCE,STATUS) values (:vSYMBOL,to_date(:vEARNINGS_DATE,'mm/dd/yy'),to_date(:vPERIOD_ENDING,'mm/yy'),to_number(:vESTIMATE_EPS),to_number(:vREPORTED_EPS),to_number(:vSURPRISE),to_number(:vPERCNT_SURPRISE),:vTIME,:vFILE_NAME,:vSOURCE,:vSTATUS)"
                        cursor.execute(insert_stmt,vSYMBOL=symbol,vEARNINGS_DATE=i[0],vPERIOD_ENDING=i[1],vESTIMATE_EPS=i[2].replace('$',''),vREPORTED_EPS=i[3].replace('$',''),vSURPRISE=i[4],vPERCNT_SURPRISE=num(i[5]),vTIME=i[6],vFILE_NAME=filename,vSOURCE='SEEK',vSTATUS=DOW_STATUS)
                        connection.commit()
                        #       cursor.execute('insert into PAST_EARNINGS (SYMBOL,EARNINGS_DATE,PERIOD_ENDING,ESTIMATE_EPS,REPORTED_EPS,SURPRISE,PERCNT_SURPRISE,TIME,FILE_NAME,SOURCE,STATUS) values (:vSYMBOL,:vSTATUS,:vvERROR_MSG)',vSYMBOL=i,vSTATUS=ercode,vvERROR_MSG=err)
                except cx_Oracle.IntegrityError:
                        print 'Row already exsists in PAST_EARNINGS'
    except NoSuchElementException:
        print 'symbol not present in screener'
        vERROR_MSG='symbol not present in screener'
        print vERROR_MSG
        ercode=2
    except IndexError:
        print 'symbol  present BUT error in screener'
        vERROR_MSG='symbol  present but error in screener'
        print vERROR_MSG
        ercode=2
    except ValueError as e:
        print e
        vERROR_MSG=('%s  Down') %(e)
        print vERROR_MSG
        ercode=2
    #### check folder exsists or if not create it ##
    if ercode==0:
        ##### earnings call ###
        Page.open('https://www.zacks.com/stock/research/'+symbol+'/earnings-announcements?tab=transcript')
        time.sleep(2)
        links = browser.find_elements_by_partial_link_text("Open")
        link_data=[]
        i=0
        try:
            for link in links:
                earnings_table[i].append(link.get_attribute("href"))
                i=i+1
            filepath= r'C:\\FS\\JEN_DAT\\UPLOADS\\Earnings\\'+symbol
            if not os.path.exists(filepath):
                    os.makedirs(filepath)
            for i in earnings_table:
                print i
                quat=i[1].replace('/','_')
                filename=symbol+'_'+quat+'.txt'
                try:
                    Page.open(i[7]+'?part=single')
                    time.sleep(2)
                    element=browser.find_element_by_id("a-body")
                    completeName = os.path.join(filepath,filename)
                    file_object = codecs.open(completeName, "w", "utf-8")
                    file_object.write(element.text)
                    file_object.close
                    DOW_STATUS=1
                except IndexError:
                    print 'PAGE OPEN ERROR for Quater'
                    DOW_STATUS=9
                except NoSuchElementException:
                    print 'PAGE OPEN ERROR for quater'
                    DOW_STATUS=11
                try:
                    insert_stmt="insert into PAST_EARNINGS (SYMBOL,EARNINGS_DATE,PERIOD_ENDING,ESTIMATE_EPS,REPORTED_EPS,SURPRISE,PERCNT_SURPRISE,TIME,FILE_NAME,SOURCE,STATUS) values (:vSYMBOL,to_date(:vEARNINGS_DATE,'mm/dd/yy'),to_date(:vPERIOD_ENDING,'mm/yy'),to_number(:vESTIMATE_EPS),to_number(:vREPORTED_EPS),to_number(:vSURPRISE),to_number(:vPERCNT_SURPRISE),:vTIME,:vFILE_NAME,:vSOURCE,:vSTATUS)"
                    cursor.execute(insert_stmt,vSYMBOL=symbol,vEARNINGS_DATE=i[0],vPERIOD_ENDING=i[1],vESTIMATE_EPS=i[2].replace('$',''),vREPORTED_EPS=i[3].replace('$',''),vSURPRISE=i[4],vPERCNT_SURPRISE=num(i[5]),vTIME=i[6],vFILE_NAME=filename,vSOURCE='SEEK',vSTATUS=DOW_STATUS)
                    connection.commit()
                    #       cursor.execute('insert into PAST_EARNINGS (SYMBOL,EARNINGS_DATE,PERIOD_ENDING,ESTIMATE_EPS,REPORTED_EPS,SURPRISE,PERCNT_SURPRISE,TIME,FILE_NAME,SOURCE,STATUS) values (:vSYMBOL,:vSTATUS,:vvERROR_MSG)',vSYMBOL=i,vSTATUS=ercode,vvERROR_MSG=err)
                except cx_Oracle.IntegrityError:
                    print 'Row already exsists in PAST_EARNINGS'
        except IndexError:
            print 'symbol  present BUT earnings table map error'
            vERROR_MSG='symbol  present but error Earnings Map'
            ercode=2
### Merging any new symbols found into tracker ###
symbol_input_lis=[]
global vERROR_MSG
global ercode
vERROR_MSG='Good'
ercode=0
cursor.execute('MERGE INTO earnings_download_tracker e USING (select distinct symbol from nasdaq_avg where symbol not in (select symbol from DONOT_TRACK) and TRADEDATE>sysdate-30) c ON (e.symbol = c.symbol) WHEN MATCHED THEN UPDATE SET e.status = e.status WHEN NOT MATCHED THEN INSERT (symbol,status) VALUES (c.symbol, 5)')
connection.commit()
### selecting symbol into loop ##
cursor.execute('select DISTINCT symbol  from earnings_download_tracker where (STATUS=5 or STATUS is null) AND rownum<905 ')
##cursor.execute('select SYMBOL FROM TEST ')
for row in cursor:
        symbol_input_lis.append(row[0])
print symbol_input_lis
for i in symbol_input_lis:
    print '#################### New symbol %s ########################' %i
    download(i)
    print 'INSERT %s .' %ercode
    err=' %s' %vERROR_MSG
    print err
    cursor.execute('merge into earnings_download_tracker using dual on (symbol=:vSYMBOL) WHEN MATCHED THEN UPDATE SET status=:vSTATUS,ERROR_MSG=:vvERROR_MSG  WHEN NOT MATCHED THEN INSERT (symbol,status,ERROR_MSG) values (:vSYMBOL,:vSTATUS,:vvERROR_MSG)',vSYMBOL=i,vSTATUS=ercode,vvERROR_MSG=err)
    connection.commit()
    time.sleep(2)





