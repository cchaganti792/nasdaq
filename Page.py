import sys
import os
import selenium
import re
import xlrd
from selenium import webdriver
import time
import glob
import shutil
import locale
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
browser = webdriver.Firefox()
time.sleep(5)
global vERROR_MSG
global ercode
def open(symbol):
        try:
                a=symbol
                print a
                browser.get(a)
                time.sleep(5)
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
#url=sys.argv[1]
#download(url)
