#coding:utf-8
import pandas as pd
from pandas import DataFrame, Series
import datetime as dt
import pymongo
import sys
sys.path.append("../")
import common
import copy

'''
该代码从每日的开板、封板等数据进行追踪
'''



# 将涨停的股票，根据是否一字进行区分
def group_ten_list(stockids, day):
    price_frame = common.get_mysqlData(stockids,[day])
    direct_list = list(price_frame[price_frame.HIGHEST_PRICE == price_frame.LOWEST_PRICE]['TICKER_SYMBOL'])
    back_list = list(price_frame[price_frame.HIGHEST_PRICE > price_frame.LOWEST_PRICE]['TICKER_SYMBOL'])
    return direct_list, back_list

# 计划将多种统计都在这里完成
# 传入的都是昨日的值
# dummyDirectTen = {"000839":15,}  考虑回封在内的连板涨停数，用不同颜色标注
# directTen = {"000839":14,}  不考虑回封，直接一字涨停的连板数
# backTen_acc = {"000839": 21.4%, }
# directOpen = {"601989":3.45, }
# backOpen = {"601989":3.45, }
# highDirectOpen = {"601989":3.45}
# highBackOpen = {"601989":3.45}
def continues_count(day, directTen, dummyDirectTen, backTen_acc, today_zt_stocks, today_new_stocks):
# def continues_count(day, *args):
#     [directTen, dummyDirectTen, backTen_acc, today_zt_stocks, today_new_stocks] = args
    zt_stocks = today_zt_stocks.split("_")
    new_stocks = today_new_stocks.split("_")
    direct_ten_list, back_ten_list = group_ten_list(zt_stocks, day)
    directOpen = {}
    highDirectOpen = {}
    backOpen = {}
    highBackOpen = {}
    # 搞清楚dummyDirecTen 同 backTen的关系, XXX
    # dummyDirectTen的key同backTen的key基本一致，如果当天某回封股票不再涨停，则在dummy中就直接抹去了，但在当日的backTen_acc还有（为了看累计涨幅）
    # 到了第二天，该股票就不再出现在backTen_acc中
    # 先将昨日打开涨停的去除，这样当天acc能看到，第二天就看不到了
    remove_stocks = [x for x in backTen_acc.keys() if x not in dummyDirectTen.keys()]
    for stcid in remove_stocks:
        del backTen_acc[stcid]

    # 先判断dummy
    for stocid in copy.copy(dummyDirectTen.keys()):
        if len(stocid) <3:
            del dummyDirectTen[stocid]
            continue
        ratio, close_zt_status, close_dt_status, high_zt_status, low_dt_status = common.get_day_k_status(stocid, day)
        if ratio is None:
            print "None for %s, %s"%(stocid, day)
            continue
        backTen_acc[stocid] += ratio
        if stocid in zt_stocks: # 继续涨停
            dummyDirectTen[stocid] += 1
        else:   # 开板
            del dummyDirectTen[stocid]
            backOpen[stocid] = ratio
            if high_zt_status:
                highBackOpen[stocid] = ratio

    for stocid in copy.copy(directTen.keys()):
        if len(stocid) <3:
            del directTen[stocid]
            continue
        if stocid in direct_ten_list:  # 继续连续涨停
            directTen[stocid] += 1
        elif stocid in back_ten_list:   # 今日回封了，记录从directTen转移到 dummyDirectTen
            ratio, close_zt_status, close_dt_status, high_zt_status, low_dt_status = common.get_day_k_status(stocid, day)
            dummyDirectTen[stocid] = directTen[stocid] + 1
            backTen_acc[stocid] = ratio
            del directTen[stocid]  # 不再涨停，剔除
        else:   # 直接开板了
            ratio, close_zt_status, close_dt_status, high_zt_status, low_dt_status = common.get_day_k_status(stocid, day)
            if ratio is None:
                del directTen[stocid]  # 不再涨停，剔除
                print "None in directOpen for %s, %s"%(stocid, day)
                continue
            directOpen[stocid] = ratio
            if high_zt_status:
                highDirectOpen[stocid] = ratio
            del directTen[stocid]


    # 将新股加到directTen中
    for stocid in new_stocks:
        directTen[stocid] = 1
    return directTen, dummyDirectTen, backTen_acc, directOpen, highDirectOpen, backOpen, highBackOpen

# 更新数据库
# 如果force =1， 则在start_day不考虑前一天数据库的值，强制从0开始
def reControlCx(start_day = '20160101', end_day = dt.datetime.today().strftime("%Y%m%d"),  force = 0):
    mongodb = pymongo.MongoClient("localhost")
    # 统计新股的开始日期 start_day
    # 统计结束日期 end_day

    results = mongodb.stock.ZDT_by_date.find({"date":{"$gte":start_day, "$lte":end_day}})
    # 强势从0开始
    if force == 1:
        previous_back_list = [] # 记录的昨日持续涨停的、回封新股， 不包括今天的回封, 每天开盘前，该字段的值就确定了
        previous_direct_ten_list = [] # 记录的昨日直接涨停的新股，未曾开板过， 每天开盘前，该字段的值就确定了
        flag = 0

        directTen = {}    # 当天，各个一字新股的累计涨停个数，收盘之后才能确定
        backTen_acc = {}      # 当天，各个回封股票的累计涨幅，收盘之后才能确定
        dummyDirectTen = {}
        # dummyDirectTen = {"000839":15,}  考虑回封在内的连板涨停数，用不同颜色标注
        # directTen = {"000839":14,}  不考虑回封，直接一字涨停的连板数
        # backTen_acc = {"000839": 21.4%, }
        # directOpen = {"601989":3.45, }
        # backOpen = {"601989":3.45, }
        # highDirectOpen = {"601989":3.45}
        # highBackOpen = {"601989":3.45}

        # return directTen, dummyDirectTen, backTen_acc, directOpen, highDirectOpen, backOpen, highBackOpen
        last_zt_stocks = "" #昨日的涨停股票
        last_new_stocks = "" # 昨日新上市的股票
    else:
        print start_day
        last_start = common.get_lastN_date(start_day, 1)
        last_start = common.format_date(last_start, "%Y%m%d")
        last_mongo = mongodb.stock.ZDT_by_date.find({"date": last_start})
        day = last_start
        directTen = {}    # 当天，各个一字新股的累计涨停个数，收盘之后才能确定
        backTen_acc = {}      # 当天，各个回封股票的累计涨幅，收盘之后才能确定
        dummyDirectTen = {}
        flag = 1
        if last_mongo.count() == 1:
            mongo_record = last_mongo[0]
            if 'previous_direct_ten_list' in mongo_record.keys():
                previous_direct_ten_list = mongo_record['previous_direct_ten_list']

            if 'directTen' in mongo_record.keys():
                directTen = mongo_record['directTen']

            if 'dummyDirectTen' in mongo_record.keys():
                dummyDirectTen = mongo_record['dummyDirectTen']

            if 'backTen_acc' in mongo_record.keys():
                backTen_acc = mongo_record['backTen_acc']

            if "freshStocks" in mongo_record.keys():
                last_zt_stocks = mongo_record['freshStocks']
            else:
                last_zt_stocks = ""

            if "Add_newStocks" in mongo_record.keys():
                last_new_stocks = "_".join(mongo_record['Add_newStocks'].keys())
            else:
                last_new_stocks = ""

    # 更新每天的昨日回封股票list、昨日一字涨停股票list、今日的一字涨停股票和涨停数（多了数目，也多了今天新加的股票）、
    # 今日的回封股票及涨停数（多了数值，以及今天回封的股票）
    for result in results:
        if flag == 0:   # 说明是初始化的第一天
            if "freshStocks" in result:
                previous_direct_ten_list = result['freshStocks'].split("_")     # 赋值为当天的一字涨停新股（包括了当天的新上市股，也包括了回封的新股，所有的都是当天涨停的）
            flag = 1
        else:
            # 今日的“昨日直接涨停新股” = 昨日的“昨日直接涨停新股”中涨停的 + 昨日新增的股票， 还应该减去中间有开板过的
            previous_direct_ten_list = [x for x in previous_direct_ten_list if x in last_zt_stocks.split("_")]
            previous_direct_ten_list, new_back_ten_list = group_ten_list(previous_direct_ten_list, day)

            previous_direct_ten_list.extend(last_new_stocks.split("_"))
            previous_direct_ten_list = list(set(previous_direct_ten_list))
            # 昨日涨停的新股 = 前日一字新股中昨日直接涨停的 + 昨日新上市的 + 回封的
            previous_back_list = [x for x in last_zt_stocks.split("_") if x not in previous_direct_ten_list]

        if "freshStocks" in result.keys():
            last_zt_stocks = result['freshStocks']
        else:
            last_zt_stocks = ""

        if "Add_newStocks" in result:
            last_new_stocks = "_".join(result['Add_newStocks'].keys())
        else:
            last_new_stocks = ""

        day = result['date']
        # 更新今日收盘后，一字涨停的股票涨停数
        directTen, dummyDirectTen, backTen_acc, directOpen, highDirectOpen, backOpen, highBackOpen = continues_count(day, directTen, dummyDirectTen, backTen_acc, last_zt_stocks, last_new_stocks)
        print day
        print "will update"
        print "directTen:", directTen
        mongodb.stock.ZDT_by_date.update({"date":day},
                                         {"$set":
                                              {"previous_direct_ten_list":previous_direct_ten_list,
                                               "previous_back_list":previous_back_list,
                                               "directTen":directTen,
                                               "dummyDirectTen":dummyDirectTen,
                                               "backTen_acc":backTen_acc,
                                               "directOpen":directOpen,
                                               "highDirectOpen":highDirectOpen,
                                               "backOpen":backOpen,
                                               "highBackOpen":highBackOpen}},
                                         True)

if __name__ == "__main__":
    reControlCx(start_day='20150624', end_day='20160108', force = 1)