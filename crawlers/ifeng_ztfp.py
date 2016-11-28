# coding:utf-8
'''
从凤凰财经上爬取涨停复盘，如果能够进行结构化，就比较有价值了
'''
import pymongo
import requests as rs
import datetime as dt
import os
import sys
sys.path.append("../")
import common
import time
from lxml import etree

mongodb = pymongo.MongoClient("localhost")

def crawl_fp(date, out_dir = u"D:/Money/modeResee/复盘/网络复盘/凤凰"):
    try:
        date = common.format_date(date, "%Y%m%d")
        year = date[:4]
        month = date[4:6]
        day = date[-2:]
        if int(year) < 2016 and int(month) <7 and int(day) < 27:        # 20150627 之前
            url = "http://finance.ifeng.com/TMP/special/ztbfp%s%s/index.shtml"%(month, day)
        else:                                           # 20150628之后
            url = "http://finance.ifeng.com/TMP/special/ztbfp%s/index.shtml"%date[2:]
        if int(date) > 20151126:
            url = url.replace("TMP", "mrztbfp")
        else:
            url = url.replace("TMP", 'news')
        while True:
            r = rs.get(url)
            if r.status_code != 200:
                time.sleep(5)
            else:
                break
        root = etree.HTML(r.content)
        fig_address = root.xpath('//div[@class="pic01"]//img/@src')[0]
        # 下载图片
        while True:
            r = rs.get(fig_address)
            if r.status_code == 200:
                break
            else:
                time.sleep(5)
        with open(os.path.join(out_dir, "%s.jpg"%date), 'wb') as fHandler:
            fHandler.write(r.content)
        return True
    except Exception, e:
        print e
        return False


'''
以下为从0开始强制重新下载
'''
results = mongodb.stock.ZDT_by_date.find({"date":{"$gte": "20150612"}})
for result in results:
    out_dir = u"D:/Money/modeResee/复盘/网络复盘/凤凰"
    date = result['date']
    if os.path.exists(os.path.join(out_dir, "%s.jpg"%date)):
        continue

    status = crawl_fp(date)
    print date, status
    time.sleep(2)