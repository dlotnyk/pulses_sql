# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 11:05:06 2018

@author: dmytr
"""
from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
#import scipy.signal as ss
#import os
#import shutil
import logging
import datetime
from functools import wraps
#import sys
#import time as e_t
#from mpl_toolkits.mplot3d import Axes3D
import warnings
warnings.simplefilter('ignore', np.RankWarning)
from createdata import sql_create as sqdata

class timetotemp(sqdata):
    vals=['time','Q','Tmc','index','pulse']
#---------------------------------------------------------
    def __init__(self,conf,sett):
        '''connect to conn mysql server with data'''
        self.connect_f(conf)
        self.sett=sett
        self.title=sett['pressure']
        assert self.sett['indent'] >= 0, "cut from begin. it should be > 0"
        assert self.sett['cut'] > self.sett['indent'] >= 0, "cut always greater than indent"
        assert self.sett['offset'] >= 0, "offset it should be > 0"
        self.rawdata1,self.rawdata2=self.import_fun()
        self.pulse_id=self.pulse_indicies()
    def __repr__(self):
        return "Pulse analysis"
#---------------------------------------------------------      
    def time_this(original_function):  
        '''Measures the processing time. Decorator'''
        @wraps(original_function)                      
        def new_function(*args,**kwargs):    
            import time       
            before = time.time()                     
            x = original_function(*args,**kwargs)                
            after = time.time()                      
            print ("Elapsed Time of fun {0} = {1}".format(original_function.__name__,after-before))      
            return x                                             
        return new_function  
##---------------------------------------------------------
    def my1_logger(orig_func):
        '''Decorate function to write into log on the level ERROR'''
        logging.getLogger('').handlers = []
        logging.basicConfig(filename='work1.log'.format(orig_func.__name__), level=logging.INFO)
        
        @wraps(orig_func)
        def wrapper(*args,**kwargs):
            dt=datetime.datetime.now()
            dt_str=str(dt)
            vrema=dt_str.split('.')[0]
            logging.info(
                    ' {} Ran with args: {}, and kwargs: {} \n'.format(vrema, args, kwargs))
            return orig_func(*args, **kwargs) 
        return wrapper 
  #---------------------------------------------------------  
    @my1_logger  
    @time_this       
    def pulse_st(self):
       tab1_count=("SELECT COUNT(`index`) FROM `{}`".format(self.tables[self.sett['pressure']][0]))
       self.cursor.execute(tab1_count)
       res1=self.cursor.fetchall() 
       b=str(res1[0][0])
       self.mval=round(res1[0][0],-len(b)+1)+10**(len(b)-1) # value grater than index. starting point for new pulsing data
        
       return self.mval
 #---------------------------------------------------------   
    @my1_logger  
    @time_this
    def import_fun(self):
        '''select time,Q and Tmc data from database. slice later. could be improved with BETWEEN'''
        data1=self.select_col(self.vals,self.tables[self.sett['pressure']][0])
        data2=self.select_col(self.vals,self.tables[self.sett['pressure']][1])
        a=np.shape(data1)[0]
        b=str(a)
        self.mval=round(a,-len(b)+1)+10**(len(b)-1) # value grater than index. starting point for new pulsing data
        data11=data1[self.sett['indent']:self.sett['cut'],:]
        data21=data2[self.sett['indent']:self.sett['cut'],:]
#        data2=data2[0:-self.sett['offset'],:]
        data13=np.transpose(data11)
        data23=np.transpose(data21)
        t0=data23[0][0]
        data13[0]=data13[0]-t0
        data23[0]=data23[0]-t0  
#        print(np.shape(data1),np.shape(data2),np.shape(data13),np.shape(data23))
        return data13,data23
#---------------------------------------------------------    
    @my1_logger  
    @time_this
    def pulse_indicies(self):
        '''Find pulses in IC fork'''
        a=np.where(np.abs(self.rawdata2[1])>1500)
        pulse=[]
        pulse.append(a[0][0])
        ite=a[0][0]
        for x in range(1,np.shape(a)[1]):
            if (a[0][x] > ite+100):
                pulse.append(a[0][x])
                ite=a[0][x]
            else:
                ite += 1
        pul=np.asarray(pulse)     
#        print(np.shape(pul))
        return pul
#---------------------------------------------------------    
    @my1_logger  
    @time_this
    def pulse_renumb(self):
        '''renumber of pulses and update in sql. start from mval and 1000 per each pulse'''

        ini=self.mval
        pul_id=0
        id1=0
        id2=self.pulse_id[0]
        increm=1000/(id2-id1)
        count=0
        nump=1
        for ii in self.rawdata2[3]:
            if ii == self.rawdata2[3][self.pulse_id[pul_id]]:
#                print(pul_id, self.pulse_id[pul_id])
                pul_id += 1
                if pul_id == np.shape(self.pulse_id)[0]:
                    id1=self.pulse_id[pul_id-1]
                    id2=np.shape(self.rawdata2)[1]
                    print(id1,id2)
                    pul_id-=1                    
                else:
                    id1=self.pulse_id[pul_id-1]
                    id2=self.pulse_id[pul_id]
                increm=1000/(id2-id1)
                self.rawdata1[4][count]=self.mval+1000*nump
                self.__set_pulse(self.sett['indent']+count+1,self.mval+1000*nump)
                nump+=1
            else:
                self.rawdata1[4][count]=ini
                self.__set_pulse(self.sett['indent']+count+1,ini)
            count+=1
            ini+=increm
        self.cnx.commit()
 #---------------------------------------------------------                   
    def __set_pulse(self,ind,val):
        '''update a value of `pulse` in a HEC table. it is a primary key bonded with IC'''
#        UPDATE `table_one` SET `value` = '200' WHERE `table_one`.`id` = 1;
        set_v=("UPDATE `{0}` SET `pulse` = '{1}' WHERE `{0}`.`index` = '{2}'".format(self.tables[self.sett['pressure']][0],val,int(ind)))
        self.cursor.execute(set_v)
#        print(set_v)
  #---------------------------------------------------------  
    @my1_logger  
    @time_this    
    def pulse_remove(self,n1,n2):
        '''Remove pulse and n1/n2-surroundings'''
        a=range(-n1,n1*n2)
        s=[]
        for p in np.nditer(self.pulseID):
            for ad in np.nditer(a):
                s.append(ad+p)
        pulse_rem=np.asarray(s)
        d1=np.in1d(range(0,len(self.rawdata1[1])),pulse_rem,assume_unique=True,invert = True)
        d2=np.in1d(range(0,len(self.rawdata2[1])),pulse_rem,assume_unique=True,invert = True)
        return d1,d2
        
# main program below------------------------------------------------------------------------   
conf = {
        'user': 'dlotnyk',
        'password': 'RiDeaBiKe2RuN',
        'host': '127.0.0.1',
        'database': 'pulses_he3',
        'raise_on_warnings': True,
        }
sett1={'pressure':'0bar','indent':9200,'cut':47000,'offset':1800
       }
sett2={'pressure':'9psi','indent':10000,'cut':53000,'offset':700
       }
sett3={'pressure':'22bar','indent':1000,'cut':41000,'offset':1
       }

A=timetotemp(conf,sett1)
vv=A.pulse_st()
#print(vv)
#A.pulse_renumb()
#A.__set_pulse(10,9.5)
#numz=A.sett['indent']+A.pulse_id[0]+1
#query=("SELECT `Q` FROM `{0}` WHERE `{0}`.`index` = {1}".format(A.tables[A.sett['pressure']][1],numz))
#print(query)
#A.cursor.execute(query)
#res=A.cursor.fetchall()
#print('res = ',res)
fig1 = plt.figure(1, clear = True)
ax1 = fig1.add_subplot(211)
ax1.set_ylabel('Q')
ax1.set_xlabel('time [sec]')
ax1.set_title('Q vs time for both forks')
ax1.scatter(A.rawdata1[3],A.rawdata1[1],color='green', s=0.5)
ax1.scatter(A.rawdata2[0],A.rawdata2[1],color='red', s=0.5)
#ax1.scatter(C.rawdata1[0][C.nopulse1],C.rawdata1[1][C.nopulse1],color='red', s=0.5)
ax2 = fig1.add_subplot(212)
ax2.set_ylabel('T')
ax2.set_xlabel('time [sec]')
ax2.set_title('T vs time for both forks')
ax2.scatter(A.rawdata1[3],A.rawdata1[2],color='green', s=0.5)
ax2.scatter(A.rawdata2[0],A.rawdata2[2],color='red', s=0.5)
plt.grid()
plt.show()

fig2 = plt.figure(2, clear = True)
ax1 = fig2.add_subplot(111)
ax1.set_ylabel('pulse')
ax1.set_xlabel('time [sec]')
ax1.set_title('pulse vs time for both forks')
ax1.scatter(A.rawdata1[0],A.rawdata1[4],color='green', s=0.5)
plt.grid()
plt.show()
#print(A)
#print(np.shape(A.rawdata1),np.shape(A.rawdata2))
#print(A.rawdata1[4][A.pulse_id[50]-1],A.rawdata1[4][A.pulse_id[50]])
#print(A.rawdata1[3][A.pulse_id[2]-1],A.rawdata1[3][A.pulse_id[2]])
#for ii in A.pulse_id:
#    print(ii)
A.close_f()
del A
#B=timetotemp(conf,sett2)
#B.pulse_renumb()
#B.close_f()
#del B
#
#C=timetotemp(conf,sett3)
#C.pulse_renumb()
#C.close_f()
#del C