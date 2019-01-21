# -*- coding: utf-8 -*-
"""
Created on Mon Jan 14 00:06:43 2019

@author: dlotnyk
Unittesting of tauanalysis.py
"""
from __future__ import print_function
import unittest
import numpy as np
from tauanalysis import timetotemp
import warnings
warnings.simplefilter('ignore', np.RankWarning)
warnings.filterwarnings("ignore", message="Reloaded modules: <chromosome_length>")
class TestTauanalysis(unittest.TestCase):
    '''testing of tauanalysis.py'''
    
if __name__ == '__main__':
    unittest.main()