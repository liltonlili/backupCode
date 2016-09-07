#coding:utf-8
import pandas as pd
import os
import pymongo

# 将add.csv的股票写到mongo中，作为我挑选出来的股票列表

dir = u"D:/Money/lilton_code/Market_Mode/rocketup/全概念"
oriCsv = os.path.join(dir, "LED.csv")
oriFrame = pd.read_csv(oriCsv, encoding='gbk')
mongo_url = "localhost"
mongodb = pymongo.MongoClient(mongo_url)

concept_name = u'LED'
for index in oriFrame.index.values:
    try:
        stockid = oriFrame.loc[index, "stockid"]
        stockid = "0" * (6-len(str(stockid))) + str(stockid)
        stockid = stockid.decode("utf-8")
        name = oriFrame.loc[index, "name"]
        reason = oriFrame.loc[index, 'reason']
        zt_num = int(oriFrame.loc[index, 'zt_num'])
        dt_num = int(oriFrame.loc[index, 'dt_num'])
        print stockid
        mongodb.stock.myconcept.update({"stockid":stockid, "concept":concept_name},
                                       {"$set":{"reason":reason, "zt_num":zt_num, "dt_num":dt_num, "name":name}}, True, True, True)
    except Exception,err:
        print err