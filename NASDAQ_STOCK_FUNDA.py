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
connection = cx_Oracle.connect("nasdaq", "nasdaq123", "localhost/orcl")
cursor = connection.cursor()
browser = webdriver.Firefox()
time.sleep(5)
global vERROR_MSG
global ercode
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
        ercode=0
        vERROR_MSG='Good'
        try:
                a='http://financials.morningstar.com/ratios/r.html?t='+symbol+''
                print a
                browser.get(a)
                element = browser.find_element_by_link_text("Export")
                element.click()
                time.sleep(5)
                parser(symbol)
        except NoSuchElementException:
                print 'symbol not present in screener'
                vERROR_MSG='symbol not present in screener'
                print vERROR_MSG
                ercode=3
        except ValueError as e:
                print e
                vERROR_MSG=('%s  Down') %(e)
                print vERROR_MSG
                ercode=3
def parser(symbol):
        global vERROR_MSG
        global ercode
        ercode=0
        try:
                list_of_files = glob.glob("C:\Users\jenit\Downloads\\%s*Ratios.csv" %symbol)
                latest_file = max(list_of_files, key=os.path.getctime)
                print latest_file
#               a='python C:\\Python27\\Scripts\\xlsx2csv -s 0 "'+ latest_file +'" "C:\\Users\\User\\Documents\\stock_funda\\'+symbol+'"'
#               print a
#               os.system(a)
                flname=latest_file.split("ds\\")[1]
                print flname
                print '#################### Financials ########################'
                csv_read_financials(symbol,latest_file)
                print '#################### kr_Profitability ########################'
                csv_read_kr_Profitability(symbol,latest_file)
                print '#################### Profitability ########################'
                csv_read_Profitability(symbol,latest_file)
                print '#################### kr_growth ########################'
                csv_read_kr_growth(symbol,latest_file)
                print '#################### kr_CashFlow ########################'
                csv_read_kr_CashFlow(symbol,latest_file)
                print '#################### kr_FinancialHealth ########################'
                csv_read_kr_FinancialHealth(symbol,latest_file)
                print '#################### Liquidity_Financial ########################'
                csv_read_Liquidity_Financial(symbol,latest_file)
                print '#################### kr_Efficiency_Ratios ########################'
                csv_read_kr_Efficiency_Ratios(symbol,latest_file)
                print '#################### kr_Efficiency_Ratios ########################'
                shutil.move(latest_file,"C:\\Users\\jenit\\Downloads\\NASDAQ\\Funda\\"+flname)
        except ValueError as e:
                print e
                #vERROR_MSG=e+' pars'
                vERROR_MSG=('%s  pars') %(e)
                print vERROR_MSG
                ercode=4
def insert_FINANCIALS(symbol,values):
        if values[0] == 'TTM' :
                print 'inser into FINANCIALS_TTM'
                insert_stmt="insert into FINANCIALS_TTM (REPORT_DATE,SYMBOL,REVENUE,GROSS_MARGIN,OPER_INCOME,OPER_MARGIN,NET_INCOME,EPS,DIVIDEND,PAYOUT_RATIO,SHARES,BOOK_VALUE_PER_SHARE,OPER_CASH_FLOW,CAP_SPENDING,FREE_CASH_FLOW,FREECASH_PERSHARE,WORKING_CAPITAL,CURRENCY) values (sysdate,:vSYMBOL,:vREVENUE,to_number(:vGROSS_MARGIN),to_number(:vOPER_INCOME,'999,999,999'),to_number(:vOPER_MARGIN),:vNET_INCOME,to_number(:vEPS),to_number(:vDIVIDEND),to_number(:vPAYOUT_RATIO),to_number(:vSHARES,'999,999,999'),to_number(:vBOOK_VALUE_PER_SHARE),to_number(:vOPER_CASH_FLOW,'999,999,999'),to_number(:vCAP_SPENDING,'999,999,999'),to_number(:vFREE_CASH_FLOW,'999,999,999'),:vFREECASH_PERSHARE,to_number(:vWORKING_CAPITAL,'999,999,999'),:vCURRENCY)"
                cursor.execute(insert_stmt,vSYMBOL=symbol,vREVENUE=num(values[1]),vGROSS_MARGIN=values[2],vOPER_INCOME=values[3],vOPER_MARGIN=values[4],vNET_INCOME=num(values[5]),vEPS=values[6],vDIVIDEND=values[7],vPAYOUT_RATIO=values[8],vSHARES=values[9],vBOOK_VALUE_PER_SHARE=values[10],vOPER_CASH_FLOW=values[11],vCAP_SPENDING=values[12],vFREE_CASH_FLOW=values[13],vFREECASH_PERSHARE=values[14],vWORKING_CAPITAL=values[15],vCURRENCY=values[16])
                connection.commit()
        else:
                try:
                        print values
                        print num(values[1])
                        insert_stmt="insert into FINANCIALS (REPORT_DATE,SYMBOL,REVENUE,GROSS_MARGIN,OPER_INCOME,OPER_MARGIN,NET_INCOME,EPS,DIVIDEND,PAYOUT_RATIO,SHARES,BOOK_VALUE_PER_SHARE,OPER_CASH_FLOW,CAP_SPENDING,FREE_CASH_FLOW,FREECASH_PERSHARE,WORKING_CAPITAL,CURRENCY) values (to_date(:vREPORT_DATE,'yyyy-mm'),:vSYMBOL,:vREVENUE,to_number(:vGROSS_MARGIN),to_number(:vOPER_INCOME,'999,999,999'),to_number(:vOPER_MARGIN),:vNET_INCOME,to_number(:vEPS),to_number(:vDIVIDEND),to_number(:vPAYOUT_RATIO),to_number(:vSHARES,'999,999,999'),to_number(:vBOOK_VALUE_PER_SHARE),to_number(:vOPER_CASH_FLOW,'999,999,999'),to_number(:vCAP_SPENDING,'999,999,999'),to_number(:vFREE_CASH_FLOW,'999,999,999'),:vFREECASH_PERSHARE,to_number(:vWORKING_CAPITAL,'999,999,999'),:vCURRENCY)"
                        cursor.execute(insert_stmt,vREPORT_DATE=values[0],vSYMBOL=symbol,vREVENUE=num(values[1]),vGROSS_MARGIN=values[2],vOPER_INCOME=values[3],vOPER_MARGIN=values[4],vNET_INCOME=num(values[5]),vEPS=values[6],vDIVIDEND=values[7],vPAYOUT_RATIO=values[8],vSHARES=values[9],vBOOK_VALUE_PER_SHARE=values[10],vOPER_CASH_FLOW=values[11],vCAP_SPENDING=values[12],vFREE_CASH_FLOW=values[13],vFREECASH_PERSHARE=values[14],vWORKING_CAPITAL=values[15],vCURRENCY=values[16])
                        connection.commit()
                except cx_Oracle.IntegrityError:
                        print 'FINANCIALS row already present'
def insert_kr_Profitability(symbol,values):
        if values[0] == 'TTM' :
                print 'insert into kr_Profitability_ttm'
                insert_stmt="insert into kr_Profitability_ttm (REPORT_DATE,SYMBOL,REVENUE,COGS,GROSS_MARGIN,SG_A,RD,OTHER,OPERATING_MARGIN,NET_INT_OTHER,EBT_MARGIN) values (sysdate,:vSYMBOL,to_number(:vREVENUE),to_number(:vCOGS),to_number(:vGROSS_MARGIN),to_number(:vSG_A),to_number(:vRD),to_number(:vOTHER),to_number(:vOPERATING_MARGIN),to_number(:vNET_INT_OTHER),to_number(:vEBT_MARGIN))"
                cursor.execute(insert_stmt,vSYMBOL=symbol,vREVENUE=values[1],vCOGS=values[2],vGROSS_MARGIN=values[3],vSG_A=values[4],vRD=values[5],vOTHER=values[6],vOPERATING_MARGIN=values[7],vNET_INT_OTHER=values[8],vEBT_MARGIN=values[9])
                connection.commit()
        else:
                try:
                        print values
                        insert_stmt="insert into kr_Profitability (REPORT_DATE,SYMBOL,REVENUE,COGS,GROSS_MARGIN,SG_A,RD,OTHER,OPERATING_MARGIN,NET_INT_OTHER,EBT_MARGIN) values (to_date(:vREPORT_DATE,'yyyy-mm'),:vSYMBOL,to_number(:vREVENUE),to_number(:vCOGS),to_number(:vGROSS_MARGIN),to_number(:vSG_A),to_number(:vRD),to_number(:vOTHER),to_number(:vOPERATING_MARGIN),to_number(:vNET_INT_OTHER),to_number(:vEBT_MARGIN))"
                        cursor.execute(insert_stmt,vREPORT_DATE=values[0],vSYMBOL=symbol,vREVENUE=values[1],vCOGS=values[2],vGROSS_MARGIN=values[3],vSG_A=values[4],vRD=values[5],vOTHER=values[6],vOPERATING_MARGIN=values[7],vNET_INT_OTHER=values[8],vEBT_MARGIN=values[9])
                        connection.commit()
                except cx_Oracle.IntegrityError:
                        print 'kr_Profitability row already present'
def insert_Profitability(symbol,values):
        if values[0] == 'TTM' :
                print 'inser into Profitability_ttm'
                insert_stmt="insert into Profitability_ttm (REPORT_DATE,SYMBOL,TAX_RATE,NET_MARGIN,ASSET_TURNOVER_AVG,ROA,FINANCIAL_LEVERAGE_AVG,ROE,ROIC,INTEREST_COVERAGE) values (sysdate,:vSYMBOL,to_number(:vTAX_RATE),to_number(:vNET_MARGIN),to_number(:vASSET_TURNOVER_AVG),to_number(:vROA),to_number(:vFINANCIAL_LEVERAGE_AVG),to_number(:vROE),to_number(:vROIC),to_number(:vINTEREST_COVERAGE))"
                cursor.execute(insert_stmt,vSYMBOL=symbol,vTAX_RATE=values[1],vNET_MARGIN=values[2],vASSET_TURNOVER_AVG=values[3],vROA=values[4],vFINANCIAL_LEVERAGE_AVG=values[5],vROE=values[6],vROIC=values[7],vINTEREST_COVERAGE=values[8])
                connection.commit()
        else:
                try:
                        print values
                        insert_stmt="insert into Profitability (REPORT_DATE,SYMBOL,TAX_RATE,NET_MARGIN,ASSET_TURNOVER_AVG,ROA,FINANCIAL_LEVERAGE_AVG,ROE,ROIC,INTEREST_COVERAGE) values (to_date(:vREPORT_DATE,'yyyy-mm'),:vSYMBOL,to_number(:vTAX_RATE),to_number(:vNET_MARGIN),to_number(:vASSET_TURNOVER_AVG),to_number(:vROA),to_number(:vFINANCIAL_LEVERAGE_AVG),to_number(:vROE),to_number(:vROIC),to_number(:vINTEREST_COVERAGE))"
                        cursor.execute(insert_stmt,vREPORT_DATE=values[0],vSYMBOL=symbol,vTAX_RATE=values[1],vNET_MARGIN=values[2],vASSET_TURNOVER_AVG=values[3],vROA=values[4],vFINANCIAL_LEVERAGE_AVG=values[5],vROE=values[6],vROIC=values[7],vINTEREST_COVERAGE=values[8])
                        connection.commit()
                except cx_Oracle.IntegrityError:
                        print 'Profitability row already present'
def insert_kr_growth(symbol,values):
        if values[0] == 'Latest Qtr' :
                print 'inser into kr_growth_ttm'
                insert_stmt="insert into kr_growth_ttm (REPORT_DATE,SYMBOL,REVENUE_YOY,REVENUE_3Y,REVENUE_5Y,REVENUE_10Y,OI_YOY,OI_3Y,OI_5Y,OI_10Y,NI_YOY,NI_3Y,NI_5Y,NI_10Y,EPS_YOY,EPS_3Y,EPS_5Y,EPS_10Y) values (sysdate,:vSYMBOL,to_number(:vREVENUE_YOY),to_number(:vREVENUE_3Y),to_number(:vREVENUE_5Y),to_number(:vREVENUE_10Y),to_number(:vOI_YOY),to_number(:vOI_3Y),to_number(:vOI_5Y),to_number(:vOI_10Y),to_number(:vNI_YOY),to_number(:vNI_3Y),to_number(:vNI_5Y),to_number(:vNI_10Y),to_number(:vEPS_YOY),to_number(:vEPS_3Y),to_number(:vEPS_5Y),to_number(:vEPS_10Y))"
                cursor.execute(insert_stmt,vSYMBOL=symbol,vREVENUE_YOY=values[1],vREVENUE_3Y=values[2],vREVENUE_5Y=values[3],vREVENUE_10Y=values[4],vOI_YOY=values[5],vOI_3Y=values[6],vOI_5Y=values[7],vOI_10Y=values[8],vNI_YOY=values[9],vNI_3Y=values[10],vNI_5Y=values[11],vNI_10Y=values[12],vEPS_YOY=values[13],vEPS_3Y=values[14],vEPS_5Y=values[15],vEPS_10Y=values[16])
                connection.commit()
        else:
                try:
                        print values
                        insert_stmt="insert into kr_growth (REPORT_DATE,SYMBOL,REVENUE_YOY,REVENUE_3Y,REVENUE_5Y,REVENUE_10Y,OI_YOY,OI_3Y,OI_5Y,OI_10Y,NI_YOY,NI_3Y,NI_5Y,NI_10Y,EPS_YOY,EPS_3Y,EPS_5Y,EPS_10Y) values (to_date(:vREPORT_DATE,'yyyy-mm'),:vSYMBOL,to_number(:vREVENUE_YOY),to_number(:vREVENUE_3Y),to_number(:vREVENUE_5Y),to_number(:vREVENUE_10Y),to_number(:vOI_YOY),to_number(:vOI_3Y),to_number(:vOI_5Y),to_number(:vOI_10Y),to_number(:vNI_YOY),to_number(:vNI_3Y),to_number(:vNI_5Y),to_number(:vNI_10Y),to_number(:vEPS_YOY),to_number(:vEPS_3Y),to_number(:vEPS_5Y),to_number(:vEPS_10Y))"
                        cursor.execute(insert_stmt,vREPORT_DATE=values[0],vSYMBOL=symbol,vREVENUE_YOY=values[1],vREVENUE_3Y=values[2],vREVENUE_5Y=values[3],vREVENUE_10Y=values[4],vOI_YOY=values[5],vOI_3Y=values[6],vOI_5Y=values[7],vOI_10Y=values[8],vNI_YOY=values[9],vNI_3Y=values[10],vNI_5Y=values[11],vNI_10Y=values[12],vEPS_YOY=values[13],vEPS_3Y=values[14],vEPS_5Y=values[15],vEPS_10Y=values[16])
                        connection.commit()
                except cx_Oracle.IntegrityError:
                        print 'kr_growth row already present'
def insert_kr_CashFlow(symbol,values):
        if values[0] == 'TTM' :
                print 'insert into kr_CashFlow_ttm'
                if len(values)==6:
                        insert_stmt="insert into kr_CashFlow_ttm (REPORT_DATE,SYMBOL,OPER_CASHFLOW_GRO_PR_YOY,FREE_CASHFLOW_GRO_PR_YOY,CAP_EX_AS_PR_SALES,FREE_CASHFLOW_PER_SALES,FREE_CASHFLOW_PER_NI) values (sysdate,:vSYMBOL,to_number(:vOPER_CASHFLOW_GRO_PR_YOY),to_number(:vFREE_CASHFLOW_GRO_PR_YOY),to_number(:vCAP_EX_AS_PR_SALES),to_number(:vFREE_CASHFLOW_PER_SALES),to_number(:vFREE_CASHFLOW_PER_NI))"
                        cursor.execute(insert_stmt,vSYMBOL=symbol,vOPER_CASHFLOW_GRO_PR_YOY=values[1],vFREE_CASHFLOW_GRO_PR_YOY=values[2],vCAP_EX_AS_PR_SALES=values[3],vFREE_CASHFLOW_PER_SALES=values[4],vFREE_CASHFLOW_PER_NI=values[5])
                        connection.commit()
                elif len(values)==5:
                        insert_stmt="insert into kr_CashFlow_ttm (REPORT_DATE,SYMBOL,OPER_CASHFLOW_GRO_PR_YOY,FREE_CASHFLOW_GRO_PR_YOY,CAP_EX_AS_PR_SALES,FREE_CASHFLOW_PER_SALES) values (sysdate,:vSYMBOL,to_number(:vOPER_CASHFLOW_GRO_PR_YOY),to_number(:vFREE_CASHFLOW_GRO_PR_YOY),to_number(:vCAP_EX_AS_PR_SALES),to_number(:vFREE_CASHFLOW_PER_SALES))"
                        cursor.execute(insert_stmt,vSYMBOL=symbol,vOPER_CASHFLOW_GRO_PR_YOY=values[1],vFREE_CASHFLOW_GRO_PR_YOY=values[2],vCAP_EX_AS_PR_SALES=values[3],vFREE_CASHFLOW_PER_SALES=values[4])
                        connection.commit()
                        
        else:
                try:
                        print values
                        if len(values)==6:
                                insert_stmt="insert into kr_CashFlow (REPORT_DATE,SYMBOL,OPER_CASHFLOW_GRO_PR_YOY,FREE_CASHFLOW_GRO_PR_YOY,CAP_EX_AS_PR_SALES,FREE_CASHFLOW_PER_SALES,FREE_CASHFLOW_PER_NI) values (to_date(:vREPORT_DATE,'yyyy-mm'),:vSYMBOL,to_number(:vOPER_CASHFLOW_GRO_PR_YOY),to_number(:vFREE_CASHFLOW_GRO_PR_YOY),to_number(:vCAP_EX_AS_PR_SALES),to_number(:vFREE_CASHFLOW_PER_SALES),to_number(:vFREE_CASHFLOW_PER_NI))"
                                cursor.execute(insert_stmt,vREPORT_DATE=values[0],vSYMBOL=symbol,vOPER_CASHFLOW_GRO_PR_YOY=values[1],vFREE_CASHFLOW_GRO_PR_YOY=values[2],vCAP_EX_AS_PR_SALES=values[3],vFREE_CASHFLOW_PER_SALES=values[4],vFREE_CASHFLOW_PER_NI=values[5])
                                connection.commit()
                        elif len(values)==5:
                                insert_stmt="insert into kr_CashFlow (REPORT_DATE,SYMBOL,OPER_CASHFLOW_GRO_PR_YOY,FREE_CASHFLOW_GRO_PR_YOY,CAP_EX_AS_PR_SALES,FREE_CASHFLOW_PER_SALES) values (to_date(:vREPORT_DATE,'yyyy-mm'),:vSYMBOL,to_number(:vOPER_CASHFLOW_GRO_PR_YOY),to_number(:vFREE_CASHFLOW_GRO_PR_YOY),to_number(:vCAP_EX_AS_PR_SALES),to_number(:vFREE_CASHFLOW_PER_SALES))"
                                cursor.execute(insert_stmt,vREPORT_DATE=values[0],vSYMBOL=symbol,vOPER_CASHFLOW_GRO_PR_YOY=values[1],vFREE_CASHFLOW_GRO_PR_YOY=values[2],vCAP_EX_AS_PR_SALES=values[3],vFREE_CASHFLOW_PER_SALES=values[4])
                                connection.commit()
                except cx_Oracle.IntegrityError:
                        print 'kr_CashFlow row already present'
def insert_kr_FinancialHealth(symbol,values):
        if values[0] == 'Latest Qtr' :
                print 'insert into KR_FINANCIAL_HEALTH_PR_ttm'
                insert_stmt="insert into KR_FINANCIAL_HEALTH_PR_ttm (REPORT_DATE,SYMBOL,CASH_SHORT_TERM_INV,ACCOUNTS_RECEIVABLE,INVENTORY,OTHER_CURRENT_ASSETS,TOTAL_CURRENT_ASSETS,NET_PP_E,INTANGIBLES,OTHER_LONG_TERM_ASSETS,TOTAL_ASSETS,ACCOUNTS_PAYABLE,SHORT_TERM_DEBT,TAXES_PAYABLE,ACCRUED_LIABILITIES,OTHER_SHORT_TERM_LIAB,TOTAL_CUR_LIAB,LONG_TERM_DEBT,OTHER_LONG_TERM_LIAB,TOTAL_LIAB,TOTAL_STOCKHOLDERS_EQUITY,TOTAL_LIAB_EQUITY) values (sysdate,:vSYMBOL,to_number(:vCASH_SHORT_TERM_INV),to_number(:vACCOUNTS_RECEIVABLE),to_number(:vINVENTORY),to_number(:vOTHER_CURRENT_ASSETS),to_number(:vTOTAL_CURRENT_ASSETS),to_number(:vNET_PP_E),to_number(:vINTANGIBLES),to_number(:vOTHER_LONG_TERM_ASSETS),to_number(:vTOTAL_ASSETS),to_number(:vACCOUNTS_PAYABLE),to_number(:vSHORT_TERM_DEBT),to_number(:vTAXES_PAYABLE),to_number(:vACCRUED_LIABILITIES),to_number(:vOTHER_SHORT_TERM_LIAB),to_number(:vTOTAL_CUR_LIAB),to_number(:vLONG_TERM_DEBT),to_number(:vOTHER_LONG_TERM_LIAB),to_number(:vTOTAL_LIAB),to_number(:vTOTAL_STOCKHOLDERS_EQUITY),to_number(:vTOTAL_LIAB_EQUITY))"
                cursor.execute(insert_stmt,vSYMBOL=symbol,vCASH_SHORT_TERM_INV=values[1],vACCOUNTS_RECEIVABLE=values[2],vINVENTORY=values[3],vOTHER_CURRENT_ASSETS=values[4],vTOTAL_CURRENT_ASSETS=values[5],vNET_PP_E=values[6],vINTANGIBLES=values[7],vOTHER_LONG_TERM_ASSETS=values[8],vTOTAL_ASSETS=values[9],vACCOUNTS_PAYABLE=values[10],vSHORT_TERM_DEBT=values[11],vTAXES_PAYABLE=values[12],vACCRUED_LIABILITIES=values[13],vOTHER_SHORT_TERM_LIAB=values[14],vTOTAL_CUR_LIAB=values[15],vLONG_TERM_DEBT=values[16],vOTHER_LONG_TERM_LIAB=values[17],vTOTAL_LIAB=values[18],vTOTAL_STOCKHOLDERS_EQUITY=values[19],vTOTAL_LIAB_EQUITY=values[20])
                connection.commit()
        else:
                try:
                        print values
                        insert_stmt="insert into KR_FINANCIAL_HEALTH_PR (REPORT_DATE,SYMBOL,CASH_SHORT_TERM_INV,ACCOUNTS_RECEIVABLE,INVENTORY,OTHER_CURRENT_ASSETS,TOTAL_CURRENT_ASSETS,NET_PP_E,INTANGIBLES,OTHER_LONG_TERM_ASSETS,TOTAL_ASSETS,ACCOUNTS_PAYABLE,SHORT_TERM_DEBT,TAXES_PAYABLE,ACCRUED_LIABILITIES,OTHER_SHORT_TERM_LIAB,TOTAL_CUR_LIAB,LONG_TERM_DEBT,OTHER_LONG_TERM_LIAB,TOTAL_LIAB,TOTAL_STOCKHOLDERS_EQUITY,TOTAL_LIAB_EQUITY) values (to_date(:vREPORT_DATE,'yyyy-mm'),:vSYMBOL,to_number(:vCASH_SHORT_TERM_INV),to_number(:vACCOUNTS_RECEIVABLE),to_number(:vINVENTORY),to_number(:vOTHER_CURRENT_ASSETS),to_number(:vTOTAL_CURRENT_ASSETS),to_number(:vNET_PP_E),to_number(:vINTANGIBLES),to_number(:vOTHER_LONG_TERM_ASSETS),to_number(:vTOTAL_ASSETS),to_number(:vACCOUNTS_PAYABLE),to_number(:vSHORT_TERM_DEBT),to_number(:vTAXES_PAYABLE),to_number(:vACCRUED_LIABILITIES),to_number(:vOTHER_SHORT_TERM_LIAB),to_number(:vTOTAL_CUR_LIAB),to_number(:vLONG_TERM_DEBT),to_number(:vOTHER_LONG_TERM_LIAB),to_number(:vTOTAL_LIAB),to_number(:vTOTAL_STOCKHOLDERS_EQUITY),to_number(:vTOTAL_LIAB_EQUITY))"
                        cursor.execute(insert_stmt,vREPORT_DATE=values[0],vSYMBOL=symbol,vCASH_SHORT_TERM_INV=values[1],vACCOUNTS_RECEIVABLE=values[2],vINVENTORY=values[3],vOTHER_CURRENT_ASSETS=values[4],vTOTAL_CURRENT_ASSETS=values[5],vNET_PP_E=values[6],vINTANGIBLES=values[7],vOTHER_LONG_TERM_ASSETS=values[8],vTOTAL_ASSETS=values[9],vACCOUNTS_PAYABLE=values[10],vSHORT_TERM_DEBT=values[11],vTAXES_PAYABLE=values[12],vACCRUED_LIABILITIES=values[13],vOTHER_SHORT_TERM_LIAB=values[14],vTOTAL_CUR_LIAB=values[15],vLONG_TERM_DEBT=values[16],vOTHER_LONG_TERM_LIAB=values[17],vTOTAL_LIAB=values[18],vTOTAL_STOCKHOLDERS_EQUITY=values[19],vTOTAL_LIAB_EQUITY=values[20])
                        connection.commit()
                except cx_Oracle.IntegrityError:
                        print 'kr_CashFlow row already present'
def insert_Liquidity_Financial_HEALTH(symbol,values):
        if values[0] == 'Latest Qtr' :
                print 'insert into LIQUIDITY_FINANCIAL_HEALTH_ttm'
                insert_stmt="insert into LIQUIDITY_FINANCIAL_HEALTH_ttm (REPORT_DATE,SYMBOL,CURRENT_RATIO,QUICK_RATIO,FINANCIAL_LEVERAGE,DEBT_PR_EQUITY) values (sysdate,:vSYMBOL,to_number(:vCURRENT_RATIO),to_number(:vQUICK_RATIO),to_number(:vFINANCIAL_LEVERAGE),to_number(:vDEBT_PR_EQUITY))"
                cursor.execute(insert_stmt,vSYMBOL=symbol,vCURRENT_RATIO=values[1],vQUICK_RATIO=values[2],vFINANCIAL_LEVERAGE=values[3],vDEBT_PR_EQUITY=values[4])
                connection.commit()
        else:
                try:
                        print values
                        insert_stmt="insert into LIQUIDITY_FINANCIAL_HEALTH (REPORT_DATE,SYMBOL,CURRENT_RATIO,QUICK_RATIO,FINANCIAL_LEVERAGE,DEBT_PR_EQUITY) values (to_date(:vREPORT_DATE,'yyyy-mm'),:vSYMBOL,to_number(:vCURRENT_RATIO),to_number(:vQUICK_RATIO),to_number(:vFINANCIAL_LEVERAGE),to_number(:vDEBT_PR_EQUITY))"
                        cursor.execute(insert_stmt,vREPORT_DATE=values[0],vSYMBOL=symbol,vCURRENT_RATIO=values[1],vQUICK_RATIO=values[2],vFINANCIAL_LEVERAGE=values[3],vDEBT_PR_EQUITY=values[4])
                        connection.commit()
                except cx_Oracle.IntegrityError:
                        print 'LIQUIDITY_FINANCIAL_HEALTH row already present'
def insert_kr_Efficiency_Ratios(symbol,values):
        if values[0] == 'TTM' :
                print 'inser into kr_Efficiency_Ratios_ttm'
                insert_stmt="insert into kr_Efficiency_Ratios_ttm (REPORT_DATE,SYMBOL,DAYS_SALES_OUTSTANDING,DAYS_INVENTORY,PAYABLES_PERIOD,CASH_CONVERSION_CYCLE,RECEIVABLES_TURNOVER,INVENTORY_TURNOVER,FIXED_ASSETS_TURNOVER,ASSET_TURNOVER) values (sysdate,:vSYMBOL,to_number(:vDAYS_SALES_OUTSTANDING),to_number(:vDAYS_INVENTORY),to_number(:vPAYABLES_PERIOD),to_number(:vCASH_CONVERSION_CYCLE),to_number(:vRECEIVABLES_TURNOVER),to_number(:vINVENTORY_TURNOVER),to_number(:vFIXED_ASSETS_TURNOVER),to_number(:vASSET_TURNOVER))"
                cursor.execute(insert_stmt,vSYMBOL=symbol,vDAYS_SALES_OUTSTANDING=values[1],vDAYS_INVENTORY=values[2],vPAYABLES_PERIOD=values[3],vCASH_CONVERSION_CYCLE=values[4],vRECEIVABLES_TURNOVER=values[5],vINVENTORY_TURNOVER=values[6],vFIXED_ASSETS_TURNOVER=values[7],vASSET_TURNOVER=values[8])
                connection.commit()
        else:
                try:
                        print values
                        insert_stmt="insert into kr_Efficiency_Ratios (REPORT_DATE,SYMBOL,DAYS_SALES_OUTSTANDING,DAYS_INVENTORY,PAYABLES_PERIOD,CASH_CONVERSION_CYCLE,RECEIVABLES_TURNOVER,INVENTORY_TURNOVER,FIXED_ASSETS_TURNOVER,ASSET_TURNOVER) values (to_date(:vREPORT_DATE,'yyyy-mm'),:vSYMBOL,to_number(:vDAYS_SALES_OUTSTANDING),to_number(:vDAYS_INVENTORY),to_number(:vPAYABLES_PERIOD),to_number(:vCASH_CONVERSION_CYCLE),to_number(:vRECEIVABLES_TURNOVER),to_number(:vINVENTORY_TURNOVER),to_number(:vFIXED_ASSETS_TURNOVER),to_number(:vASSET_TURNOVER))"
                        cursor.execute(insert_stmt,vREPORT_DATE=values[0],vSYMBOL=symbol,vDAYS_SALES_OUTSTANDING=values[1],vDAYS_INVENTORY=values[2],vPAYABLES_PERIOD=values[3],vCASH_CONVERSION_CYCLE=values[4],vRECEIVABLES_TURNOVER=values[5],vINVENTORY_TURNOVER=values[6],vFIXED_ASSETS_TURNOVER=values[7],vASSET_TURNOVER=values[8])
                        connection.commit()
                except cx_Oracle.IntegrityError:
                        print 'kr_Efficiency_Ratios row already present'
def insert_quat(symbol,values):
        global ercode
        global vERROR_MSG
        try:
                insert_stmt="insert into PROFIT_LOSS_QUAT_CONS (SYMBOL,REPORT_DATE,SALES,EXPENSES,OTHER_INCOME,DEPRECIATION,INTEREST,PBT,TAX,NET_PROFIT,OPERATING_PROFIT) values (:vSYMBOL,to_date(:vREPORT_DATE,'mon-yy'),to_number(:vSALES),to_number(:vEXPENSES),to_number(:vOTHER_INCOME),to_number(:vDEPRECIATION),to_number(:vINTEREST),to_number(:vPBT),to_number(:vTAX),to_number(:vNET_PROFIT),to_number(:vOPERATING_PROFIT))"
                cursor.execute(insert_stmt,vSYMBOL=symbol,vREPORT_DATE=values[0],vSALES=values[1],vEXPENSES=values[2],vOTHER_INCOME=values[3],vDEPRECIATION=values[4],vINTEREST=values[5],vPBT=values[6],vTAX=values[7],vNET_PROFIT=values[8],vOPERATING_PROFIT=values[9])
                connection.commit()
                ercode=1
                vERROR_MSG=''
                print 'ercode is %d' % ercode
        except cx_Oracle.IntegrityError:
                print 'QUAT row already present'
                ercode=1
                vERROR_MSG=''
                print 'ercode is %d' % ercode
def csv_read_financials(symbol,flname):
        cnt=-1
        lis=[]
#        csv1='C:\\Users\\User\\Documents\\stock_funda\\'+symbol+'\\Data Sheet.csv'
        with open(flname) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if cnt>0:
                                lis=lis+[row]
                                cnt=cnt-1
                        if row == ['Financials']:
                                cnt=16
                gip=zip(*lis)
                currlist=(gip[0][1].split())
                del gip[0]
                for i in gip:
                        #print i
                        i=i+(currlist[1],)
                        insert_FINANCIALS(symbol,i)
def csv_read_kr_Profitability(symbol,flname):
        cnt=-1
        lis=[]
        with open(flname) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if cnt>0:
                                lis=lis+[row]
                                cnt=cnt-1
                        if row == ['Key Ratios -> Profitability']:
                                cnt=10
                gip=zip(*lis)
                del gip[0]
                for i in gip:
                        #print i
                        insert_kr_Profitability(symbol,i)
def csv_read_Profitability(symbol,flname):
        cnt=-1
        lis=[]
        with open(flname) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if row == []:
                                pass
                        else:
                                if row[0] == 'Profitability' or cnt>0:
                                        lis=lis+[row]
                                        cnt=cnt-1
                                if row[0] == 'Profitability':
                                        cnt=8
                gip=zip(*lis)
                del gip[0]
                for i in gip:
                        #print i
                        insert_Profitability(symbol,i)
def csv_read_kr_growth(symbol,flname):
        cnt=-1
        lis=[]
        with open(flname) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if cnt>0:
                                del row[0]
                                if row == []:
                                        pass
                                else:
                                        lis=lis+[row]
                                cnt=cnt-1
                        if row == ['Key Ratios -> Growth']:
                                cnt=21
                gip=zip(*lis)
                #del gip[0]
                for i in gip:
                        #print i
                        insert_kr_growth(symbol,i)
def csv_read_kr_CashFlow(symbol,flname):
        cnt=-1
        lis=[]
        cntreal=-1
        cnt_est=0
        with open(flname) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if cnt_est>0:
                                cnt_est=cnt_est-1
                                cntreal=cntreal+1
                                if row == []:
                                       cnt_est=0
                        if row == ['Key Ratios -> Cash Flow']:
                                cnt_est=7
        with open(flname) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if cnt>0:
                                lis=lis+[row]
                                cnt=cnt-1
                        if row == ['Key Ratios -> Cash Flow']:
                                cnt=cntreal
                gip=zip(*lis)
                del gip[0]
                for i in gip:
                        #print i
                        #print len(i)
                        insert_kr_CashFlow(symbol,i)                        
def csv_read_kr_FinancialHealth(symbol,flname):
        cnt=-1
        lis=[]
        with open(flname) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if cnt>0:
                                lis=lis+[row]
                                cnt=cnt-1
                        if row == ['Key Ratios -> Financial Health']:
                                cnt=21
                gip=zip(*lis)
                del gip[0]
                for i in gip:
                        #print i
                        insert_kr_FinancialHealth(symbol,i)
def csv_read_Liquidity_Financial(symbol,flname):
        cnt=-1
        lis=[]
        with open(flname) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if row == []:
                                pass
                        else:
                                if row[0] == 'Liquidity/Financial Health' or cnt>0:
                                        lis=lis+[row]
                                        cnt=cnt-1
                                if row[0] == 'Liquidity/Financial Health':
                                        cnt=4
                gip=zip(*lis)
                del gip[0]
                for i in gip:
                        #print i
                        insert_Liquidity_Financial_HEALTH(symbol,i)
def csv_read_kr_Efficiency_Ratios(symbol,flname):
        cnt=-1
        lis=[]
        with open(flname) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if cnt>0:
                                lis=lis+[row]
                                cnt=cnt-1
                        if row == ['Key Ratios -> Efficiency Ratios']:
                                cnt=9
                gip=zip(*lis)
                del gip[0]
                for i in gip:
                        #print i
                        insert_kr_Efficiency_Ratios(symbol,i)
def csv_read_quat(symbol):
        global ercode
        global vERROR_MSG
        cnt=-1
        lis=[]
        csv1='C:\\Users\\User\\Documents\\stock_funda\\'+symbol+'\\Data Sheet.csv'
        with open(csv1) as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                        if cnt>0:
                                lis=lis+[row]
                                cnt=cnt-1
                        if row == ['Quarters', '', '', '', '', '', '', '', '', '', '']:
                                cnt=10
                gip=zip(*lis)
                del gip[0]
                for i in gip:
                        if i[0] == '' or i[1] == '':
                                print 'quat is  null'
                                ercode=1
                                vERROR_MSG=''
                        else:
                                insert_quat(symbol,i)   
### clear download directory ###
#for file in (glob.glob("C:\Users\User\Downloads\\*.xlsx")):
#        flname=file.split("ds\\")[1]
#        shutil.move(file,"C:\\Users\\User\\Downloads\\stock_funda_temp\\"+flname)
symbol_input_lis=[]
global vERROR_MSG
global ercode
vERROR_MSG='Good'
ercode=0
##cursor.execute('select NSECODE from NSESTOCK where NSECODE NOT IN (SELECT NSECODE FROM NSESTOCK_INDX union SELECT NSECODE FROM funda_download_status where status=1) and rownum<50 order by nsecode')
##cursor.execute('select distinct symbol as nsecode from nsehist_nf where tradedate=:vDATE and symbol NOT IN (SELECT NSECODE FROM NSESTOCK_INDX union SELECT NSECODE FROM funda_download_status where status in (1)) and rownum<350 order by nsecode',vDATE='24-NOV-17')
##cursor.execute('select NSECODE from NSESTOCK where NSECODE=:code',code='ANDHRABANK')
##cursor.execute('select DISTINCT SYMBOL  from nsehist_nf where SYMBOL=:code',code='BALAJITELE')
## from stokc list## cursor.execute('select DISTINCT SYMBOL  from nasdaq_stock_list_stage where rownum<5 ')
##cursor.execute('select DISTINCT STOCKCODE  from US_STOCK_funda_download_status where (STATUS in (1,2) or STATUS is null) and rownum<1250 ')
cursor.execute('select DISTINCT STOCKCODE  from US_STOCK_funda_download_status where STATUS=3 and rownum<1000 ')
##cursor.execute('select DISTINCT STOCKCODE  from US_STOCK_funda_download_status where  STATUS is not null and rownum<10 ')
##cursor.execute('select DISTINCT STOCKCODE  from temp_dp where  rownum<15 ')
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
        time.sleep(2)
        ##cursor.execute('insert into funda_download_status (nsecode,stream,status) values (:vSYMBOL,:vSTREAM,:vSTATUS)',vSYMBOL=i,vSTREAM='CONS',vSTATUS=ercode)
        ##print 'INSERT %s .' %ercode
        ##print 'INSERT %s .'
        ##err=' %s' %vERROR_MSG
        ##print err
        ##cursor.execute('merge into funda_download_status using dual on (NSECOde=:vSYMBOL) WHEN MATCHED THEN UPDATE SET status=:vSTATUS,ERROR_MSG=:vvERROR_MSG  WHEN NOT MATCHED THEN INSERT (nsecode,stream,status,ERROR_MSG) values (:vSYMBOL,:vSTREAM,:vSTATUS,:vvERROR_MSG)',vSYMBOL=i,vSTREAM='CONS',vSTATUS=ercode,vvERROR_MSG=err)
        ##print 'hello'
        ##connection.commit()
        
