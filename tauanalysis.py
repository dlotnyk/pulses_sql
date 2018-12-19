# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 11:05:06 2018

@author: dmytr
"""
from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as ss
#import os
#import shutil
#from functools import wraps
#import sys
#import time as e_t
#from mpl_toolkits.mplot3d import Axes3D
import warnings
warnings.simplefilter('ignore', np.RankWarning)
from createdata import sql_create as sqdata
from createdata import time_this
from createdata import my_logger

#-------------------------------------
class timetotemp(sqdata):
    vals=['time','Q','Tmc','index','pulse'] # the most important columns
    plimit=1500 # value in Q which identify the pulsing
#---------------------------------------------------------
    def __init__(self,conf,sett):
        '''connect to conn mysql server with data'''
        self.conf=conf
        self.sett=sett
        self.title=sett['pressure']
        self.connect_f(conf)
        assert self.sett['indent'] >= 0, "cut from begin. it should be > 0"
        assert self.sett['cut'] > self.sett['indent'] >= 0, "cut always greater than indent"
        assert self.sett['offset'] >= 0, "offset it should be > 0"
#---------------------------------------------------------         
    def __repr__(self):
        return str(self.__class__.__name__)+" "+str(self.sett['pressure'])+", db: "+str(self.conf['database'])

#----------------------------------------------------------- 
    @my_logger  
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
        return data13,data23
#---------------------------------------------------------    
    @my_logger  
    @time_this
    def pulse_indicies(self,data1,data2):
        '''Find pulses in IC fork'''
        a=np.where(np.abs(data2[1])>self.plimit)
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
        return pul
#---------------------------------------------------------    
    @my_logger  
    @time_this
    def pulse_renumb(self,data2):
        '''renumber of pulses and update in sql. start from mval and 1000 per each pulse'''

        ini=self.mval
        pul_id=0
        id1=0
        id2=self.pulse_id[0]
        increm=1000/(id2-id1)
        count=0
        nump=1
        for ii in data2[3]:
            if ii == data2[3][self.pulse_id[pul_id]]:
#                print(pul_id, self.pulse_id[pul_id])
                pul_id += 1
                if pul_id == np.shape(self.pulse_id)[0]:
                    id1=self.pulse_id[pul_id-1]
                    id2=np.shape(data2)[1]
                    pul_id-=1                    
                else:
                    id1=self.pulse_id[pul_id-1]
                    id2=self.pulse_id[pul_id]
                increm=1000/(id2-id1)
#                self.rawdata1[4][count]=self.mval+1000*nump
                self.__set_pulse(self.sett['indent']+count+1,self.mval+1000*nump)
                nump+=1
            else:
#                self.rawdata1[4][count]=ini
                self.__set_pulse(self.sett['indent']+count+1,ini)
            count+=1
            ini+=increm
        self.cnx.commit()  
#-----------------------------------------------------------
    @my_logger  
    @time_this     
    def __pulse_st(self):
        '''Find the maximum value of `pulse` during the first start'''
        tab1_count=("SELECT COUNT(`index`) FROM `{}`".format(self.tables[self.sett['pressure']][0]))
        self.cursor.execute(tab1_count)
        res1=self.cursor.fetchall() 
        b=str(res1[0][0])
        self.mval=round(res1[0][0],-len(b)+1)+10**(len(b)-1) # value grater than index. starting point for new pulsing data
 #---------------------------------------------------------  
    @my_logger
    @time_this
    def first_start(self):
        '''command sequence of the program after creating tables in sql create class'''
        data_hec,data_ic=self.import_fun()
        self.pulse_id=self.pulse_indicies(data_hec,data_ic)
        self.pulse_renumb(data_ic)  
#        self.pulse_remove2(data_hec,data_ic)
 #---------------------------------------------------------             
    def __set_pulse(self,ind,val):
        '''update a value of `pulse` in a HEC table. it is a primary key bonded with IC'''
        set_v=("UPDATE `{0}` SET `pulse` = '{1}' WHERE `{0}`.`index` = '{2}'".format(self.tables[self.sett['pressure']][0],val,int(ind)))
        self.cursor.execute(set_v)

#--------------------------------------------------------------------------------------------------    
    @my_logger
    @time_this
    def sel_onlypulse(self,r_list,tab):
        '''select data only with pulses i.e. 70000 and higher `pulse`'''
        self.__pulse_st()
        cur=''
        for ii in r_list:
            cur+="`"+ii+"`, "
        cur=cur[0:-2]
        query=("SELECT "+cur+" FROM `{0}` WHERE `pulse` > '{1}' ORDER BY `{0}`.`index` ASC".format(tab,str(self.mval)))
        self.cursor.execute(query)
        res=self.cursor.fetchall()
        dat=self._removeNull(res)
        dat1=np.transpose(dat)
        return dat1
 #---------------------------------------------------------  
    @my_logger
    @time_this
    def sel_onlypulseJoin(self,r_list1,tab1,r_list2,tab2):
        '''select data only with pulses i.e. 70000 and higher `pulse` JOIN two tables by `pulse`'''
        assert type(r_list1) is list and type(tab1) is str, "HEC data not list or string"
        assert type(r_list2) is list and type(tab2) is str, "IC data not list or string"
        self.__pulse_st()
        cur1=''
        for ii in r_list1:
            cur1+="`"+str(tab1)+"`.`"+ii+"`, "
        cur1=cur1[0:-2]
        cur2=''
        for jj in r_list2:
            cur2+="`"+str(tab2)+"`.`"+jj+"`, "
        cur2=cur2[0:-2]
        query=("SELECT "+cur1+", "+cur2+
               " FROM `{0}` JOIN `{1}` "
               "ON `{0}`.`pulse` = `{1}`.`pulse` "
               "WHERE `{0}`.`pulse` > '{2}' ORDER BY `{0}`.`index` ASC".format(tab1,tab2,str(self.mval)))
#        print(query)
        self.cursor.execute(query)
        res=self.cursor.fetchall()
        dat=self._removeNull(res)
        dat1=np.transpose(dat)
        return dat1
 #---------------------------------------------------------  
    @my_logger  
    @time_this    
    def pulse_remove(self,n1,n2,data1,data2):
        '''Remove pulse and n1/n2-surroundings'''
        a=range(-n1,n2)
        b=np.where(np.abs(data2[1])>self.plimit)
        s=[]
        for p in np.nditer(self.pulse_id):
            for ad in np.nditer(a):
                s.append(ad+p)
        pulse_rem=np.asarray(s)
        d1=np.in1d(range(0,len(data1[1])),pulse_rem,assume_unique=True,invert = True)
        d2=np.in1d(range(0,len(data2[1])),pulse_rem,assume_unique=True,invert = True)
#        new_in=self.pulse_remove2(b)
#        print(new_in)
#        self.cnx.commit()!
        self.__remInsq(d1,b)
        self.cnx.commit()
        return d1,d2
 #---------------------------------------------------------  
    @my_logger  
    @time_this    
    def pulse_remove2(self,a):
        '''Remove pulse and n1/n2-surroundings'''
#        a=np.where(np.abs(data2[1])>self.plimit)
#        print(a[0],end=' ')
        new_in=-1
        for idx in a[0]:            
            self.__set_pulse(self.sett['indent']+idx+2,new_in)
            new_in -= 1
        self.cnx.commit()
        return new_in

#------------------------------------------------------------
    def __remInsq(self,d1,b):
        '''update `pulse` values in table according to removing pulse'''
        new_in=-1
#        print(245 in b[0])
        for idx, ni in enumerate(d1):
            if (ni==False) or (idx in b[0]):
                self.__set_pulse(self.sett['indent']+idx+2,new_in)
                new_in -=1
    
#------------------------------------------------------------
    @my_logger
    @time_this
    def temp_fit(self,nump):
        '''nump - polyfit regression fit of temperature data, removing nan first'''
        res=self.sel_onlypulse(['time','Tmc','index'],self.tables[self.sett['pressure']][0])
        na=np.where(np.isnan(res[1]))
        sh=np.shape(res)[1]
        d1=np.in1d(range(0,sh),na,invert = True)
        w=np.ones(sh)
        w[int(sh/2):]=2
        fit = np.polyfit(res[0][d1],res[1][d1],nump,w=w[d1])
        fit_fn = np.poly1d(fit) 
        temp2=fit_fn(res[0])
        dt=self.tc[self.sett['pressure']]-np.mean(temp2[-30:-1]) #correction to tc
        fit[-1]+=dt
        temp2=fit_fn(res[0][d1])
        fit_rev=np.polyfit(temp2,res[0][d1],nump)
#        timeRev=np.poly1d(fit_rev)
        for idx,y in enumerate(fit_fn(res[0])):
            s_com1=("UPDATE `{0}` SET `Tmc` = '{1}' WHERE `{0}`.`index` = '{2}'".format(self.tables[self.sett['pressure']][0],y,res[2][idx]))
#            s_com2=("UPDATE `{0}` SET `Tmc` = '{1}' WHERE `{0}`.`index` = '{2}'".format(self.tables[self.sett['pressure']][1],y,res[2][idx]))
            self.cursor.execute(s_com1)
#            self.cursor.execute(s_com2)
        self.cnx.commit()
#        print(s_com1)
#        print(s_com2)
        fig1 = plt.figure(7, clear = True)
        ax1 = fig1.add_subplot(111)
        ax1.set_ylabel('T')
        ax1.set_xlabel('time')
        ax1.set_title('T and time')
        ax1.plot(res[0][d1], res[1][d1], color='green',lw=1)
        ax1.plot(res[0][d1], fit_fn(res[0][d1]), color='blue',lw=1)
        plt.grid()
        plt.show()
        return fit,fit_rev
    
 #------------------------------------------------------------
    @my_logger
    @time_this
    def QtoT(self,nump):   
        '''Transformation of Q into Temperature based on HEC Fork
        nump - degree of polyfit'''
        assert type(nump) is int,"Must be integer"
        res=self.sel_onlypulse(['Q','Tmc','index','time'],self.tables[self.sett['pressure']][0])
        filt=ss.medfilt(res[0],21)
        w=np.ones(len(res[0]))
        w[0:100]=15
        w[-100:-1]=15
        fit = np.polyfit(res[1],filt,nump,w=w) # T vs Q first
        fit_fn = np.poly1d(fit) # Q
        Q=fit_fn(res[1])
        fit2 = np.polyfit(Q,res[1],nump,w=w) # Q vs T fit. main one
        fit_fn2 = np.poly1d(fit2) # T
#        T=fit_fn2(Q)
       
        fig1 = plt.figure(8, clear = True)
        ax1 = fig1.add_subplot(211)
        ax1.set_ylabel('Q')
        ax1.set_xlabel('T')
        ax1.set_title('Q vs T')
        ax1.plot(res[1], res[0], color='blue',lw=1)
        ax1.plot(res[1],Q, color='red',lw=1)
        ax1.plot(res[1],filt, color='green',lw=1)
        plt.grid()
        ax2 = fig1.add_subplot(212)
        ax2.set_ylabel('T/Tc')
        ax2.set_xlabel('time')
        ax2.set_title('T/Tc vs Q')
        ax2.plot(res[3], fit_fn2(res[0])/self.tc[self.sett['pressure']], color='blue',lw=1)
#        ax2.plot(Q,T, color='red',lw=1)
#        ax2.plot(filt,res[1], color='green',lw=1)
        
        plt.grid()
        plt.show()
#        dat=np.vstack((filt,T))
        return fit2
    #------------------------------------------------------------
    def QtoTic(self,fit):
        '''Converts Q to temp for an IC fork using calibration from HEC'''
        fit_fn=np.poly1d(fit)
        res=self.sel_onlypulseJoin(['Q'],self.tables[self.sett['pressure']][0],['Q','Tmc','index','time'],self.tables[self.sett['pressure']][1])
        # connect two datasets in the end taking into account hte offset
        Q1=np.mean(res[1][-10:-1])
        Q2=np.mean(res[0][-10:-1])
        dQ=Q1-Q2 # correction to Q
        print(Q1,Q2,dQ)
        
        
 #------------------------------------------------------------
    @my_logger
    @time_this
    def update_local(self,tab,fit):
        assert type(tab) is str,'Table is string'
        assert type(fit) is np.ndarray,"fit is numpy.ndarray"
        fit_fn=np.poly1d(fit)
        res=self.sel_onlypulse(['Q','index'],self.tables[self.sett['pressure']][0])
         # update a SQL table
        for idx,val in enumerate(res[0]):
            self.__set_local(tab,res[1][idx],fit_fn(val),fit_fn(val)/self.tc[self.sett['pressure']])
        self.cnx.commit()
        
 #------------------------------------------------------------        
    def __set_local(self,tab,index,value1,value2):
        '''set value in the SQL table tab with index index and value1 is loc, value2 is Tloc/Tc'''
        s_com1=("UPDATE `{0}` SET `Tloc` = '{1}' WHERE `{0}`.`index` = '{2}'".format(tab,value1,index))
        s_com2=("UPDATE `{0}` SET `Tloc/Tc` = '{1}' WHERE `{0}`.`index` = '{2}'".format(tab,value2,index))
        self.cursor.execute(s_com1)
        self.cursor.execute(s_com2)
        
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
#A.first_start()
#data1=A.sel_onlypulse(['time','Q','Tmc','index','pulse'],A.tables[A.sett['pressure']][0])
#data2=A.sel_onlypulse(['time','Q','Tmc','index'],A.tables[A.sett['pressure']][1])
##A.nopulse1,A.nopulse2=A.pulse_remove(15,35,data1,data2) # for 0 bar
#A.nopulse1,A.nopulse2=A.pulse_remove(10,50,data1,data2) # for 9 psi and 22 bar
#del data1
#del data2
#f_lt,f_tl=A.temp_fit(1)
fit_qt=A.QtoT(10) # optimal for 0 bar
A.QtoTic(fit_qt)
#A.update_local(A.tables[A.sett['pressure']][0],fit_qt)
dataJ=A.sel_onlypulseJoin(['time','Q','Tloc/Tc','index','pulse'],A.tables[A.sett['pressure']][0],['Q'],A.tables[A.sett['pressure']][1])


fig1 = plt.figure(1, clear = True)
ax1 = fig1.add_subplot(211)
ax1.set_ylabel('Q')
ax1.set_xlabel('time [sec]')
ax1.set_title('Q vs time for both forks')
ax1.scatter(dataJ[0],dataJ[1],color='green', s=0.5)
ax1.scatter(dataJ[0],dataJ[5],color='red', s=0.5)
#ax1.scatter(C.rawdata1[0][C.nopulse1],C.rawdata1[1][C.nopulse1],color='red', s=0.5)
ax2 = fig1.add_subplot(212)
ax2.set_ylabel('T')
ax2.set_xlabel('time [sec]')
ax2.set_title('T vs time for both forks')
ax2.scatter(dataJ[0],dataJ[2],color='green', s=0.5)
#ax2.scatter(data2[0],data2[2],color='red', s=0.5)
plt.grid()
plt.show()

fig2 = plt.figure(2, clear = True)
ax1 = fig2.add_subplot(111)
ax1.set_ylabel('pulse')
ax1.set_xlabel('time [sec]')
ax1.set_title('pulse vs time for both forks')
ax1.scatter(dataJ[0],dataJ[4],color='green', s=0.5)
plt.grid()
plt.show()
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