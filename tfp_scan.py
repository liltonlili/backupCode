#coding:utf-8
'''
用来记录每天的复牌股, 更新到数据库中
'''
import requests as rs
from lxml import etree
import pandas as pd
from pandas import DataFrame, Series
import sys
import os
import datetime
import pymongo
import time
import common

class TFP_Crawler:
    def __init__(self, pageNo=5): # 默认扫5页
        self.pageNo = pageNo
        mongourl = "localhost"
        self.mongodb = pymongo.MongoClient(mongourl)
        self.date = datetime.datetime.today().strftime("%Y-%m-%d")  # 当前日期
        # self.date = '2017-05-19'
        self.dayRange = 3   # 3天之内的复牌

    def crawl(self):
        for page in range(1, self.pageNo+1):
            target_url = "http://datainterface.eastmoney.com/EM_DataCenter/JS.aspx?type=FD&sty=SRB&st=0&sr=-1&p=" + str(page) + "&ps=50&js=var%20kcSTlIop={pages:(pc),data:[(x)]}&mkt=1&fd=2017-03-13&rt=49646855"
            r = rs.get(target_url)
            if r.status_code != 200:
                print "crawl %s failed!"%page
                continue
            content = r.content.decode('utf-8')
            info_dict = self.parse_content(content)

    def parse_content(self, content):
        content = content.replace(u'var kcSTlIop=', u'').replace(u'pages', u'"pages"').replace(u'data', u'"data"')
        con_dict = eval(content)

        # 当前时间点
        ttime = time.localtime()
        thour = ttime.tm_hour
        tmin = ttime.tm_min
        day_list = []
        if thour >= 18:  # 晚上6点以后，可以得到当天收盘价了，关注复牌时间点为[明天，今天，昨天]
            for n in range(2-self.dayRange, 2):
                day_list.append(common.get_lastN_date(self.date, n))
        else:               # 否则，关注时间点为[今天，昨天，前天]
            for n in range(1-self.dayRange, 1):
                day_list.append(common.get_lastN_date(self.date, n))

        for infos in con_dict['data']:
            elements = infos.split(",")
            if len(elements) < 2:
                continue
            secid = elements[0]
            secname = elements[1]
            tp_time = elements[-2]
            fp_time = elements[-1]
            reason = elements[5]
            db_num = self.mongodb.stock.FP.find({"stcid":"%s" % secid, "tp_time":"%s" % tp_time, "fp_time":"%s" % fp_time, "target_ratio":{"$exists":True}}).count()
            if db_num > 0:
                continue
            else:
                self.mongodb.stock.FP.update({"stcid":"%s" % secid, "tp_time":"%s" % tp_time},
                                             {"$set":{"stcid":"%s" % secid, "tp_time":"%s" % tp_time, "fp_time":"%s" % fp_time, "reason":"%s" %reason}},
                                             True, True)


            # 仅仅记录目标日期在关注日期内的信息
            if fp_time in day_list:
                # 期间大盘涨幅
                if secid[:2] == '60':
                    dp_stockid = 'ZS000001'
                else:
                    dp_stockid = 'ZS399006'

                dp_frame = common.get_mysqlData([dp_stockid], [tp_time, common.get_last_date(fp_time)])
                if len(dp_frame) < 2:
                    continue

                dp_ratio = (dp_frame.loc[1, 'CLOSE_PRICE'] - dp_frame.loc[0, 'CLOSE_PRICE']) / dp_frame.loc[0, 'CLOSE_PRICE']
                dp_ratio = round(dp_ratio, 2)

                # 停牌时价格
                stock_price = common.get_mysqlData([secid], [tp_time]).loc[0, 'CLOSE_PRICE']
                if dp_ratio > 0:
                    diff = 0.05
                else:
                    diff = -0.05

                # 目标涨幅
                target_ratio = dp_ratio + diff

                # 目标价格
                target_price = round(stock_price*(1+target_ratio), 2)

                # 停牌时间
                delta_days = common.get_mongoDicts(dateStart=tp_time,dateEnd=fp_time).count()

                self.mongodb.stock.FP.update({"stcid":"%s" % secid, "tp_time":"%s" % tp_time},
                                             {"$set":{"dp_ratio":dp_ratio, "target_ratio":target_ratio, "target_price": target_price, 'delta_days':delta_days}},
                                             True, True)


if __name__ == '__main__':
    x = TFP_Crawler()
    x.crawl()