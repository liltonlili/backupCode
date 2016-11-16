#coding:utf-8
import pymongo
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
import time
import sys
sys.path.append("./../../")
import common
import datetime
import matplotlib.pyplot as plt

'''
该程序从每一只上市新股的角度进行统计
'''

# 得到某只新股的非一字涨停日期， 非一字涨停日状态（涨停 or 涨幅）， 非涨停收盘日， 非涨停收盘涨幅
# dates 为上市日
def get_stopDetail(stockid, dates, mysqls):
    global diOut_dict, backTen_dict, tenMonitor_dict
    stockid = '0'*(6-len(stockid)) + stockid

    edates = common.get_lastN_date(dates, -50)
    dates = common.format_date(dates,"%Y-%m-%d")
    edates = common.format_date(edates,"%Y-%m-%d")
    table="vmkt_equd"
    query = 'SELECT TICKER_SYMBOL, SEC_SHORT_NAME, TRADE_DATE, PRE_CLOSE_PRICE, OPEN_PRICE, HIGHEST_PRICE, LOWEST_PRICE, CLOSE_PRICE, ACT_PRE_CLOSE_PRICE ' \
                'from %s where TICKER_SYMBOL = "%s" and TRADE_DATE >= "%s" and TRADE_DATE <= "%s"' % (table, stockid, dates, edates)
    z = mysqls.dydb_query(query)
    z['actualRatio'] = (z['CLOSE_PRICE'].astype(np.float64) /z['PRE_CLOSE_PRICE'].astype(np.float64)) - 1
    z['actualRatio'] = (100*z['actualRatio']).round(2)

    z['priceTen'] = z['PRE_CLOSE_PRICE'].astype(np.float64) * 1.1
    z['priceTen'] = z['priceTen'].round(2)

    z['closeStatus'] = z['CLOSE_PRICE'] - z['priceTen']
    z['closeStatus'] = z['closeStatus'].apply(lambda x: True if x >= 0 else False)

    z['lowStatus'] = z['LOWEST_PRICE'] - z['priceTen']
    z['lowStatus'] = z['lowStatus'].apply(lambda x: True if x >= 0 else False)
    print stockid
    # 记录第一次的时间点
    # 如果当前还在涨停期间，跳过
    if len(z[z.lowStatus != True].index.values) == 0:
        return 100, "2018-01-01", "No Result", "INF", "2018-01-01", "100"
    print stockid

    first_low_out_index = z[z.lowStatus != True].index.values[0]
    first_low_out_day = z.loc[first_low_out_index, 'TRADE_DATE']

    # 当前还在回封期， 开板日设置为2018-01-01， 开板的index设置为无穷大
    if len(z[z.closeStatus != True].index.values) == 0:
        first_close_out_index = 10000
        first_close_out_day = "2018-01-01"
    else:
        first_close_out_index = z[z.closeStatus != True].index.values[0]
        first_close_out_day = z.loc[first_close_out_index, 'TRADE_DATE']

    if first_low_out_index == first_close_out_index:     # 开板没有回封
        diout_ratio = z.loc[first_close_out_index, 'actualRatio']
        diout_ratio = round(diout_ratio,2)
        if first_low_out_day not in diOut_dict.keys():
            diOut_dict[first_low_out_day] = {"stock":[stockid], "ratio":[diout_ratio]}
        else:
            diOut_dict[first_low_out_day]['stock'].append(stockid)
            diOut_dict[first_low_out_day]['ratio'].append(diout_ratio)
    else:    # 开板后回封
        diback_ratio = z.loc[first_low_out_index, 'actualRatio']
        diback_ratio = round(diback_ratio,2)
        # 记录每天的回封个数
        if first_low_out_day not in backTen_dict.keys():
            backTen_dict[first_low_out_day] = {"stock":[stockid], "ratio":[diback_ratio]}
        else:
            backTen_dict[first_low_out_day]['stock'].append(stockid)
            backTen_dict[first_low_out_day]['ratio'].append(diback_ratio)

        # 记录开板
        if first_close_out_index != 10000:
            diout_ratio = z.loc[first_close_out_index, 'actualRatio']
            diout_ratio = round(diout_ratio,2)
            if first_close_out_day not in diOut_dict.keys():
                diOut_dict[first_close_out_day] = {"stock":[stockid], "ratio":[diout_ratio]}
            else:
                diOut_dict[first_close_out_day]['stock'].append(stockid)
                diOut_dict[first_close_out_day]['ratio'].append(diout_ratio)


        # 记录每天回封后的涨幅（即：A日回封，B日不再涨停，记录A+1日到B日至今的涨幅）
        for idx in range(first_low_out_index+1, first_close_out_index+1):
            if idx > max(z.index.values):
                break
                # idx = max(z.index.values)
            day = z.loc[idx, 'TRADE_DATE']





            # today = datetime.datetime.now()
            # print day, today
            # if day == datetime.date(2016, 11, 7) and stockid == "300548":
            #     print 'abc'
            # if day > datetime.date(today.year, today.month, today.day):
            #     print 'yes'
            #     break

            # 这里记录的是收盘涨幅，开板再回封的情况暂时不考虑
            ratio = z.loc[idx, 'actualRatio']
            if day not in tenMonitor_dict.keys():
                tenMonitor_dict[day] = {"stock":[stockid], "ratio":[ratio]}
            else:
                tenMonitor_dict[day]['stock'].append(stockid)
                tenMonitor_dict[day]['ratio'].append(ratio)

    ## 此处不全，diOut不仅仅是first_low_out_index， 还包括回封后开板的
    # return
    # 返回涨停数，开板日，开板状态（是否回封）， 非涨停日，非涨停日涨幅
    if first_close_out_index == 10000:
        actualRatio = 100
    else:
        actualRatio = z.loc[first_close_out_index, 'actualRatio']
    return first_close_out_index, first_low_out_day, first_close_out_index > first_low_out_index, first_close_out_index - first_low_out_index,first_close_out_day,actualRatio



mongourl = "localhost"
mongodb = pymongo.MongoClient(mongourl)
results = mongodb.stock.ZDT_by_date.find({"date": {"$gte": "20160101"}})
count = 0
dframe = DataFrame()
mysqls = common.mysqldata()

global diOut_dict, backTen_dict, tenMonitor_dict
diOut_dict = {}    # 开板没有回封的记录
backTen_dict = {}  # 专门记录回封情况的dict
tenMonitor_dict = {}    # 回封后的每a日监控

for result in results:
    dates = result['date']
    if "Add_newStocks" in result.keys():
        stocks = result['Add_newStocks'].keys()
        for stock in stocks:
            dframe.loc[count, 'startDate'] = dates
            dframe.loc[count, 'stockid'] = stock
            dframe.loc[count, 'name'] = common.QueryStockMap(stock)[0]
            tmp_result = get_stopDetail(stock, dates, mysqls)
            (dframe.loc[count, 'numTen'], dframe.loc[count, 'openDate'], dframe.loc[count, 'backTen?'],
            dframe.loc[count, 'backDuring'], dframe.loc[count, 'stopDate'], dframe.loc[count, 'stopRatio']) = tmp_result
            count += 1

print 'will finish'
dframe.to_csv(u"新股开板情况.csv", encoding='GBK')