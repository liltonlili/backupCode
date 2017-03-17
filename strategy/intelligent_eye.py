# coding:utf-8
'''
该代码的目的是生成一个html，用来复盘当日走势，包括：
1. 指数分时图，以及在指数分时图的基础上，涨停的冲击点分布（以颜色区分是否涨停成功，即后面是否有开板，可重复计算）
2. 根据概念、热点，画出各个概念、热点下的板块攻击图

具体来看：
A. 分数图和涨停冲击分布，横轴是时间，左纵轴是涨幅，右纵轴是数量，用来刻画某个时间点的涨停数
'''
import datetime as dt
import time
import pandas as pd
import pymongo
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append("D:/Money/lilton_code/Market_Mode/rocketup")
import common
import copy
import os
import best_hit
import datetime
import numpy as np



class IntelliGentEye:
    def __init__(self, day = dt.datetime.today().strftime("%Y%m%d")):
        self.mongodb = pymongo.MongoClient("localhost")
        # self.day = day  # 日期
        self.day = day
        self.mongoRecord = self.mongodb.stock.ZDT_by_date.find({"date":day})[0]
        self.ztList = []
        self.hiList = []
        if 'ZT_stocks' in self.mongoRecord.keys():
            self.ztList = self.mongoRecord['ZT_stocks'].split("_")
        if 'HD_stocks' in self.mongoRecord.keys():
            self.hiList = self.mongoRecord['HD_stocks'].split("_")

    # 根据日期，得到zt和hi的list
    def get_zt_high_list(self, date):
        date = common.format_date(date, "%Y%m%d")
        mongoRecord = self.mongodb.stock.ZDT_by_date.find({"date":date})[0]
        ztList = []
        hiList = []
        if 'ZT_stocks' in mongoRecord.keys():
            ztList = mongoRecord['actulZtStocks'].split("_")
        if 'HD_stocks' in mongoRecord.keys():
            hiList = mongoRecord['HD_stocks'].split("_")
        return [ztList, hiList]

    # 统计出各个和涨停有关的股票，其涨停时间、状态
    # 返回两个dict: closeZt, openZt, 涨停后封住的dict以及涨停后未能封住的dict
    # closeZt = {"14:26":[3, "601989,600036"]}, openZt同理
    def get_zt_details(self):
        # '''
        # 临时debug
        # '''
        # self.hiList = ['603108', '000929']
        # self.hiList = ['000672']
        # self.ztList = []
        # self.ztList = ['603819', '603987', '000422', '000022']
        targetlist = []
        targetlist.extend(self.ztList)
        targetlist.extend(self.hiList)
        closeZt = {}
        openZt = {}
        for stock in targetlist:
            closetime, nonstable_time = common.zt_time_details(stock, self.day)
            stock_name = common.QueryStockMap(stock)[0]
            if stock_name == "":
                stock_name = stock
            self.add_to_dict(closeZt, closetime, stock_name)
            self.add_to_dict(openZt, nonstable_time, stock_name)
        return closeZt, openZt

    def scan(self):
        # 第一步，先扫描得到有涨停记录的股票，生成dataframe
        # {u'09:30': [2, '603819,603987']}, {u'09:49': [1, '000022']}
        self.closeZt, self.openZt = self.get_zt_details()


        # dataframe用来记录每个时间点，开板和封板的个数和股票情况
        dataframe = common.get_minly_ratio_frame(["ZS000001"], self.day)
        dataframe.set_index('barTime', inplace=True)
        if len(self.closeZt) == 0:
            dataframe.loc['15:00', 'Num'] = 0
            # dataframe.loc['15:00', 'Details'] = ""
        for bartime in self.closeZt:
            bartime = bartime.encode("utf-8")
            dataframe.loc[bartime, 'Num'] = self.closeZt[bartime][0]
            dataframe.loc[bartime, 'Details'] = self.closeZt[bartime][1]
        for bartime in self.openZt:
            bartime = bartime.encode("utf-8")
            dataframe.loc[bartime, 'oNum'] = self.openZt[bartime][0]
            dataframe.loc[bartime, 'oDetails'] = self.openZt[bartime][1]


        if len(self.openZt) == 0:
            dataframe.loc['15:00', 'oNum'] = 0
            # dataframe.loc['15:00', 'oDetails'] = " "
        dataframe.fillna(value = "'-'", inplace=True)
        # 第二步，再得到每日的概念聚合的股票
        self.dataframe = dataframe
        dframe_list = [dataframe]
        title_list = ['']
        type_list = [2]
        concept_dict = common.get_concept_list(self.day)
        for concept in concept_dict.keys():
            # print concept
            stock_list = concept_dict[concept]
            # 增加上证指数
            stock_list.append("ZS000001")
            tmp_dframe = common.get_dataframe_option1(stock_list, self.day)
            dframe_list.append(tmp_dframe)
            title_list.append(concept)
            type_list.append(1)
        # 生成html文件
        save_day = common.format_date(self.day, "%Y%m%d")
        common.get_html_curve(dframe_list, u"market_eye", html_types = type_list, title_list=title_list, save_dir=os.path.join(u"D:/Money/modeResee/复盘/%s"%save_day,""))


    # 根据某日的daydayup.csv 生成今日的html
    def scan_yestoday(self):
        last_day = common.get_last_date(self.day)
        common.generate_html(last_day, self.day)


    # 根据股票概念，生成html，方框热力图，显示概念的延续性情况
    # 最近30天的概念情况，日期可自定义
    def concept_pipeline_html(self, default_period=30, csv_dir=u'D:/Money/modeResee/复盘'):
        concepts = common.get_focused_concepts()    # 热力图的纵轴
        back_day = common.get_lastN_date(self.day, default_period)
        day_list = common.getDate(back_day, self.day)       # 热力图横轴
        zt_concepts_group = [0] * (len(day_list)*len(concepts))
        hd_concepts_group = [0] * (len(day_list)*len(concepts))
        dt_concepts_group = [0] * (len(day_list)*len(concepts))
        meat_concepts_group = [0] * (len(day_list)*len(concepts))
        hole_concepts_group = [0] * (len(day_list)*len(concepts))
        group_list = [zt_concepts_group, hd_concepts_group, dt_concepts_group, meat_concepts_group, hole_concepts_group]
        character_list = ['ZT', 'HD', 'DT', 'meat', 'hole']
        # character_list = ['ZT']
        group_list = group_list[:len(character_list)]
        for i in range(0, len(day_list)):
            tarday = day_list[i]
            print tarday
            tarday = common.format_date(tarday, "%Y%m%d")
            dframe = pd.read_csv(os.path.join(csv_dir, "%s/daydayup.csv" %tarday), encoding='gbk')
            dframe['len_status'] = dframe['stock'].apply(lambda x: len(str(x)))
            dframe = dframe[dframe.len_status > 0]
            for j in range(0, len(concepts)):
                concept = concepts[j]
                cframe = dframe[dframe.group == concept]
                for k in range(0, len(character_list)):
                    tmp_frame = cframe[cframe.type == character_list[k]]
                    stock_name = list(set(list(np.unique(tmp_frame.name.values))))
                    num = len(stock_name)
                    stock_name = "_".join(stock_name)
                    position = j*len(day_list) + i
                    group_list[k][position] = [j, i, num, stock_name]

        dframe_list = []
        day_list = [common.format_date(x, "%m%d") for x in day_list]
        for i in range(0, len(group_list)):
            dframe_list.append(common.get_dataframe_option3(group_list[i], "_".join(concepts), "_".join(day_list), character_list[i]))
        type_list = [3] * len(dframe_list)
        title_list = character_list
        save_day = common.format_date(self.day, "%Y%m%d")
        common.get_html_curve(dframe_list, u"concepts_flow", html_types=type_list, title_list=title_list, save_dir=os.path.join(u"D:/Money/modeResee/复盘/%s"%save_day, ""))


    # 增加
    # dict结构为： closeZt = {"14:26":[3, "601989,600036"]}
    # 其中, dkey为"14:26", value 为 601989
    def add_to_dict(self, ddict, dkey_list, dvalue):
        for dkey in dkey_list:
            if dkey in ddict.keys():
                count = ddict[dkey][0] + 1
                value = "%s,%s"%(ddict[dkey][1], dvalue)
                ddict[dkey] = [count, value]
            else:
                ddict[dkey] = [1, dvalue]

if __name__ == "__main__":
    global mongodb
    mongodb = pymongo.MongoClient("localhost")
    today = dt.datetime.today().strftime("%Y%m%d")

    # today = "20170314"

    htmler = IntelliGentEye(day=today)
    # 生成概念热力图
    htmler.concept_pipeline_html()
    # # 生成分时图的html文件，包括当天的，和昨天涨停、高点涨停股票在今日的表现
    htmler.scan()
    # 生成昨日涨停、HD、DT的股票今日表现
    htmler.scan_yestoday()
    print "Generate Html finished!"

    # # 更新L1/L2
    cacheL = best_hit.HitBest()
    cacheL.updateCacheFromCsv(today, today)
    print "Update cache pool finished!"

    # # 生成L1.csv
    result = mongodb.stock.ZDT_by_date.find({"date":{"$lte":today}}).sort("date", pymongo.DESCENDING)[0]
    save_dir_name = result['date']
    constant_dir = u'D:/Money/modeResee/复盘'
    save_dir = u"%s/%s" %(constant_dir, save_dir_name)
    cacheL.generate_L1_csv(save_dir)
    print 'generate L1 csv finished, output dir:%s' %save_dir

    # 生成.bat文件用来更新L1
    with open(os.path.join(save_dir, u"2是否提高.bat"), 'wb') as fHandler:
        fHandler.write(ur"@start cmd /k python D:\Money\lilton_code\Market_Mode\rocketup\strategy\manage_cache_L1.py")
    common.showinfos(u'请review L1.csv')
