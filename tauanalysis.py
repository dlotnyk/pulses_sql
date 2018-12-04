# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 11:05:06 2018

@author: dmytr
"""

import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as ss
import os
import shutil
#import sys
import time as e_t
from mpl_toolkits.mplot3d import Axes3D
import warnings
warnings.simplefilter('ignore', np.RankWarning)
from createdata import sql_create as sqdata

class timetotemp(sqdata):
    vals=['time','Q','Tmc','index','pulse']
    def __init__(self,conf,sett):
        '''connect to conn mysql server with data'''
#        self.set=nums[0]
#        assert self.set == 0 or self.set == 2 or self.set == 1, "wrong pressure chose"
#        self.num_exp=nums[1]
#        self.num1=nums[2]
#        assert self.num1 >= 0, "cut from begin. it should be > 0"
#        self.num2=nums[3]
#        self.offset=nums[4]
        self.connect_f(conf)
        self.sett=sett
        assert self.sett['indent'] >= 0, "cut from begin. it should be > 0"
        assert self.sett['cut'] > self.sett['indent'] >= 0, "cut always greater than indent"
        assert self.sett['offset'] >= 0, "offset it should be > 0"
        self.rawdata1,self.rawdata2=self.import_fun()
        self.pulse_id=self.pulse_indicies()
      
    def import_fun(self):
        '''select time,Q and Tmc data from database. slice later. could be improved with BETWEEN'''
        data1=self.select_col(self.vals,self.tables[self.sett['pressure']][0])
        data2=self.select_col(self.vals,self.tables[self.sett['pressure']][1])
        a=np.shape(data1)[0]
        b=str(a)
        self.mval=round(a,-len(b)+1)+10**(len(b)-1) # value grater than index. starting point for new pulsing data
        data1=data1[self.sett['indent']:self.sett['cut'],:]
        data2=data2[self.sett['indent']:self.sett['cut'],:]
        data2=data2[0:-self.sett['offset'],:]
        data1=np.transpose(data1)
        data2=np.transpose(data2)
        t0=data2[0][0]
        data1[0]=data1[0]-t0
        data2[0]=data2[0]-t0
        
        return data1,data2
    
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
        print(np.shape(pul))
        return pul
    
    def pulse_renumb(self):
        '''renumber of pulses and update in sql. start from mval and 1000 per each pulse'''
        ini=self.sett['indent']
#        for ii in self.pulse_id:
#            increm=(ii-ini)/1000
#            for jj 
#        
    def pulse_remove(self,n1,n2):
        '''Remove pulse and n-surroundings'''
        a=range(-n1,n1*n2)
        s=[]
        for p in np.nditer(self.pulseID):
            for ad in np.nditer(a):
                s.append(ad+p)
        pulse_rem=np.asarray(s)
        d1=np.in1d(range(0,len(self.rawdata1[1])),pulse_rem,assume_unique=True,invert = True)
        d2=np.in1d(range(0,len(self.rawdata2[1])),pulse_rem,assume_unique=True,invert = True)
        return d1,d2
        
#A=timetotemp(0,20,9200,47000,1800) # zero bar       
conf = {
        'user': 'dlotnyk',
        'password': 'RiDeaBiKe2RuN',
        'host': '127.0.0.1',
        'database': 'pulses_he3',
        'raise_on_warnings': True,
        }
sett1={'pressure':'0bar','indent':9200,'cut':47000,'offset':1800
       }

A=timetotemp(conf,sett1)


fig1 = plt.figure(1, clear = True)
ax1 = fig1.add_subplot(211)
ax1.set_ylabel('Q')
ax1.set_xlabel('time [sec]')
ax1.set_title('Q vs time for both forks')
ax1.scatter(A.rawdata1[0],A.rawdata1[1],color='green', s=0.5)
ax1.scatter(A.rawdata2[0],A.rawdata2[1],color='red', s=0.5)
#ax1.scatter(C.rawdata1[0][C.nopulse1],C.rawdata1[1][C.nopulse1],color='red', s=0.5)
ax2 = fig1.add_subplot(212)
ax2.set_ylabel('T')
ax2.set_xlabel('time [sec]')
ax2.set_title('T vs time for both forks')
ax2.scatter(A.rawdata1[0],A.rawdata1[2],color='green', s=0.5)
ax2.scatter(A.rawdata2[0],A.rawdata2[2],color='red', s=0.5)

plt.grid()
plt.show()
A.close_f()
print(A.rawdata1[3][A.pulse_id[0]],A.rawdata1[3][A.pulse_id[1]])
#del A
#print(A.tc[A.set])