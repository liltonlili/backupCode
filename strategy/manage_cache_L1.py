# coding:utf-8
import best_hit
import pandas as pd
import datetime as dt
import pymongo
import os

'''
该文件用来管理L1，具体功能为：
1. 之前会在每日复盘中生成L1.csv
2. 该代码会读取L1.csv，然后对L1进行删减操作
3. 后续可以将第二天监控的概念板块加入，在L1.csv指定第二日管理的板块，然后更新到mongo中
'''

mongodb = pymongo.MongoClient("localhost")

today = dt.datetime.today().strftime("%Y%m%d")
result = mongodb.stock.ZDT_by_date.find({"date":{"$lte":today}}).sort("date", pymongo.DESCENDING)[0]
save_dir_name = result['date']
constant_dir = u'D:/Money/modeResee/复盘'
save_dir = u"%s/%s" %(constant_dir, save_dir_name)
csv_file = os.path.join(save_dir, 'L1.csv')

cacheL = best_hit.HitBest()
cacheL.update_L1_from_generated_csv(csv_file)