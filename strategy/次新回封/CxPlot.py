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
    backTen_list = []   # 回封数，同html格式一致，[["2016-01-01", 回封连板数，符合条件的股票数], ["2016-09-28", 回封连板数，符合条件的股票数], ...]
    open_list = []  # 开板数，格式如上， [['2016-01-01', 之前连板数，符合条件的股票数], ['2016-09-29', '之前连板数', 符合条件的股票数], ...]
    last_result = {}
    for result in results:
        # 记录每日回封的个数， backCount = {3:2}, 在第几个板回封的个数
        backCount = {}
        # 记录每日开板的情况， openCount = {15:2, 10:1}, 表示前面N连板且在今天开板的股票数
        openCount = {}
        day = result['date']
        day = common.format_date(day, "%Y-%m-%d")

        if len(last_result) == 0:
            yesDay = common.get_last_date(day)
            last_result = mongodb.stock.ZDT_by_date.find({"date":common.format_date(yesDay, "%Y%m%d")})[0]

        backTen_acc = result['backTen_acc']
        dummyDirectTen = result['dummyDirectTen']
        directOpen = result['directOpen']
        backOpen = result['backOpen']
        if len(dummyDirectTen) > 0: # 存在回封的股票
            for stockid in dummyDirectTen.keys():
                num_back = int(backTen_acc[stockid] / 9)    # 回封的时候是几个板
                if num_back in backCount.keys():
                    backCount[num_back] += 1
                else:
                    backCount[num_back] = 1
        else:
            backCount = {0: 0}

        if len(directOpen) > 0:   # 直接开板
            for stockid in directOpen:
                continue_num = last_result['directTen'][stockid]        # 昨日会记录该股票的连板数
                continue_num = round(float(continue_num)/5, 2)
                continue_num *= -1
                if continue_num in openCount.keys():
                    openCount[continue_num] += 1
                else:
                    openCount[continue_num] = 1
        if len(backOpen) > 0:   # 回封开板
            for stockid in backOpen:
                continue_num = last_result['dummyDirectTen'][stockid]        # 昨日会记录该股票的连板数
                continue_num = round(float(continue_num)/5, 2)
                continue_num *= -1
                if continue_num in openCount.keys():
                    openCount[continue_num] += 1
                else:
                    openCount[continue_num] = 1
        if len(openCount) == 0:
            openCount = {0: 0}


        for num in backCount:
            ax.plot(count, num, color='r', marker=markers[backCount[num]], markersize=markersize)
            backTen_list.append([day, num, backCount[num]])     # 回封

        for num in openCount:
            open_list.append([day, num, openCount[num]])     # 开板
            ax.plot(count, num, color='g', marker=markers[openCount[num]], markersize=markersize)
        count += 1
        last_result = result

    # 写入html
    str_back = str(backTen_list).replace('"', '').replace("'", '"')
    str_open = str(open_list).replace('"', '').replace("'", '"')
    str_3 = str_back
    str_4 = str_open
    size1 = size2 = "5"
    type1html = htmlType1.replace("DATA1", str_back).replace("DATA2", str_open).replace("DATA3", str_3).replace("DATA4", str_4).replace("SIZE1", size1).replace("SIZE2", size2)
    with open(os.path.join("C:/Users/li.li/Desktop/test", "openBack.html"), 'wb') as fHanlder:
        fHanlder.write(type1html)

if __name__ == "__main__":
    start_day = "20160101"
    end_day = "20161116"
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


