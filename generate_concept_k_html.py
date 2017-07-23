#coding:utf-8
import pandas as pd
import sys
import common
import os
import numpy as np
import tushare as ts
import pymongo
import time

mongodb = pymongo.MongoClient("localhost")
tframe = pd.read_csv(u'D:/Money/运筹帷幄/tframe.csv', encoding='utf-8', index_col=0, dtype=np.str)

# 得到一个新股上市的dict
global new_stock_list_by_date
new_stock_list_by_date = {}

# 概念list
global concept_data_frame_list
concept_data_frame_list = {}
# concept_data_frame = pd.DataFrame()


mongo_results = mongodb.stock.ZDT_by_date.find({"date":{"$gt":"20100101"}}).sort("date", 1)
newstock_frame = pd.DataFrame()
for result in mongo_results:
    tdate = result['date']
    if 'Add_newStocks' in result.keys():
        newstock_frame.loc[tdate, 'ticker'] = "_".join(result['Add_newStocks'].keys())
    else:
        newstock_frame.loc[tdate, 'ticker'] = "_"

for tdate in newstock_frame.index.values:
    tmp_frame = newstock_frame[newstock_frame.index <= tdate].tail(120)
    tmp_stock_list = "_".join(list(tmp_frame.ticker.values))
    tmp_stock_list = list(set(tmp_stock_list.split("_")))
    tmp_stock_list = [x for x in tmp_stock_list if x!='' and x!= u'未公布']
    new_stock_list_by_date[tdate] = tmp_stock_list




# INDEX TICKER_SYMBOL SEC_SHORT_NAME TRADE_DATE rate
def get_all_concept_stocks_daily_rate(start_date, end_date, target_concept, tframe):
    target_code_list = tframe[(tframe.date>=start_date) & (tframe.date<=end_date) & (tframe.concept == target_concept)].ticker.values
    # trade_date_list = common.getDate(start_date,end_date)
    # trade_detail = common.get_mysqlData(target_code_list, trade_date_list)
    trade_detail = common.get_mysqlData_tushare(target_code_list, start_date, end_date)
    trade_detail['rate'] = 100*(trade_detail['CLOSE_PRICE'] - trade_detail['PRE_CLOSE_PRICE'])/trade_detail['PRE_CLOSE_PRICE']
    trade_detail['rate'] = trade_detail['rate'].round(2)
    trade_detail['hrate'] = 100*(trade_detail['HIGHEST_PRICE'] - trade_detail['PRE_CLOSE_PRICE'])/trade_detail['PRE_CLOSE_PRICE']
    trade_detail['hrate'] = trade_detail['hrate'].round(2)
    trade_detail['lrate'] = 100*(trade_detail['LOWEST_PRICE'] - trade_detail['PRE_CLOSE_PRICE'])/trade_detail['PRE_CLOSE_PRICE']
    trade_detail['lrate'] = trade_detail['lrate'].round(2)
    trade_detail = trade_detail[['TICKER_SYMBOL', 'SEC_SHORT_NAME','OPEN_PRICE', 'HIGHEST_PRICE', 'LOWEST_PRICE', 'CLOSE_PRICE', 'TRADE_DATE', "TURNOVER_VOL", 'rate', 'hrate', 'lrate']]
    trade_detail['TRADE_DATE'] = trade_detail['TRADE_DATE'].apply(lambda x: str(x).replace('-', ''))
#     trade_detail = trade_detail.pivot(index='SEC_SHORT_NAME', columns='TRADE_DATE', values='rate')
#     trade_detail.to_excel(u'分析结果/%s_study.xlsx'%target_concept, encoding='gbk')
    return trade_detail


def get_daily_forcuse_stock(xdetail):
    concept_history_zt_list = {}
    zt_frame = xdetail[xdetail.rate > 9]
    global new_stock_list_by_date
    for trade_date in np.unique(xdetail.TRADE_DATE.values):
        tmp_frame = zt_frame[zt_frame.TRADE_DATE <= trade_date]
        if trade_date in new_stock_list_by_date.keys():
            new_stock_list = new_stock_list_by_date[trade_date]
        else:
            new_stock_list = []
        concept_history_zt_list[trade_date] = [x for x in list(tmp_frame.TICKER_SYMBOL.values) if x not in new_stock_list]
    return concept_history_zt_list


# 得到统计了每天，关注列表涨幅分布的frame，以及所有相关概念股票在日期范围内的涨幅数据
# group_frame 格式为： index, date, ratio, count
# all_concept_stock_dailyframe 格式为： INDEX TICKER_SYMBOL SEC_SHORT_NAME TRADE_DATE rate
def get_group_frame(start_date, end_date, target_concept, tframe):

    #所有相关概念股票在日期范围内的涨幅数据
    all_concept_stock_dailyframe = get_all_concept_stocks_daily_rate(start_date, end_date, target_concept, tframe)

    # 得到每天应该关注的股票列表(过去有涨停历史)
    concept_history_zt_list = get_daily_forcuse_stock(all_concept_stock_dailyframe)

    # 每天关注股票对应的涨跌幅，便于统计
    forcus_frame_list = []
    for trade_date in concept_history_zt_list.keys():
        stock_list = concept_history_zt_list[trade_date]
        tmp_frame = all_concept_stock_dailyframe[(all_concept_stock_dailyframe.TRADE_DATE == trade_date) & (all_concept_stock_dailyframe.TICKER_SYMBOL.isin(stock_list))]
        forcus_frame_list.append(tmp_frame)

    # 每天，关注的股票（以前有涨停历史）的涨幅
    forcus_frame = pd.concat(forcus_frame_list, axis=0)
    # 统计数据，每天，在各个rate的股票数
    group_frame = forcus_frame.groupby(['TRADE_DATE', 'rate'])['TICKER_SYMBOL'].count().reset_index()

    # 转换成html支持的格式
    group_frame['TRADE_DATE'] = group_frame['TRADE_DATE'].apply(lambda x: common.format_date(x, '%Y-%m-%d'))
    group_frame.rename(columns={"TRADE_DATE":"date", "TICKER_SYMBOL":"count", "rate":"ratio"}, inplace=True)
    group_frame['data_flag'] = 1
    return group_frame, all_concept_stock_dailyframe

# 得到符合html要求的dataframe
def get_dataframe_option5(start_date, end_date, target_concept, stockid, tframe):
    global concept_data_frame_list
    if target_concept not in concept_data_frame_list.keys():
        print "will get all_concept_stock_dailyframe for %s" %target_concept
        group_frame, all_concept_stock_dailyframe = get_group_frame(start_date, end_date, target_concept, tframe)
        concept_data_frame_list[target_concept] = [group_frame, all_concept_stock_dailyframe]
    else:
        [group_frame, all_concept_stock_dailyframe] = concept_data_frame_list[target_concept]
    signal_frame = all_concept_stock_dailyframe[all_concept_stock_dailyframe.TICKER_SYMBOL == stockid]
    stock_name = signal_frame.iloc[0,:]['SEC_SHORT_NAME']
    signal_frame = signal_frame[['TRADE_DATE', 'rate']]
    signal_frame.rename(columns={"TRADE_DATE":'date', 'rate':"ratio"}, inplace=True)
    signal_frame['date'] = signal_frame['date'].apply(lambda x: common.format_date(x, "%Y-%m-%d"))
    signal_frame['count'] = 1
    signal_frame['data_flag'] = 2
    outframe = pd.concat([signal_frame, group_frame], axis=0)
    name_list = [target_concept, stock_name]
    return outframe, name_list


# start_date = '20151113'
# end_date = '20170601'
# target_concept = u'新能源'

concept_list = {
    # u"新能源":["20151102", "20160706"],
    # u"股权变更":["20160704", "20161201"],
    u"雄安":["20170301", "20170628"]
    # u"黄金":["20160115", "20160828"]
}

for tconcept in concept_list.keys():
    print tconcept
    global concept_data_frame_list
    start_date = concept_list[tconcept][0]
    end_date = concept_list[tconcept][1]
    concept_stocks = list(np.unique(tframe[(tframe.concept == tconcept) & (tframe.date>=start_date) & (tframe.date <= end_date)].ticker.values))
    for stockid in concept_stocks:
        print stockid
        # dframe_k = ts.get_k_data(stockid,start=common.format_date(start_date, "%Y-%m-%d"), end=common.format_date(end_date, "%Y-%m-%d"))
        test_frame, name_list = get_dataframe_option5(start_date, end_date, tconcept, stockid, tframe)
        tmp_frame = concept_data_frame_list[tconcept][1]
        dframe_k = tmp_frame[tmp_frame.TICKER_SYMBOL == stockid][['TICKER_SYMBOL', 'SEC_SHORT_NAME', 'OPEN_PRICE', 'HIGHEST_PRICE', 'LOWEST_PRICE', 'CLOSE_PRICE', 'TRADE_DATE', 'rate', 'hrate', 'lrate', 'TURNOVER_VOL']]
        dframe_k['TRADE_DATE'] = dframe_k['TRADE_DATE'].apply(lambda x: common.format_date(x,"%Y-%m-%d"))
        common.get_html_curve([[dframe_k,test_frame]], name_list[1].replace(r'*', u'星'), html_types=['4and5'], title_list=[stockid], height=700, data_name_list=name_list, save_dir=os.path.join(u'D:/Money/运筹帷幄/分析结果', tconcept))
        # break
    # break