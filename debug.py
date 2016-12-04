#coding:utf-8
import cv2
import numpy as np
import requests as rq
import tushare as ts
import time
import datetime
import common
import pandas as pd

stock = ['603060', '603322', '603060']
day = '20161202'
tmp_dframe = common.get_dataframe_option1(stock, day)
common.get_html_curve([tmp_dframe], "complex_html", html_types=[1], title_list=[u'测试'])

