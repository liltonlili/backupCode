#coding:utf-8
import common
import pandas as pd
from pandas import DataFrame, Series
import numpy as np

dframe = DataFrame()
date = '2016-11-9'
stock_list = ['002716', '600547', '002155', '600988', '601069', '600489']
for stock in stock_list:
    tmp_frame = common.get_minly_frame(stock, date)
    tmp_frame = tmp_frame[['bartime', 'closeprice']]
    yesterday = common.get_lastN_date(date, 1)
    yeframe = common.get_mysqlData([stock],[yesterday])
    if len(yeframe) > 0:
        pre_close = yeframe.loc[0,'CLOSE_PRICE']
    else:
        pre_close = 10000
    tmp_frame['closeprice'] = common.normalize_frame(tmp_frame['closeprice'], pre_close)
    tmp_frame.columns = ['barTime', stock]
    tmp_frame.set_index('barTime', inplace=True)
    dframe = pd.concat([dframe, tmp_frame], axis=1)

dframe.reset_index(range(len(dframe)), inplace=True)
common.get_html_curve(dframe, "try4", save_dir="C:/Users/li.li/Desktop/test")