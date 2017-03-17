#coding:utf-8
import cv2
import numpy as np
import requests as rq
import tushare as ts
import time
import datetime
import common
import pandas as pd
import pymongo
import os
import shutil
import sys
sys.path.append("./strategy")
import intelligent_eye
import tushare as ts
import urllib2
import urllib
import os
import copy
import shutil

print common.get_mongoDicts(dateStart="2016-10-20",dateEnd="2017-03-10").count()
# shutil.move
# today = "20161230"
# mongodb = pymongo.MongoClient('localhost')
# results = mongodb.stock.ZDT_by_date.find({"date":{"$gte":"20161010"}})
# csv_dir = u'D:/Money/modeResee/复盘'
# for result in results:
#     day = result['date']
#     csv_file = os.path.join(csv_dir, "%s/daydayup.csv" % day)
#     dframe = pd.read_csv(csv_file, encoding='gbk')
#     dframe.dropna(subset=['stock'], inplace=True)
#     columns = copy.deepcopy(dframe.columns)
#     # if u'type' not in columns:
#     #     continue
#     for idx in dframe.index.values:
#         stockid = dframe.loc[idx, 'stock']
#         stockid = common.regulize_stockid(stockid)
#         status = ''
#         change_rate, close_zt_status, close_dt_status, high_zt_status, low_dt_status = common.get_day_k_status(stockid, day)
#         status_list = [close_zt_status, close_dt_status, high_zt_status]
#         type_list = ['ZT', 'DT', 'HD']
#         if u'type' in columns and dframe.loc[idx, 'type'] == dframe.loc[idx, 'type'] and len(dframe.loc[idx, 'type']) >0:
#             continue
#         if True in status_list:
#             status = type_list[status_list.index(True)]
#         else:
#             print "not find match for %s, %s" % (stockid, day)
#             continue
#         dframe.loc[idx, 'type'] = status
#         print "%s, %s,  readd type, %s" % (day, stockid, status)
#     dframe.to_csv(csv_file, encoding='gbk')



# csv_dir = u'D:/Money/modeResee/复盘/网络复盘/凤凰/extract'
# target_dir = u'D:/Money/modeResee/复盘'
# current_dir_list = os.listdir(target_dir)
# results = mongodb.stock.ZDT_by_date.find({"date":{"$gte":"20161010"}})
# for result in results:
#     date = result['date']
#     date = common.format_date(date, "%Y%m%d")
#     x = intelligent_eye.IntelliGentEye(day = date)
#     x.scan()

# 将凤凰的文件转到各个文件夹下面
# for result in results:
#     date = result['date']
#     date = common.format_date(date, "%Y%m%d")
#     scan_dir = os.path.join(target_dir, date)
#     print date
#     if date not in current_dir_list:
#         print "will build folder %s" %date
#         os.makedirs(scan_dir)     #创建目录
#         shutil.copy(os.path.join(csv_dir, "%s.csv"%date), os.path.join(scan_dir, 'daydayup.csv'))
#     elif 'daydayup.csv' not in os.listdir(scan_dir):        # 存在目录，但是没有daydayup.csv
#         print 'will copy daydayup.csv'
#         shutil.copy(os.path.join(csv_dir, "%s.csv"%date), os.path.join(scan_dir, 'daydayup.csv'))
#     else:
#         print "already exists dir, and daydayup.csv"

# common.generate_html("20161221", "20161222")
# 将AR概念的，好几天都画到一张图中，最后生成一个html
# global mongodb
# stockids, stocknames = common.get_stockids_from_concept(u'AR')
#
# dates = ['20160711', '20160712', '20160713']
# common.get_html_curve1_multi_date(stockids, dates, u'C:/Users/li.li/Desktop/test', 'AR2')
# dframe_list = []
# title_list = []
# html_types = []
# for date in dates:
#     dframe = common.get_dataframe_option1(stockids, date)
#     dframe_list.append(dframe)
#     title_list.append(date)
#     html_types.append(1)
#
# common.get_html_curve(dframe_list, 'AR', html_types=html_types, title_list=title_list, save_dir=u'C:/Users/li.li/Desktop/test')
#


# print x



