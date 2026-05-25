import sys
import os
import locale
import time
import codecs
import re
linenum = 0
#for line in open('C:\\FS\\JEN_DAT\\UPLOADS\\Earnings\\ADMS\\ADMS_9_2018.txt'):
for line in open('C:\\FS\\JEN_DAT\\UPLOADS\\Earnings\\NVDA\\NVDA_1_2019.txt'):
    linenum+=1
    PRCNT_LIST=[]
    DOLLAR_LIST=[] 
#    for m in re.finditer('$',line):
#        print ('$ found ',m.start(), m.end())
    if  '$' in line:
#        print line
        index = 0 
        while index <len(line):
            index=line.find('$',index)
            if index == -1:
                break
            DOLLAR_LIST.append(index)
#            print('innner loop dollar',DOLLAR_LIST)
#            print ('$ found at',index)
            index += 1
#    print('outer loop dollar',DOLLAR_LIST)
    if  '%' in line:
#        print line
        index1 = 0
        while index1 <len(line):
            index1=line.find('%',index1)
            if index1==-1:
                break
            PRCNT_LIST.append(index1)
#            print('innner loop PRCNT',PRCNT_LIST)
            index1 += 1
#        print ('% LIST ',PRCNT_LIST)
    if (len(DOLLAR_LIST)==0 and len(PRCNT_LIST)==0):
        pass
    else:
        DOLLAR_LIST=DOLLAR_LIST+PRCNT_LIST
        DOLLAR_LIST.sort()
        run=0
        print ('##########---NEW LINE ----############')
        for i in DOLLAR_LIST:
            if len(DOLLAR_LIST)>1:
                if run==0:
                    listfirstnum=i
                    listcurrnum1=i
                    listlastnum=i
                else:
                    if (i-listcurrnum1<=200):
                        listcurrnum1=i
                        listlastnum=i
                        if (run==len(DOLLAR_LIST)-1):
                            if (listfirstnum<100):
                                print ('**shorten list--',0,listlastnum+100)
                                print line[0:listlastnum+100]
                            else:
                                print ('**shorten list--',listfirstnum-100,listlastnum+100)
                                print line[listfirstnum-100:listlastnum+100]
                    else:
                        if (run<len(DOLLAR_LIST)-1):
                            if (listfirstnum<100):
                                print ('shorten list--',0,listlastnum+100)
                                print line[0:listlastnum+100]
                            else:
                                print ('shorten list--',listfirstnum-100,listlastnum+100)
                                print line[listfirstnum-100:listlastnum+100]
                            listfirstnum=i
                            listcurrnum1=i
                            listlastnum=i
                        else:
                            if (listfirstnum<100):
                                print ('shorten list--',0,listlastnum+100)
                                print line[0:listlastnum+100]
                            else:
                                print ('shorten list--',listfirstnum-100,listlastnum+100)
                                print line[listfirstnum-100:listlastnum+100]
                            if (listfirstnum<100):
                                print ('shorten list--',0,i+100)
                                print line[0:i+100]
                            else:
                                print ('shorten list--',i-100,i+100)
                                print line[i-100:i+100]
                            
                run+=1
            else:
                if (i<100):
                    print ('shorten list--',0,i+100)
                else:
                    print ('shorten list--',i-100,i+100)
        print('outer loop dollar',DOLLAR_LIST)
