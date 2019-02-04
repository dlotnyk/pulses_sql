# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 15:13:00 2019

@author: dmytr
"""
import math
cylinder={"radius":15,"height":5}
sq1=math.pi*cylinder["radius"]**2
volume=sq1*cylinder["height"]
sq_cyl=2*sq1+2*math.pi*cylinder["radius"]*cylinder["height"]
print(sq1,volume,sq_cyl)