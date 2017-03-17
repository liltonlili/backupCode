#coding:utf-8

'''
用来记录和管理强势概念，分为两级：
L2：由复盘记录的所有记录组成，当前只支持往里面添加股票
L1：最近值得关注的概念以及股票列表，每天更新, 暂时不支持L1操作
'''
import pandas as pd
import pymongo
import os
import time
import numpy as np
import sys
sys.path.append("D:/Money/lilton_code/Market_Mode/rocketup")
import common
import datetime
from pandas import DataFrame

class HitBest():
    def __init__(self):
        self.mongodb = pymongo.MongoClient("localhost")
        # self.updateL2Flag = 0 # L2强制刷新，为0的话，则为
        self.backsee_dir = u'D:/Money/modeResee/复盘'
        self.operationDay = datetime.datetime.today().strftime("%Y%m%d")   #更新数据库的日期

    # 根据复盘的csv更新L1/L2池
    def updateCacheFromCsv(self, start_date, end_date):
        start_date = common.format_date(start_date, "%Y%m%d")
        end_date = common.format_date(end_date, "%Y%m%d")
        results = self.mongodb.stock.ZDT_by_date.find({"date":{"$gte":start_date, "$lte":end_date}})
        # 获取指定日期之间的交易日期
        for result in results:
            date = result['date']
            print "updating L1/L2 from csv of date:%s ..." %date
            self.updateAnotationL2CsvByDate(date)
            self.updateCacheCsvByDate(date)

    # 之前的可能不支持（不包含anotation)
    # 根据某日的csv进行L2更新，会将anotation也归类到概念中
    def updateAnotationL2CsvByDate(self, date):
        # 读入daydayup.csv
        dframe = pd.read_csv(os.path.join(self.backsee_dir, u"%s/daydayup.csv" % date), encoding='gbk')
        dframe.dropna(subset= ['group'], inplace=True)
        for idx in dframe.index.values:
            concept = dframe.loc[idx, 'group']  # 概念
            # stockids = [dframe.loc[idx, 'stock']]
            stockids = []       # 不更新csv中stock列, 在另一个函数中更新
            try:
                if str(dframe.loc[idx, 'anotation']) == 'nan' or len(str(dframe.loc[idx, 'anotation'])) < 2:
                    anotation_stockids = []
                else:
                    anotations = dframe.loc[idx, 'anotation'].replace(u' ', u'').replace(u'，', u',').split(u',')
                    anotation_stockids = [common.QueryStockMap(name=x)[1] for x in anotations]
            except Exception, err:
                print "force to set the anotation stockids to be empty for concept:%s" %concept
                anotation_stockids = []
            stockids.extend(anotation_stockids)     # 该行中，概念相关的股票
            print "updating concept of:%s ..." %concept
            for stockid in stockids:
                self.insertCache(stockid, concept, date, cache=2)     # 往L2中添加股票及对应的概念


    # 根据某日的csv进行Cache更新，仅仅更新当日有记录的股票
    def updateCacheCsvByDate(self, date):
        # 读入daydayup.csv
        dframe = pd.read_csv(os.path.join(self.backsee_dir, u"%s/daydayup.csv" % date), encoding='gbk')
        for idx in dframe.index.values:
            concept = dframe.loc[idx, 'group']  # 概念
            stockid = dframe.loc[idx, 'stock']
            # print "Will update L1, %s" % stockid
            # L1
            inL1 = common.exist_in_cache(stockid, concept, 1)
            csv_inL1 = dframe.loc[idx, 'inL1']
            if csv_inL1 and not inL1:       # 需要插入L1
                self.insertCache(stockid, concept, date)
            elif inL1 and not csv_inL1:     # 需要从L1中删除
                self.removeCache(stockid, concept)

            # L2
            inL2 = common.exist_in_cache(stockid, concept, 2)
            csv_inL2 = dframe.loc[idx, 'inL2']
            if not csv_inL2 and csv_inL1:       # 记录到L1则一定要记录到L2
                csv_inL2 = 1

            if csv_inL2 and not inL2:       # 需要插入L2
                self.insertCache(stockid, concept, date, cache=2)
            elif inL2 and not csv_inL2:     # 需要从L1中删除
                self.removeCache(stockid, concept, cache=2)


    def insertCache(self, stockid, concept, date, cache=1):
        stockid = common.regulize_stockid(stockid)
        if cache == 1:
            self.mongodb.concepts.L1.update({"stockid":stockid, "concept":concept},
                                        {"$set":{"stockid":stockid, "concept":concept, "name":common.QueryStockMap(id=stockid)[0], "updatetime": date}},upsert=True)
        else:
            self.mongodb.concepts.L2.update({"stockid":stockid, "concept":concept},
                                        {"$set":{"stockid":stockid, "concept":concept, "name":common.QueryStockMap(id=stockid)[0], "updatetime": date}},upsert=True)

    def removeCache(self, stockid, concept, cache=1):
        stockid = common.regulize_stockid(stockid)
        if cache == 1:
            self.mongodb.concepts.L1.remove({"stockid":stockid, "concept":concept})
        else:
            self.mongodb.concepts.L2.remove({"stockid":stockid, "concept":concept})


    # 生成L1.csv，用来浏览
    # csv 列为：
    # stockid	stockname	concept	if_delete
    # 300081	恒信移动	AR	0
    def generate_L1_csv(self, save_dir, file_name='L1.csv'):
        common.look_up_dir(save_dir)
        dframe = DataFrame()
        idx = 0
        results = self.mongodb.concepts.L1.find()
        for result in results:
            stockid = result['stockid']
            stockname = result['name']
            concept = result['concept']
            dframe.loc[idx, 'stockid'] = stockid
            dframe.loc[idx, 'stockname'] = stockname
            dframe.loc[idx, 'concept'] = concept
            dframe.loc[idx, 'if_delete'] = 0
            idx += 1
        dframe = dframe.sort(columns=['concept'])
        dframe.to_csv(os.path.join(save_dir, file_name), encoding='gbk')
        print "Generate L1.csv finished! output:%s" % os.path.join(save_dir, file_name)


    # 按照generate_L1_csv的输出格式，更新L1, 如果if_delete设置为1，则delete，如果是新行，则insert
    # csv 列为：
    # stockid	stockname	concept	if_delete
    # 300081	恒信移动	AR	0
    def update_L1_from_generated_csv(self, csv_file, date=datetime.datetime.today().strftime("%Y%m%d")):
        dframe = pd.read_csv(csv_file, encoding='gbk')
        dframe.fillna(value=0, inplace=True)
        for idx in dframe.index.values:
            stockid = dframe.loc[idx, 'stockid']
            stockid = common.regulize_stockid(stockid)
            concept = dframe.loc[idx, 'concept']
            stockname = dframe.loc[idx, 'stockname']
            if_delete = dframe.loc[idx, 'if_delete']
            # 如果为1，则删除
            if if_delete:
                self.removeCache(stockid, concept, cache=1)
                print "Delete L1 element, concept:%s, stockid:%s, stockname:%s" % (concept, stockid, stockname)
            else:
                # 如果该行值不在L1，则插入
                if not common.exist_in_cache(stockid, concept, 1):
                    stockname = common.QueryStockMap(id=stockid)[0]
                    self.insertCache(stockid, concept, date)
                    print "Insert new L1 element, concept:%s, stockid:%s, stockname:%s" % (concept, stockid, stockname)
        print "Update L1 cache from L1.csv under each day finished!"


    # 偶尔添加L1的时候需要
    def add_L1_element(self, file_dir=u'D:/Money/modeResee/复盘', file_name = u'insert_L1.csv', date=datetime.datetime.today().strftime("%Y%m%d")):
        print "Begin to insert L1 alone using file: %s" % os.path.join(file_dir, file_name)
        dframe = pd.read_csv(os.path.join(file_dir, file_name), encoding='gbk')
        for idx in dframe.index.values:
            print idx
            concept = dframe.loc[idx, 'group']  # 概念
            stockids = [common.QueryStockMap(name=dframe.loc[idx, 'name'])[1]]
            try:
                if str(dframe.loc[idx, 'anotation']) == 'nan' or len(str(dframe.loc[idx, 'anotation'])) < 2:
                    anotation_stockids = []
                else:
                    anotations = dframe.loc[idx, 'anotation'].replace(u' ', u'').replace(u'，', u',').split(u',')
                    anotation_stockids = [common.QueryStockMap(name=x)[1] for x in anotations]
            except Exception, err:
                    print "force to set the anotation stockids to be empty for concept:%s" %concept
                    anotation_stockids = []
            stockids.extend(anotation_stockids)     # 该行中，概念相关的股票
            for stockid in stockids:
                self.insertCache(stockid, concept, date, cache=1)     # 往L2中添加股票及对应的概念


if __name__ == "__main__":
    x = HitBest()
    x.add_L1_element()