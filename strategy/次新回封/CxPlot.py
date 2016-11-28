# coding:utf-8
'''
将次新股的开板、封板情况画出来
'''
import matplotlib.pyplot as plt
from pandas import DataFrame
import pandas as pd
import numpy as np
import datetime
import time
import sys,os
import pymongo
sys.path.append("../")
import common

# 每日的开板数，回封数（在回封积累数的基础上）
def plot_back_open_num(ax, markersize=8):
    global results, htmlType1
    count = 0

    # 回封数，同html格式一致，[["2016-01-01", 回封连板数，符合条件的股票数(相同回封数), 股票代码字符串], ["2016-09-28", 回封连板数，符合条件的股票数, 股票代码字符串], ...]
    backTen_list = []

    # 开板数，格式如上， [['2016-01-01', 之前连板数，符合条件的股票数(相同连板), 股票代码字符串], ['2016-09-29', '之前连板数', 符合条件的股票数, 股票代码字符串], ...]
    open_list = []

    # 昨日back涨停股票，今日涨幅，格式如上, [['2016-01-01', 股票涨幅, 符合条件的股票数（相同涨幅), 股票代码字符串]
    yes_back_ratio_list = []

    # 第一次回封失败股票，格式如上，[['2016-01-01', 股票亏损额度(10 - 涨幅), 符合条件的股票数（相同涨幅), 股票代码字符串]
    # 第一次回封失败的股票，第二日的涨幅， [['2016-01-01', 股票涨幅, 符合条件的股票数（相同涨幅), 股票代码字符串]
    first_back_fail_list = []
    first_back_next_ratio_list = []

    # 第二次回封失败股票，格式如上，[['2016-01-01', 股票亏损额度(10 - 涨幅), 符合条件的股票数（相同涨幅), 股票代码字符串]
    # 第二次回封失败的股票，第二日的涨幅， [['2016-01-01', 股票涨幅, 符合条件的股票数（相同涨幅), 股票代码字符串]
    second_back_fail_list = []
    second_back_next_ratio_list = []


    last_result = {}
    # 记录昨日最高冲击涨停股，今日的涨幅
    last_direct_high_list = []
    last_second_back_high_list = []
    for result in results:
        # 记录backCount和openCount是哪些
        trace_backCount = {}  # trace_backCount = {3:"000002_000012_000026"}
        trace_openCount = {}
        trace_yesbackRatio = {} # trace_yesbackRatio = {2.75:"000002"}

        # 回封失败的损失
        trace_first_back_fail_loss = {} # trace_first_back_fail_loss = {2.75:"000002"}
        trace_second_back_fail_loss = {}
        trace_next_first_fail_ratio = {}
        trace_next_second_fail_ratio = {}

        # 记录每日回封的个数， backCount = {3:2}, 在第几个板回封的个数
        backCount = {}
        # 记录每日开板的情况， openCount = {15:2, 10:1}, 表示前面N连板且在今天开板的股票数
        openCount = {}
        # 记录昨日回封股票，今日的涨幅, yesbackRatio = {3.27:2, 10:1}
        yesbackRatio = {}
        # 回封失败的个数
        firstbackCount = {}
        secondbackCount = {}
        next_firstbackCount = {}
        next_secondbackCount = {}


        day = result['date']
        day = common.format_date(day, "%Y-%m-%d")
        print day

        if len(last_result) == 0:
            yesDay = common.get_last_date(day)
            last_result = mongodb.stock.ZDT_by_date.find({"date":common.format_date(yesDay, "%Y%m%d")})[0]

        backTen_acc = result['backTen_acc']
        dummyDirectTen = result['dummyDirectTen']
        directOpen = result['directOpen']
        backOpen = result['backOpen']
        highDirectOpenList = result['highDirectOpen']
        highBackOpenList = result['highBackOpen']

        last_dummyDirectTen_list = last_result['dummyDirectTen'].keys()  # 昨日回封的股票
        last_backTen_acc = last_result['backTen_acc']  # 昨日回封的涨幅

        # 记录昨日回封的股票，今日收益
        if len(last_dummyDirectTen_list) > 0:        #昨日有回封的
            for stockid in last_dummyDirectTen_list:
                acc_last_back_ratio = last_backTen_acc[stockid]
                ratio = backTen_acc[stockid] - acc_last_back_ratio # 得到今日涨幅
                ratio = round(ratio, 2)
                if ratio in yesbackRatio:
                    yesbackRatio[ratio] += 1
                    trace_yesbackRatio[ratio] += "_%s"%stockid
                else:
                    yesbackRatio[ratio] = 1
                    trace_yesbackRatio[ratio] = stockid
        else:
            yesbackRatio = {0:0}
            trace_yesbackRatio = {0:""}

        # 记录每日的回封股票数
        if len(dummyDirectTen) > 0: # 存在回封的股票
            for stockid in dummyDirectTen.keys():
                num_back = int(backTen_acc[stockid] / 9)    # 回封的时候是几个板
                if num_back in backCount.keys():
                    backCount[num_back] += 1
                    trace_backCount[num_back] += "_%s"%stockid
                else:
                    backCount[num_back] = 1
                    trace_backCount[num_back] = stockid
        else:
            backCount = {0: 0}
            trace_backCount = {0:""}

        # 记录每日的开板数
        if len(directOpen) > 0:   # 直接开板
            for stockid in directOpen:
                continue_num = last_result['directTen'][stockid]        # 昨日会记录该股票的连板数
                continue_num = round(float(continue_num)/5, 2)
                continue_num *= -1
                if continue_num in openCount.keys():
                    openCount[continue_num] += 1
                    trace_openCount[continue_num] += "_%s"%stockid
                else:
                    openCount[continue_num] = 1
                    trace_openCount[continue_num] = stockid

        if len(backOpen) > 0:   # 回封开板
            for stockid in backOpen:
                print stockid
                continue_num = last_result['dummyDirectTen'][stockid]        # 昨日会记录该股票的连板数
                continue_num = round(float(continue_num)/5, 2)
                continue_num *= -1
                if continue_num in openCount.keys():
                    openCount[continue_num] += 1
                    trace_openCount[continue_num] += "_%s"%stockid
                else:
                    openCount[continue_num] = 1
                    trace_openCount[continue_num] = stockid
        if len(openCount) == 0:
            openCount = {0: 0}
            trace_openCount = {0:""}


        # 记录1回封失败，第二天的涨跌幅
        for stockid in last_direct_high_list:
            ratio = common.get_day_k_status(stockid, day)   # 今日涨幅
            if ratio in next_firstbackCount.keys():
                next_firstbackCount[ratio] += 1
                trace_next_first_fail_ratio[ratio] += "_%s"%stockid
            else:
                next_firstbackCount[ratio] = 1
                trace_next_first_fail_ratio[ratio] = stockid
        if len(next_firstbackCount) == 0:
            next_firstbackCount = {0: 0}
            trace_next_first_fail_ratio = {0:""}

        # 记录2回封失败，第二天的涨跌幅
        for stockid in last_second_back_high_list:
            ratio = common.get_day_k_status(stockid, day)   # 今日涨幅
            if ratio in next_secondbackCount.keys():
                next_secondbackCount[ratio] += 1
                trace_next_second_fail_ratio[ratio] += "_%s"%stockid
            else:
                next_secondbackCount[ratio] = 1
                trace_next_second_fail_ratio[ratio] = stockid
        if len(next_secondbackCount) == 0:
            next_secondbackCount = {0: 0}
            trace_next_second_fail_ratio = {0:""}

        # 记录每日的直接开板后回封失败情况
        for stockid in highDirectOpenList.keys():
            hit_status = common.get_hit_status(stockid, day)   # 是否开板之后有回封
            if hit_status:  # 有回封
                last_direct_high_list.append(stockid)
                ratio = highDirectOpenList[stockid]
                loss = round(10 - ratio, 2)
                if loss in firstbackCount.keys():
                    firstbackCount[loss] += 1
                    trace_first_back_fail_loss[loss] += "_%s"%stockid
                else:
                    firstbackCount[loss] = 1
                    trace_first_back_fail_loss[loss] = stockid
        if len(firstbackCount) == 0:
            firstbackCount = {0:0}
            trace_first_back_fail_loss = {0:""}
            last_direct_high_list = []

        # 记录每日的二封回封失败情况
        for stockid in highBackOpenList.keys():
            num_back = int(backTen_acc[stockid] / 9)    # 回封的时候是几个板
            if num_back != 1:       # 只记录第二封的情况
                continue
            hit_status = common.get_hit_status(stockid, day)   # 是否开板之后有回封
            if hit_status:  # 有回封
                last_second_back_high_list.append(stockid)
                ratio = highBackOpenList[stockid]
                loss = round(10 - ratio, 2)
                if loss in secondbackCount.keys():
                    secondbackCount[loss] += 1
                    trace_second_back_fail_loss[loss] += "_%s"%stockid
                else:
                    secondbackCount[loss] = 1
                    trace_second_back_fail_loss[loss] = stockid
        if len(secondbackCount) == 0:
            secondbackCount = {0:0}
            trace_second_back_fail_loss = {0:""}
            last_second_back_high_list = []


        for num in backCount:
            ax.plot(count, num, color='r', marker=markers[backCount[num]], markersize=markersize)
            backTen_list.append([day, num, backCount[num], trace_backCount[num]])     # 回封

        for num in openCount:
            open_list.append([day, num, openCount[num], trace_openCount[num]])     # 开板
            ax.plot(count, num, color='g', marker=markers[openCount[num]], markersize=markersize)

        for ratio in yesbackRatio:
            yes_back_ratio_list.append([day, ratio, yesbackRatio[ratio], trace_yesbackRatio[ratio]])

        for ratio in firstbackCount:
            first_back_fail_list.append([day, ratio, firstbackCount[ratio], trace_first_back_fail_loss[ratio]])

        for ratio in next_firstbackCount:
            first_back_next_ratio_list.append([day, ratio, next_firstbackCount[ratio], trace_next_first_fail_ratio[ratio]])

        for ratio in secondbackCount:
            second_back_fail_list.append([day, ratio, secondbackCount[ratio], trace_second_back_fail_loss[ratio]])

        for ratio in next_secondbackCount:
            second_back_next_ratio_list.append([day, ratio, next_secondbackCount[ratio], trace_next_second_fail_ratio[ratio]])

        count += 1
        last_result = result

    # 写入html
    str_back = str(backTen_list).replace('"', '').replace("'", '"')
    str_open = str(open_list).replace('"', '').replace("'", '"')
    str_yesback_ratio = str(yes_back_ratio_list).replace('"', '').replace("'", '"')
    str_4 = "[]"
    str_first_fail = str(first_back_fail_list).replace('"', '').replace("'", '"')
    str_second_fail = str(second_back_fail_list).replace('"', '').replace("'", '"')
    size1 = size2 = size3 = "5"
    type1html = htmlType1.replace("DATA1", str_back).replace("DATA2", str_open).replace("DATA3", str_yesback_ratio).replace("DATA4", str_4).replace("SIZE1", size1).replace("SIZE2", size2).replace(' u"', ' "')
    type1html = type1html.replace("DATA5", str_first_fail).replace("DATA6", str_second_fail).replace(' u"', ' "').replace("SIZE3", size3)
    with open(os.path.join(u"D:/Money/modeResee/复盘/次新", "TypeA.html"), 'wb') as fHanlder:
        fHanlder.write(type1html)

if __name__ == "__main__":
    start_day = "20160108"
    end_day = "20161124"
    global mongodb, results, markers
    markers = {0:".", 1:"o", 2:"<", 3:"^", 4:"h", 5:"*"}
    global htmlType1
    with open("../../src/type1_html.html", 'rb') as fHanlder:
        htmlType1 = fHanlder.read()
    mongodb = pymongo.MongoClient("localhost")
    results = mongodb.stock.ZDT_by_date.find({"date":{"$gte":start_day, "$lte":end_day}})
    figure = plt.figure(figsize=(18, 8))
    # 回封数，开板数
    ax1 = figure.add_subplot(221)
    ax1.grid(True)
    plot_back_open_num(ax1)
    # plt.show()


