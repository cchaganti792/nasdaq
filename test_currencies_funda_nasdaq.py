import os
import selenium
import re
import xlrd
import xlrd
from selenium import webdriver
import pandas
import csv
import xlsx2csv
import glob
csv1='C:\\Users\\User\\Downloads\\NASDAQ\\Funda\\YY Key Ratios.csv'
lis=[]
cnt=-1
with open(csv1) as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
            if cnt>0:
                lis=lis+[row]
                cnt=cnt-1
            if row == ['Financials']:
                cnt=16
    gip=zip(*lis)
    currency=(gip[0][1].split())
    print currency[1]
    del gip[0]
    for i in gip:
        print i+(currency[1],)
