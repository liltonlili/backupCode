#coding:utf-8
import cv2
import numpy as np
import requests as rq
import tushare as ts
import time
import datetime
import common

print common.get_hit_status("300553", "20161117")
print common.get_hit_status("603258", "20161117")
print common.get_hit_status("603667", "20161114")   # True

ts.get_stock_basics()
# print common.get_day_k_status("002436", "20161111")
# print common.get_day_k_status("000020", "20161111")