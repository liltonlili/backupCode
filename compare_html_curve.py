#coding:utf-8
import common
import pandas as pd
from pandas import DataFrame, Series
import numpy as np



date = '2014-12-12'
stock_list = ['601800', '600528']
dframe = common.get_dataframe_option1(stock_list, date)
# dframe_list = []
# for stock in stock_list:
#     tmp_frame = common.get_minly_frame(stock, date)
#     tmp_frame = tmp_frame[['bartime', 'closeprice']]
#     yesterday = common.get_lastN_date(date, 1)
#     yeframe = common.get_mysqlData([stock],[yesterday])
#     if len(yeframe) > 0:
#         pre_close = yeframe.loc[0,'CLOSE_PRICE']
#     else:
#         pre_close = 10000
#     tmp_frame['closeprice'] = common.normalize_frame(tmp_frame['closeprice'], pre_close)
#     tmp_frame.columns = ['barTime', stock]
#     tmp_frame.set_index('barTime', inplace=True)
#     dframe_list.append(tmp_frame)
# dframe = pd.concat(dframe_list, axis=1)
#
# dframe.reset_index(range(len(dframe)), inplace=True)
common.get_html_curve([dframe], u"筹码散了不好带了2", save_dir="C:/Users/li.li/Desktop/test")