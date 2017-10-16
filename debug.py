# coding:utf-8
import pandas as pd
import numpy as np
import hot_district
import common
import dragon_catcher

x = dragon_catcher.DRAGON_POOL()

start_date = "20170908"
while 1:
    if start_date >= "20170918":
        break
    next_date = common.get_lastN_date(start_date, -1)
    next_date = common.format_date(next_date, "%Y%m%d")
    x.copy_pool_dragon(start_date, next_date)
    print "copy %s to %s" %(start_date, next_date)
    start_date = next_date




# daily_frame = pd.read_csv(u'all_daily_frame.csv', encoding='gbk',dtype={"TICKER_SYMBOL":np.str}, index_col=0)
# daily_frame.head()
#
#
# tpath = u'D:/Money/modeResee/彼战'
# concept_frame = pd.read_excel(os.path.join(tpath, u'战区.xlsx'), encoding='gbk', sheetname=u'战区位置')
# concept_frame = concept_frame[concept_frame[u'开战状态'] == 1]
# concepts = concept_frame[u'战区'].values
#
#
#
# running_day = "20170706"
# n_day_before = common.get_lastN_date(running_day, 80)
# concept_frame_list = []
# all_local_frame = common.FindConceptStocks(n_day_before, running_day)
#
# for concept in concepts:
#     concept_stocks = []
#     # 云财经中相关股票
#     ycj_stocks = common.get_ycj_stocks(concept)
#     # 金融界中相关股票
#     jrj_stocks = common.get_ycj_stocks(concept)
#     # 本地csv中相关股票
#     csv_stocks = all_local_frame.filter_by_concept(concept)
#     # 合并到一起
#     concept_stocks.extend(ycj_stocks)
#     concept_stocks.extend(jrj_stocks)
#     concept_stocks.extend(csv_stocks.ticker.values)
#
#     concept_stocks = list(set(concept_stocks))
#     tmp_concept_frame = pd.DataFrame({"stockid":concept_stocks})
#     tmp_concept_frame['concept'] = concept
#     concept_frame_list.append(tmp_concept_frame)
# # index stockid, concept
# concept_frame = pd.concat(concept_frame_list, axis=0)
#
# condition1_frame = hot_district.filter_stock_by_zt_condition(daily_frame, condition='ZT', zt_num=3)
# condition1_frame.head()
#
# for concept in concepts:
#     print concept
#     concept_stock_list = list(concept_frame[concept_frame.concept==concept].stockid.values)
#     # 概念对应的所有股票的日线数据
#     concept_daily_frame = daily_frame[daily_frame.TICKER_SYMBOL.isin(concept_stock_list)]
#     # 统计出其涨幅排行
#     concept_rank_chg_frame = hot_district.add_rank_chg(concept_daily_frame, chg_days=[5, 25], sort_v=5)
#     # 得到涨幅排行前三的股票
#     stock_list = list(concept_rank_chg_frame.sort('rank', ascending=False).tail(3).TICKER_SYMBOL.values)
#     # 得到连续N个涨停以上的股票
#     stock_list.extend(condition1_frame[condition1_frame.TICKER_SYMBOL.isin(concept_stock_list)])
#     stock_list = list(set(stock_list))
#     # 一系列k线图
#     k_line_frame_list = []
#     for stock in stock_list:
#         stock_frame = daily_frame[daily_frame.TICKER_SYMBOL == stock][[u'TRADE_DATE', 'OPEN_PRICE', 'CLOSE_PRICE', 'HIGHEST_PRICE', 'LOWEST_PRICE',
#                                                                        'TURNOVER_VOL', 'TICKER_SYMBOL']]
#         stock_frame.columns=['date', 'open', 'close', 'high', 'low', 'volume', 'code']
#         # index row，date，open, close, high, low, volume, code
#         stock_frame = stock_frame.sort('date', ascending='True')
#         stock_frame.reset_index(inplace=True)
#         del stock_frame['index']
#         k_line_frame_list.append(stock_frame)
#     break
#
# # 画出一系列的html
# concept_rank_chg_frame = concept_rank_chg_frame[concept_rank_chg_frame.TICKER_SYMBOL.isin(stock_list)]
# concept_rank_chg_frame = concept_rank_chg_frame.sort('rank', ascending=True)
#
# common.get_html_curve([concept_rank_chg_frame[[u'TICKER_SYMBOL', '5_ratio', '25_ratio']]], 'TEST_2_K_LINE', html_types=[6], title_list = ['TEST6'])
# # common.get_html_curve(k_line_frame_list, 'TEST_MULTI_K_LINE', html_types=[4]*len(k_line_frame_list), title_list = ['TEST']*len(k_line_frame_list))