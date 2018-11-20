# -*- coding: utf-8 -*-
"""
Created on Wed Nov 14 15:35:18 2018

@author: dlotnyk
Unittesting of createdaa.py
"""
from __future__ import print_function
import unittest
import numpy as np
from createdata import sql_create
import warnings
warnings.simplefilter('ignore', np.RankWarning)
class TestCreatedata(unittest.TestCase):
    '''testing'''
    @classmethod
    def setUpClass(cls):
        cls.forks={'0bar':{'path1':["CF_0bar_01.dat"],
               'path2':["FF_0bar_01.dat"],
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
        a=int(0)
        b=int(1)
        with self.assertRaises(AssertionError):
            self.tinst.create_table(a,'table2')
            self.tinst.create_table('table1',b)
            self.tinst.create_table(a,b)
        
    
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
        a='table'
        d={'a':2}
        with self.assertRaises(AssertionError):
            self.tinst.drop_f(a)
            self.tinst.drop_f(d)
        self.tinst.drop_f(self.forks)
        self.tinst.cursor.execute(self.tab_ch1)
        res3=self.tinst.cursor.fetchall()
        self.tinst.cursor.execute(self.tab_ch2)
        res4=self.tinst.cursor.fetchall()
        self.assertEqual(len(res3),0,'can not drop a table')
        self.assertEqual(len(res4),0,'can not drop a table')
        
    def test_InsertTables(self):
        self.tinst.create_table('table1','table2')
        self.tinst.insert_tables(self.forks['0bar'])
        tab1_count=("SELECT COUNT(`index`) FROM `{}`".format(self.forks['0bar']['tables'][0]))
        tab2_count=("SELECT COUNT(`index`) FROM `{}`".format(self.forks['0bar']['tables'][1]))
        self.tinst.cursor.execute(tab1_count)
        res1=self.tinst.cursor.fetchall()
        self.tinst.cursor.execute(tab2_count)
        res2=self.tinst.cursor.fetchall()
        val1=("SELECT `Q` FROM `{}` WHERE `index` = 1".format(self.forks['0bar']['tables'][1]))
        self.tinst.cursor.execute(val1)
        res3=self.tinst.cursor.fetchall()
        val2=("SELECT `Q` FROM `{}` WHERE `index` = 1".format(self.forks['0bar']['tables'][0]))
        self.tinst.cursor.execute(val2)
        res4=self.tinst.cursor.fetchall()
        val3=("SELECT `Q` FROM `{}` WHERE `index` = 20451".format(self.forks['0bar']['tables'][1]))
        self.tinst.cursor.execute(val3)
        res5=self.tinst.cursor.fetchall()
        val4=("SELECT `Q` FROM `{}` WHERE `index` = 20451".format(self.forks['0bar']['tables'][0]))
        self.tinst.cursor.execute(val4)
        res6=self.tinst.cursor.fetchall()
        self.assertEqual(res1[0][0],res2[0][0],'numbers of rows in tables should be equal')
        self.assertEqual(res1[0][0],20451,'some data are missing during SQL insert prcedure')
        self.assertAlmostEqual(res3[0][0], 41.65548, 2, 'wrong first data import into IC table')
        self.assertAlmostEqual(res4[0][0], 37.32284, 2, 'wrong first data import into HEC table')
        self.assertAlmostEqual(res5[0][0], 55.47477, 2, 'wrong last data import into IC table')
        self.assertAlmostEqual(res6[0][0], 51.01369, 2, 'wrong last data import into HEC table')
        a=[2,3,'a'] # should be a dict
        b={1:[1,2,3],2:(0,1,2),3:[3,5,6]} # 3 - is tuple
        with self.assertRaises(AssertionError):
            self.tinst.insert_tables(a)
            self.tinst.insert_tables(b)

if __name__ == '__main__':
    unittest.main()
