import os
import time
import glob
import shutil
import cx_Oracle
connection = cx_Oracle.connect("nasdaq", "nasdaq123", "localhost/orcl")
cursor = connection.cursor()
list_of_files = glob.glob("C:\\Users\\jenit\\Downloads\\NASDAQ*.csv")
for i in list_of_files:
    flname=i.split("ds\\")[1]
    shutil.move(i,"C:\\Users\\jenit\\Downloads\\NASDAQ\\"+flname)
    new_location_file="C:\\Users\\jenit\\Downloads\\NASDAQ\\"+flname
    print (flname)
    cursor.callproc('stock_split_status',())
    cursor.execute("select count(*) from  SPLIT_STOCK_DOWNLOAD_STATUS where DSTATE='N'")
    for row in cursor:
        ##symbol_input_lis.append(row[0])
        print (row[0])
        if row[0]>=1 :
            print ('entered split download part')
            cmd = 'date'
            #os.system(cmd)
            os.system('python SPLIT_INFO_DOWNLOAD_YFINANCE.py')
        else :
            print (' I guess split information is already downloaded ')
    ##print symbol_input_lis
    print ('***************---- NASDAQ UPLOAD --- *******')
    os.system('C:\\Python27\\python NASDAQ_UPLOAD.py')
    print ('***************---- NASDAQ Analytics --- *******')
    os.system('C:\\Python27\\python NASDAQ_Analytics.py')
    print ('***************---- NASDAQ Bullish --- *******')
    ##solving removeing things not reffered for long ## os.system('python Nasdaq_Bullish.py')
    try:
        shutil.move(new_location_file,"C:\\Users\\jenit\\Downloads\\NASDAQ\\Nasdaq_bkp\\"+flname)
        print (new_location_file)
    except IOError:
        print ('error in moving file ')

#print list_of_files[0]
#flname=latest_file.split("ds\\")[1]
#shutil.move(latest_file,"C:\\Users\\User\\Downloads\\stock_funda_temp\\"+flname)
#latest_file = min(list_of_files, key=os.path.getctime)
#print latest_file
##os.system('python NASDAQ_UPLOAD.py')
##os.system('python NASDAQ_Analytics.py')
##os.system('python Nasdaq_Bullish.py')
