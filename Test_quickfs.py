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
symbol='spg'
print symbol
Page.open('https://quickfs.net/company/'+symbol+'')
browser.find_element_by_xpath("/html/body/app-root/app-company/div/div/div[2]/div/company-overview/div[2]/div[2]/div/company-financial-table/div/select-period-dropdown/div/button").click()
