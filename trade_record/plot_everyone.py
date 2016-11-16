# coding:utf-8
import sys
sys.path.append("../")
import common
import pandas as pd
from pandas import DataFrame, Series
import numpy as np
import os
from matplotlib.finance import candlestick_ohlc,candlestick2_ohlc
import datetime
import logging
import matplotlib.pyplot as plt
import trade_util
import os


# 画图， 6幅图， 上下结构，分别是当天交易分时图，当天交易日线图，下一次交易日线图
def plot_trade_figure(stockid, current_date, current_dframe, trade_next_date, next_dframe, store_dir):
    if os.path.exists(store_dir):
        pass
    else:
        os.mkdir(store_dir)
    '''
    得到交易时间、方向列表
    '''
    current_directions = [x[1] for x in current_dframe]    # 方向列表
    current_times = [x[0] for x in current_dframe]      # 时间列表
    next_directions = [x[1] for x in next_dframe]    # 方向列表
    next_times = [x[0] for x in next_dframe]      # 时间列表
    if len(current_directions) == 1:
        current_daily_direction = current_directions[0]
    else:
        current_daily_direction = u'买卖'

    [name,tmp_id]=common.QueryStockMap(id=stockid)
    name = name.replace("*","")


    '''
    日线数据， 需要注意，date中的08/是否有影响
    '''
    end_date = common.format_date(current_date,"%Y-%m-%d")
    start_date = common.get_lastN_date(end_date,120)

    next_end_date = common.format_date(trade_next_date,"%Y-%m-%d")
    next_start_date = common.get_lastN_date(next_end_date,120)

    # 个股日线的数据
    stock_current_dailyframe = common.get_daily_frame(stockid, start_date, end_date, id_type = 1)
    # 上证日线的数据
    sh_current_dailyframe = common.get_daily_frame(stockid, start_date, end_date, id_type = 0)
#     # 个股下个操作日的日线数据
#     stock_next_dailyframe = get_daily_frame(stockid, next_start_date, next_end_date, id_type = 1)
#     # 上证下个操作日的日线数据
#     sh_next_dailyframe = get_daily_frame(stockid, next_start_date, next_end_date, id_type = 0)

    '''
    分时线数据
    '''
    # 个股分时线的数据
    stock_current_minframe = common.get_minly_frame(stockid, current_date, id_type =1)
    # 上证分时线的数据
    sh_current_minframe = common.get_minly_frame(stockid, current_date, id_type =0)
    # 个股下个操作日的分时线数据
    stock_next_minframe = common.get_minly_frame(stockid, next_end_date, id_type =1)
    # 上证下个操作日的分时线数据
    sh_next_minframe = common.get_minly_frame(stockid, next_end_date, id_type =0)


    '''
    开始画图
    '''
    fig = plt.figure(figsize=[25,10])
    # fig = plt.figure()
    # plt.title("%s_%s_%s"%(stockid, end_date,next_end_date))
    point = 10
    ax1 = fig.add_subplot(231)
    ax2 = fig.add_subplot(234)
    ax3 = fig.add_subplot(232)
    ax4 = fig.add_subplot(235)
    ax5 = fig.add_subplot(233)
    ax6 = fig.add_subplot(236)

    trade_util.plot_candlestick(stock_current_dailyframe,ax1,point =point,direction = current_daily_direction,mount_flag = 1)  # 个股日线图
    trade_util.plot_candlestick(sh_current_dailyframe,ax2,point =point,mount_flag = 1)  # 上证指数日线图

    trade_util.plot_dealDetail(stock_current_minframe,ax3,dtimes=current_times,ddirections=current_directions,mount_flag=1)    # 个股分时图
    if len(sh_current_minframe) > 0:
        trade_util.plot_dealDetail(sh_current_minframe,ax4,dtimes=current_times,ddirections=current_directions,mount_flag=1)    # 指数分时图

    trade_util.plot_dealDetail(stock_next_minframe,ax5,dtimes=next_times,ddirections=next_directions,mount_flag=1)    # 个股分时图 (下一个操作日)
    if len(sh_next_minframe) > 0:
        trade_util.plot_dealDetail(sh_next_minframe,ax6,dtimes=next_times,ddirections=next_directions,mount_flag=1)    # 指数分时图 （下一个操作日）

    plt.savefig(os.path.join(store_dir, "%s_%s_%s_%s_%s.png" % (end_date, current_daily_direction, next_end_date, stockid,name)),dpi=300)
    # plt.savefig(os.path.join(store_dir, "%s_%s_%s_%s.pdf" % (end_date, current_daily_direction, stockid,name)),dpi=300)
    plt.close()




def main(csv_dir, csv_name, out_dir):
    aframe = pd.read_csv(os.path.join(csv_dir, csv_name), encoding='GBK')
    aframe.columns = ['trade_date', 'time', 'stockid', 'name', 'direction', 'price', 'cjje', 'fsje', 'bcje']
    aframe['stockid'] = aframe['stockid'].apply(lambda x: "0"*(6-len(str(x))) + str(x))
    aframe['trade_date'] = aframe['trade_date'].apply(lambda x: x.split("/")[0]+"/"+"0"*(2-len(x.split("/")[1]))+x.split("/")[1] + "/" + "0"*(2-len(x.split("/")[2]))+x.split("/")[2])
    total_dict = {}

    # total_dict = {
    # '601989':["2016/09/28", "2016/09/29",....]}
    for stocid in np.unique(aframe.stockid.values):
        tmp_dict = trade_util.get_trade_date(stocid, aframe)
        if len(tmp_dict) > 0:
            total_dict.update(tmp_dict)

    # 开始逐个画图
    for trade_date in np.unique(aframe.trade_date.values):
        date_dir = int(common.format_date(trade_date,"%Y%m%d"))    # 输出文件夹目录
        store_dir = "%s/%s"%(date_dir,date_dir)
        store_dir = os.path.join(out_dir, store_dir)
        if not os.path.exists(store_dir):
            os.makedirs(store_dir)

        dframe = aframe[aframe.trade_date == trade_date]
        current_date = trade_date
        # {stockid:[[time1, direction1, price1, cjje1, fsje1, bcje1], [time2, direction2, price2, cjje2, fsje2, bcje2]]}
        trade_time_dict = trade_util.get_stockid_map(dframe)
        for stockid in trade_time_dict.keys():
            stockid = "0"*(6-len(str(stockid))) + str(stockid)
            trade_next_date = trade_util.get_next_trade_date(stockid, current_date, total_dict)
            if trade_next_date is None:
                logging.getLogger().error("No valid next trade date for %s, current_date:%s"%(stockid, current_date))
                continue
            # 下一个有效交易日的所有dframe
            next_dframe = aframe[aframe.trade_date == trade_next_date]
            next_trade_time_dict = trade_util.get_stockid_map(next_dframe)
            # 画图， 6幅图， 上下结构，分别是当天交易分时图，当天交易日线图，下一次交易日线图
            plot_trade_figure(stockid, current_date, trade_time_dict[stockid], trade_next_date, next_trade_time_dict[stockid], store_dir)
            # break
        # break


if __name__ == '__main__':
    csv_dir = u'D:/Money/lilton_code/Market_Mode/learnModule/lhc_pic/save'
    csv_name = u'令胡冲交割单_带时间.csv'
    out_dir = u'D:/Money/lilton_code/Market_Mode/交割单/令胡冲'
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(threadName)s Line:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S.000',
                    filename=os.path.join(out_dir, u'交割单.log'),
                    filemode='w+')
    main(csv_dir, csv_name, out_dir)