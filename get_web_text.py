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
Page.open('https://seekingalpha.com/article/4217444-corcept-therapeutics-incorporated-cort-ceo-joseph-belanoff-q3-2018-results-earnings-call?part=single')
element=browser.find_element_by_id("a-body")
print(element.text)
file = open("C:\\Users\\User\\testfile.txt","w") 
file.write(element.text) 
file.close()
#completeName = os.path.join("C:\\Users\\User\\", "cort_page.txt")
#file_object = codecs.open(completeName, "w", "utf-8")
#print element.text
#file_object.write(element.text)
#file_object.close
