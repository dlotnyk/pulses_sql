# -*- coding: utf-8 -*-
"""
Created on Sat Nov  3 00:25:11 2018

@author: dlotnyk
Create SQL database of pulsing data including create reruired tables (and dropping), 
read data from .dat files and inserting values into SQL table, check if value is nan and replace it with NULL.
Timer and log decorators are used to measure processing time and log commands into 'work.log'

"""
from __future__ import print_function
import mysql.connector as conn
import numpy as np
from mysql.connector import errorcode
from functools import wraps

class sql_create():
    '''create data for pulses'''
    def __init__(self):
        self.tc=[0.929,1.013,2.293] # list of Tc for experiments
        self.tables=[('hec_0bar','ic_0bar'),('hec_9psi','ic_9psi'),('hec_22bar','ic_22bar')]
        
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

    def my_logger(orig_func):
        '''Decorate function to write into log on the level ERROR'''
        import logging
        import datetime
        logging.basicConfig(filename='work.log'.format(orig_func.__name__), level=logging.ERROR)
        
        @wraps(orig_func)
        def wrapper(*args,**kwargs):
            dt=datetime.datetime.now()
            dt_str=str(dt)
            vrema=dt_str.split('.')[0]
            logging.info(
                    ' {} Ran with args: {}, and kwargs: {} \n'.format(vrema, args, kwargs))
            return orig_func(*args, **kwargs) 
        return wrapper 
    
    @my_logger  
    @time_this
    def connect_f(self,conf):
        '''connect to mysql server'''
        assert type(conf) is dict, "Input parameter should be dict!!!"
        self.db_name=conf['database']
        self.cnx = None
        try:
            self.cnx = conn.connect(**conf)
            self.cursor = self.cnx.cursor()
            print('CONNECTED CLOUD!!!!')
        except conn.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
            if self.cnx:
                self.cnx.close() 
    
    @my_logger  
    @time_this
    def close_f(self):
        '''close connection'''
        self.cursor.close()
        self.cnx.close()
        print('Disconnected!')
    
    @my_logger  
    @time_this
    def create_table(self,tb_name1,tb_name2):
        '''create a table with tb_name name'''
#        CREATE TABLE `test1`.`some2` ( `fir` DOUBLE NOT NULL , `sec` DOUBLE NULL , `thir` DOUBLE NULL , `four` DOUBLE NOT NULL , PRIMARY KEY (`fir`), FOREIGN KEY (`four`) REFERENCES `test1`.`some`(`fir`)) ENGINE = InnoDB
#        ID int NOT NULL UNIQUE,
        assert type(tb_name1) is str or type(tb_name2) is str, "table name should be str"
        table_HEC=("CREATE TABLE `{}` ("
                         "  `index` int NOT NULL UNIQUE AUTO_INCREMENT COMMENT 'index',"
                         "  `time` DOUBLE NOT NULL UNIQUE COMMENT 'universal time [sec]',"
                         "  `Q` DOUBLE NULL COMMENT 'quality factor',"
                         "  `Inf_Freq` DOUBLE NULL COMMENT 'calculated frequency [HZ]',"
                         "  `Tmc` DOUBLE NULL COMMENT 'Melting curve temperature [mK]',"
                         "  `Tmc/Tc` DOUBLE NOT NULL COMMENT 'Tmc over Tc',"
                         "  `Tloc` DOUBLE NOT NULL COMMENT 'Local chamber temperature [mK]',"
                         "  `Tloc/Tc` DOUBLE NOT NULL COMMENT 'Tloc over Tc',"
                         "  `pulse` DOUBLE NOT NULL COMMENT 'number of pulse',"
                         "  KEY id (`index`),"
                         "  PRIMARY KEY (`pulse`)"
                         ") ENGINE=InnoDB".format(tb_name1))
        try:
            print("Creating table for HEC {}: ".format(tb_name1), end='')
            self.cursor.execute(table_HEC)
        except conn.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("HEC table already exists.")
            else:
                print(err.msg)
        else:
            print("OK")
        table_IC=("CREATE TABLE `{}` ("
                         "  `index` int NOT NULL AUTO_INCREMENT COMMENT 'index',"
                         "  `time` DOUBLE NOT NULL UNIQUE COMMENT 'universal time [sec]',"
                         "  `Q` DOUBLE NULL COMMENT 'quality factor',"
                         "  `Inf_Freq` DOUBLE NULL COMMENT 'calculated frequency [HZ]',"
                         "  `Tmc` DOUBLE NULL COMMENT 'Melting curve temperature [mK]',"
                         "  `Tmc/Tc` DOUBLE NOT NULL COMMENT 'Tmc over Tc',"
                         "  `Tloc` DOUBLE NOT NULL COMMENT 'Local chamber temperature [mK]',"
                         "  `Tloc/Tc` DOUBLE NOT NULL COMMENT 'Tloc over Tc',"
                         "  `pulse` DOUBLE NOT NULL UNIQUE COMMENT 'number of pulse',"
                         "  PRIMARY KEY (`index`),"
                         "  FOREIGN KEY (`pulse`) REFERENCES `{}`.`{}`(`pulse`) ON UPDATE CASCADE"
                         ") ENGINE=InnoDB".format(tb_name2,self.db_name,tb_name1))  
#        print(table_IC)
        try:
            print("Creating table for IC {}: ".format(tb_name2), end='')
            self.cursor.execute(table_IC)
        except conn.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("IC table already exists.")
            else:
                print(err.msg)
        else:
            print("OK")   
    
    @my_logger  
    @time_this    
    def drop_f(self,tb_name):
        '''delete tables in tb_name dictionary'''
        assert type(tb_name) is dict
        dis_fk=("SET foreign_key_checks = 0")
        self.cursor.execute(dis_fk)
        for k,v in tb_name.items():
            p=v['tables'] 
            table_IC=("DROP TABLE IF EXISTS `{}`".format(p[1]))
            try:
                print("Deleting table: ".format(tb_name), end='')
                self.cursor.execute(table_IC)  
            except conn.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("IC table already exists.")
                else:
                    print(err.msg)
            else:
                print("OK") 
            table_HEC=("DROP TABLE `{}`".format(p[0]))
            try:
                print("Deleting table: ".format(p[0]), end='')
                self.cursor.execute(table_HEC)  
            except conn.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("HEC table already exists.")
                else:
                    print(err.msg)
            else:
                print("OK") 
    
    def insert_sql(self,tab_name1,tab_name2,val1,val2):
        '''insert values in row imported in insert_values function into sql tables tab_name1 and tab_name2'''
        assert type(tab_name1) is str and type(tab_name2) is str, "Table name should be str"
        assert type(val1) is tuple and type(val2) is tuple, "values should be combined into tuples"
        add_row1 = ("INSERT INTO "+tab_name1+" "
                   "(`time`, `Q`, `Inf_Freq`, `Tmc`, `Tmc/Tc`, `Tloc`, `Tloc/Tc`, `pulse`) "
                   "VALUES ( %s, %s, %s, %s, 0, 0, 0, %s)" % val1) 
        add_row2 = ("INSERT INTO "+tab_name2+" "
                   "(`time`, `Q`, `Inf_Freq`, `Tmc`, `Tmc/Tc`, `Tloc`, `Tloc/Tc`, `pulse`) "
                   "VALUES (%s, %s, %s, %s, 0, 0, 0, %s)" % val2) 
        try: 
            self.cursor.execute(add_row1)
            self.cursor.execute(add_row2)
        except conn.Error as err:
            print(err.msg)
    
    @my_logger  
    @time_this 
    def insert_tables(self,d_value):
        '''insert valueus to sql tables imported from .dat files for single pressure.
        Replace nan with NULL'''
        assert type(d_value) is dict
        path1=d_value['path1']
        path2=d_value['path2']
        # truncate
        trun1=("ALTER TABLE {} AUTO_INCREMENT = 1".format(d_value['tables'][0]))
        trun2=("ALTER TABLE {} AUTO_INCREMENT = 1".format(d_value['tables'][1]))
        self.cursor.execute(trun1)
        self.cursor.execute(trun2)
        counter=0
        # HEC 0 bar
        print('Start import...')
        for p in path1:
            data=np.genfromtxt(p, unpack=True, skip_header=1, usecols = (2, 6, 7, 13))
            if counter == 0:
                data1=data.copy()
                counter += 1
            else:
                data1=np.concatenate((data1,data),axis=1)
        # IC 0 bar
        counter=0
        for p1 in path2:
            data21=np.genfromtxt(p1, unpack=True, skip_header=1, usecols = (2, 6, 7, 13))
            if counter == 0:
                data2=data21.copy()
                counter += 1
            else:
                data2=np.concatenate((data2,data21),axis=1)
        t0=data2[0][0]
        data2[0]=data2[0]-t0
        data1[0]=data1[0]-t0
        counter = 0
        for kk in range(np.shape(data2)[1]):            
            val=data1[:,kk]
            val21=data2[:,kk]
            val11=[]
            for ii in val:
                if np.isnan(ii):
                    val11.append('NULL')
                else:
                    val11.append(str(ii))
            val11.append(counter)
            val1=tuple(map(str,val11))
            val22=[]
            for jj in val21:
                if np.isnan(jj):
                    val22.append('NULL')
                else:
                    val22.append(str(jj))
            val22.append(counter)
            val2=tuple(map(str,val22))
            self.insert_sql(d_value['tables'][0],d_value['tables'][1],val1,val2)
            counter +=1
        self.cnx.commit()
        tab1_count=("SELECT COUNT(`index`) FROM `{}`".format(d_value['tables'][0]))
        tab2_count=("SELECT COUNT(`index`) FROM `{}`".format(d_value['tables'][1]))
        self.cursor.execute(tab1_count)
        res1=self.cursor.fetchall()
        self.cursor.execute(tab2_count)
        res2=self.cursor.fetchall()
        print('Writing ends')
        assert res1[0][0] == counter and res2[0][0] == counter, "dimentions of SQL tables and import table are missmatched"  
    
# ------------------------------------------------------------
conf = {
        'user': 'dlotnyk',
        'password': 'RiDeaBiKe2RuN',
        'host': '127.0.0.1',
        'database': 'pulses_he3',
        'raise_on_warnings': True,
        }
forks={'0bar':{'path1':["CF_0bar_01.dat","CF_0bar_02.dat","CF_0bar_03.dat"],
               'path2':["FF_0bar_01.dat","FF_0bar_02.dat","FF_0bar_03.dat"],
               'tables':('hec_0bar','ic_0bar')
               },
        '9psi':{'path1':["CF_9psi_01.dat","CF_9psi_02.dat","CF_9psi_03.dat"],
                'path2':["FF_9psi_01.dat","FF_9psi_02.dat","FF_9psi_03.dat"],
                'tables':('hec_9psi','ic_9psi')
                },
        '22bar':{'path1':["CF_22bar_01.dat","CF_22bar_02.dat"],
                 'path2':["FF_22bar_01.dat","FF_22bar_02.dat"],
                 'tables':('hec_22bar','ic_22bar')
                }           
       }
#A=sql_create()
#A.connect_f(conf)
##A.drop_f(forks)
##for k,v in forks.items():
##    A.create_table(v['tables'][0],v['tables'][1])
##    A.insert_tables(v)
#A.close_f()