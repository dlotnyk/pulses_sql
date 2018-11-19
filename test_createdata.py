# -*- coding: utf-8 -*-
"""
Created on Wed Nov 14 15:35:18 2018

@author: dlotnyk
Unittesting of createdaa.py
"""
from __future__ import print_function

import os
import unittest
import mysql.connector as conn
import numpy as np
from mysql.connector import errorcode
from createdata import sql_create
import warnings
warnings.simplefilter('ignore', np.RankWarning)
class TestCreatedata(unittest.TestCase):
    '''testing'''
    @classmethod
    def setUpClass(cls):
        cls.forks={'0bar':{'path1':["CF_0bar_01.dat","CF_0bar_02.dat","CF_0bar_03.dat"],
               'path2':["FF_0bar_01.dat","FF_0bar_02.dat","FF_0bar_03.dat"],
               'tables':('table1','table2')
               }}
        cls.tab_ch1=("SELECT * "
                "FROM information_schema.tables "
                "WHERE table_schema = 'test_s' " 
                "AND table_name = 'table1' "
                "LIMIT 1")
        cls.tab_ch2=("SELECT * "
                "FROM information_schema.tables "
                "WHERE table_schema = 'test_s' " 
                "AND table_name = 'table2' "
                "LIMIT 1")
    def setUp(self):
        '''connect to a empty testing database'''
        conf = {
        'user': 'dlotnyk',
        'password': 'RiDeaBiKe2RuN',
        'database': 'test_s',
        'host': '127.0.0.1',
        'raise_on_warnings': True,
        }
#       
        self.tinst=sql_create()
        self.tinst.connect_f(conf)
        self.tinst.drop_f(self.forks)
        print(' ')
                
    def tearDown(self):
        '''close connection'''
        self.tinst.close_f()
        del self.tinst
        print('Disconnected!')
    
    def test_createTable(self):
        self.tinst.create_table('table1','table2')
        self.tinst.cursor.execute(self.tab_ch1)
        res1=self.tinst.cursor.fetchall()
        self.tinst.cursor.execute(self.tab_ch2)
        res2=self.tinst.cursor.fetchall()
        tab_ch3=("SELECT * "
                "FROM information_schema.tables "
                "WHERE table_schema = 'test_s' " 
                "AND table_name = 'table3' "
                "LIMIT 1")
        self.tinst.cursor.execute(tab_ch3)
        res3=self.tinst.cursor.fetchall()
        self.assertEqual(len(res1),1,'can not create a table')
        self.assertEqual(len(res2),1,'can not create a table')
        self.assertEqual(len(res3),0,'somethin is really wrong. a table exists which can not exist at all')
    
    def test_DropTable(self):
        self.tinst.create_table('table1','table2')
        # create tables
        self.tinst.cursor.execute(self.tab_ch1)
        res1=self.tinst.cursor.fetchall()
        self.tinst.cursor.execute(self.tab_ch2)
        res2=self.tinst.cursor.fetchall()
        #check
        self.assertEqual(len(res1),1,'can not create a table')
        self.assertEqual(len(res2),1,'can not create a table')
        #drop tables
        self.tinst.drop_f(self.forks)
        self.tinst.cursor.execute(self.tab_ch1)
        res3=self.tinst.cursor.fetchall()
        self.tinst.cursor.execute(self.tab_ch2)
        res4=self.tinst.cursor.fetchall()
        self.assertEqual(len(res3),0,'can not drop a table')
        self.assertEqual(len(res4),0,'can not drop a table')
        
    def test_InsertTables(self):
        self.tinst.create_table('table1','table2')
        

if __name__ == '__main__':
    unittest.main()
