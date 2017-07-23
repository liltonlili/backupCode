#coding:utf-8
import requests as rs
import time
import json
import logging
import pymongo
import datetime
import pandas as pd
import os
import numpy as np
import common
import crawl_ycj_concept

## 配置log
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(threadName)s Line:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S.000',
                    filename=u'D:/Money/modeResee/彼战/logs/theme_digger.log',
                    filemode='w+')

'''
输入dframe格式为：
#      TICKER_SYMBOL SEC_SHORT_NAME  TRADE_DATE  PRE_CLOSE_PRICE  OPEN_PRICE    HIGHEST_PRICE   LOWEST_PRICE  CLOSE_PRICE ACT_PRE_CLOSE_PRICE TURNOVER_VOL
# 0           000033          *ST新都  2016-04-27            10.38        0.00           0.00          0.00        10.38
# 1           600710          *ST常林  2016-04-27             9.36        0.00         10.61         10.52        10.57
'''
'''
输出的frame格式为：
index TICKER_SYMBOL TRADE_DATE
'''
# 连续N日涨停
def filter_stock_by_zt_condition(dframe, condition='ZT', zt_num=3):
    if condition == 'ZT':
        dframe['ZT_PRICE'] = dframe['PRE_CLOSE_PRICE'] * 1.1
        dframe['ZT_PRICE'] = dframe['ZT_PRICE'].round(2)
        dframe['ZT_CLOSE_DELTA'] = dframe['ZT_PRICE'] - dframe['CLOSE_PRICE']
        dframe['ZT_STATUS'] = dframe['ZT_CLOSE_DELTA'].apply(lambda x: 1 if float(x) == 0.0 else 0)
        match_frame_list = []
        for stockid, stock_frame in dframe.groupby(['TICKER_SYMBOL']):
            # stock_frame = stock_frame.sort('TRADE_DATE', ascending=True)
            stock_frame = stock_frame.sort_values(by=['TRADE_DATE'], ascending=True)
            stock_frame['continue_zt'] = pd.rolling_apply(stock_frame['ZT_STATUS'], zt_num, accum_multip)
            stock_frame.fillna(0, inplace=True)
            match_frame_list.append(stock_frame[stock_frame.continue_zt == 1][['TICKER_SYMBOL', 'TRADE_DATE']])
        match_frame = pd.concat(match_frame_list, axis=0)
        match_frame.reset_index(inplace=True)
        del match_frame['index']
        return match_frame


'''
输入dframe格式为：
#      TICKER_SYMBOL SEC_SHORT_NAME  TRADE_DATE  PRE_CLOSE_PRICE  OPEN_PRICE    HIGHEST_PRICE   LOWEST_PRICE  CLOSE_PRICE ACT_PRE_CLOSE_PRICE TURNOVER_VOL
# 0           000033          *ST新都  2016-04-27            10.38        0.00           0.00          0.00        10.38
# 1           600710          *ST常林  2016-04-27             9.36        0.00         10.61         10.52        10.57
'''
'''
输出的frame格式为：
index TICKER_SYMBOL 5_chg 25_chg N_chg rank
'''
# dframe是某个concept
# 将dframe增加chg_days（最近N天）对应的区间涨跌幅，并按照sort列给出rank值
def add_rank_chg(dframe, chg_days=[5, 25], sort_v=5):
    # dframe = dframe.sort('TRADE_DATE', ascending='True')
    dframe = dframe.sort_values(by=['TRADE_DATE'], ascending='True')
    dframe = dframe[['TICKER_SYMBOL', 'TRADE_DATE', 'PRE_CLOSE_PRICE', 'CLOSE_PRICE']]
    dframe['daily_ratio'] = 100*(dframe['CLOSE_PRICE'] - dframe['PRE_CLOSE_PRICE'])/dframe['PRE_CLOSE_PRICE']
    dframe['daily_ratio'] = dframe['daily_ratio'].round(2)
    oframe = pd.DataFrame()
    max_day = max(dframe.TRADE_DATE.values)
    for chg_day in chg_days:
        # 求出最近N天的涨跌幅
        n_day = common.get_lastN_date(max_day, chg_day)
        n_day = common.format_date(n_day, "%Y-%m-%d")

        tmp_frame = dframe[dframe.TRADE_DATE >= n_day]
        for stockid, stockframe in tmp_frame.groupby('TICKER_SYMBOL'):
            oframe.loc[stockid, '%s_ratio' % chg_day] = 100*(np.prod(1+stockframe['daily_ratio']/100)-1)
    oframe.reset_index(inplace=True)
    oframe.rename(columns={"index":"TICKER_SYMBOL"}, inplace=True)
    oframe['rank'] = oframe['%s_ratio' % sort_v].rank(method='min', ascending=False)
    # oframe = oframe.sort("rank")
    oframe = oframe.sort_values(by=["rank"])
    return oframe


def accum_multip(df):
    return np.prod(df)


class ThemeDigger:
    def __init__(self, running_day=datetime.datetime.today().strftime("%Y%m%d")):
        mongourl = "localhost"
        self.mongodb = pymongo.MongoClient(mongourl)
        self.path = u'D:/Money/modeResee/彼战'
        self.running_day = running_day
        self.concepts = []
        self.detect_dict = {}   # 新增的抓取项
        # 输出路径
        self.dump_dir = os.path.join(self.path, "tree")

        # 建立输出目录
        if not os.path.exists(os.path.join(self.dump_dir, self.running_day)):
            os.makedirs(os.path.join(self.dump_dir, self.running_day))

        self.read_concepts_excel()
        self.crawl_concept()


    def read_concepts_excel(self):
        # 读取关注的概念列表
        concept_frame = pd.read_excel(os.path.join(self.path, u'战区.xlsx'), encoding='gbk', sheetname=u'战区位置')
        concept_frame = concept_frame[concept_frame[u'开战状态'] == 1]
        ini_concepts = concept_frame[u'战区'].values
        top_dns_concept = []

        # 将concept化为一级域名的concept
        for concept in ini_concepts:
            concept = common.get_top_dns_concept(concept)
            top_dns_concept.append(concept)
        self.concepts = top_dns_concept

        # 设置不同概念对应的连板数
        self.direct10_num = {}
        for idx in concept_frame.index.values:
            concept_name = common.get_top_dns_concept(concept_frame.loc[idx, u'战区'])
            self.direct10_num[concept_name] = int(concept_frame.loc[idx, u'连板数'])

        # 读取关注概念统计涨跌幅的时间区间
        range_ratio_dict = {}
        dframe = pd.read_excel(os.path.join(self.path, u'战区.xlsx'), encoding='gbk', sheetname=u'历史战况', index_col=0)
        dframe.fillna(0, inplace=True)
        dframe.reset_index(inplace=True)
        dframe[u'战区'] = dframe[u'战区'].apply(lambda x: common.get_top_dns_concept(x))
        dframe.set_index(u'战区', inplace=True)
        columns = dframe.columns
        for concept in dframe.index.values:
            if concept == 0:
                continue
            tcount = 0
            concept_list = []
            tmp_list = []
            for col in columns:
                tdate = str(int(dframe.loc[concept,col]))
                if  tdate == '0':
                    if len(tmp_list) > 0:
                        concept_list.append(tmp_list)
                    break
                if tcount % 2 == 0 and tcount != 0:
                    concept_list.append(tmp_list)
                    tmp_list = []
                    tmp_list.append(tdate)
                else:
                    tmp_list.append(tdate)
                tcount += 1
            if len(concept_list) > 0:
                range_ratio_dict[concept] = concept_list

        # range_ratio = {
        #     concept_name:[[start1, end1],[start2, end2], [start3, end3], ...],
        #     concept_name2:[[start1, end1],[start2, end2], [start3, end3], ...],
        # }
        self.range_ratio_dict = range_ratio_dict

        # 读取特殊关照股票
        dframe = pd.read_excel(os.path.join(self.path, u'战区.xlsx'), encoding='gbk', sheetname=u'特殊')
        dframe.fillna(0, inplace=True)

        self.extra_stocks = [common.QueryStockMap(name=x)[1] for x in dframe[dframe.status != 'spy']['name'].values]
        rmv_frame = dframe[dframe.status == 'spy']

        # rmv_dict = {
        #     concept_name:[stockid1, stockid2, stockid3, ...]
        # }
        self.rmv_dict = {}
        for idx in rmv_frame.index.values:
            concept = rmv_frame.loc[idx, u'concept']
            concept = common.get_top_dns_concept(concept)
            stockname = rmv_frame.loc[idx, u'name']
            if concept not in self.rmv_dict.keys():
                self.rmv_dict[concept] = [common.QueryStockMap(name=stockname)[1]]
            else:
                self.rmv_dict[concept].append(common.QueryStockMap(name=stockname)[1])


        mst_frame = dframe[dframe.status != 'spy']
        # mst_dict = {
        #     concept_name:[stockid1, stockid2, stockid3, ...]
        # }
        self.mst_dict = {}
        for idx in mst_frame.index.values:
            concept = mst_frame.loc[idx, u'concept']
            concept = common.get_top_dns_concept(concept)
            stockname = mst_frame.loc[idx, u'name']
            if concept not in self.mst_dict.keys():
                self.mst_dict[concept] = [common.QueryStockMap(name=stockname)[1]]
            else:
                self.mst_dict[concept].append(common.QueryStockMap(name=stockname)[1])

        # 读取新增的云财经或者金融界的crawl id和对应的concept
        dframe = pd.read_excel(os.path.join(self.path, u'战区.xlsx'), encoding='gbk', sheetname=u'侦查信号')
        dframe.fillna(0, inplace=True)
        ycj_dframe = dframe[dframe.source == 'YCJ']
        jrj_dframe = dframe[dframe.source == 'JRJ']

        # detect_dict = {
        # "YCJ": {conceptname1: conceptid1, conceptname2: conceptid2},
        # "JRJ": {conceptname1: conceptid1, conceptname2: conceptid2}
        # }
        detect_dict = {"YCJ":{}, "JRJ":{}}
        for idx in ycj_dframe.index.values:
            concept = ycj_dframe.loc[idx, u'概念名']
            conceptid = ycj_dframe.loc[idx, u'网站id']
            concept = common.get_top_dns_concept(concept)
            detect_dict['YCJ'][concept] = conceptid

        for idx in jrj_dframe.index.values:
            concept = jrj_dframe.loc[idx, u'概念名']
            conceptid = jrj_dframe.loc[idx, u'网站id']
            concept = common.get_top_dns_concept(concept)
            detect_dict['JRJ'][concept] = conceptid

        self.detect_dict = detect_dict

    # 每周一更新一次关注概念池
    def crawl_concept(self):
        # 从云财经收集概念信息
        ycj_crawler = crawl_ycj_concept.CrawlYcjConcept()
        new_add_count = 0
        for concept in self.concepts:
            db_id = common.get_ycj_concept_id(concept)
            if len(db_id) > 0:
                # 已经存在数据库的概念，每周更新一次
                if datetime.datetime.strptime(self.running_day, "%Y%m%d").weekday() == 3:
                    ycj_crawler.add_crawl_concept(db_id, concept)
            elif concept in self.detect_dict['YCJ'].keys():
                ycj_crawler.add_crawl_concept(self.detect_dict['YCJ'][concept], concept)
            else:
                logging.getLogger().info("WARNING: no db_id and excel_record_id for concept:%s, skip scan YCJ" % (concept))
        crawl_status = ycj_crawler.crawl_multi_concepts()
        logging.getLogger().info("Crawl Results:%s" % crawl_status)
        # 从金融界收集概念信息，暂时不考虑，太多了没必要
        pass

    # 在关注的概念中，取出符合要求的股票，记录到数据库中
    '''
    要求1： 半年内连续N个涨停以上
    要求2： 一周以来涨幅TOPN
    '''
    # 记录到mongo stock.forcus_stocks表中
    def plot_stocks_html(self):
        n_day_before = common.get_lastN_date(self.running_day, 80)
        concept_frame_list = []
        all_local_frame = common.FindConceptStocks(n_day_before, self.running_day)

        # 收集所有关注概念以及对应的股票代码
        for concept in self.concepts:
            concept_stocks = []
            # 云财经中相关股票
            ycj_stocks = common.get_ycj_stocks(concept)
            # 金融界中相关股票
            jrj_stocks = common.get_jrj_stocks(concept)
            # 本地csv中相关股票
            csv_stocks = all_local_frame.filter_by_concept(concept)
            # 合并到一起
            concept_stocks.extend(ycj_stocks)
            concept_stocks.extend(jrj_stocks)
            concept_stocks.extend(csv_stocks.ticker.values)

            concept_stocks = list(set(concept_stocks))
            tmp_concept_frame = pd.DataFrame({"stockid":concept_stocks})
            tmp_concept_frame['concept'] = concept
            concept_frame_list.append(tmp_concept_frame)
        # index stockid, concept
        concept_frame = pd.concat(concept_frame_list, axis=0)

        daily_stock_list = list(np.unique(concept_frame.stockid.values))
        daily_stock_list.extend(self.extra_stocks)
        daily_stock_list = list(set(daily_stock_list))

        # 拿到这些股票，指定日期的所有日线数据
        daily_frame = common.get_mysqlData(daily_stock_list, common.getDate(n_day_before, self.running_day))
        # daily_frame.to_csv(u'all_daily_frame.csv', encoding='gbk')
        daily_frame['rate'] = 100*(daily_frame['CLOSE_PRICE'] - daily_frame['PRE_CLOSE_PRICE'])/daily_frame['PRE_CLOSE_PRICE']
        daily_frame['rate'] = daily_frame['rate'].round(2)

        daily_frame['lrate'] = 100*(daily_frame['LOWEST_PRICE'] - daily_frame['PRE_CLOSE_PRICE'])/daily_frame['PRE_CLOSE_PRICE']
        daily_frame['lrate'] = daily_frame['lrate'].round(2)

        daily_frame['hrate'] = 100*(daily_frame['HIGHEST_PRICE'] - daily_frame['PRE_CLOSE_PRICE'])/daily_frame['PRE_CLOSE_PRICE']
        daily_frame['hrate'] = daily_frame['hrate'].round(2)

        daily_frame['TRADE_DATE'] = daily_frame['TRADE_DATE'].apply(lambda x: x.strftime("%Y-%m-%d"))

        # 复权数据，以便画k线图
        fq_daily_frame = common.get_mysqlData(daily_stock_list, common.getDate(n_day_before, self.running_day), db_table='vmkt_equd_adj')
        fq_daily_frame['rate'] = 100*(fq_daily_frame['CLOSE_PRICE'] - fq_daily_frame['PRE_CLOSE_PRICE'])/fq_daily_frame['PRE_CLOSE_PRICE']
        fq_daily_frame['rate'] = fq_daily_frame['rate'].round(2)

        fq_daily_frame['lrate'] = 100*(fq_daily_frame['LOWEST_PRICE'] - fq_daily_frame['PRE_CLOSE_PRICE'])/fq_daily_frame['PRE_CLOSE_PRICE']
        fq_daily_frame['lrate'] = fq_daily_frame['lrate'].round(2)

        fq_daily_frame['hrate'] = 100*(fq_daily_frame['HIGHEST_PRICE'] - fq_daily_frame['PRE_CLOSE_PRICE'])/fq_daily_frame['PRE_CLOSE_PRICE']
        fq_daily_frame['hrate'] = fq_daily_frame['hrate'].round(2)

        fq_daily_frame['TRADE_DATE'] = fq_daily_frame['TRADE_DATE'].apply(lambda x: x.strftime("%Y-%m-%d"))


        # 筛选出符合条件的股票
        # 连续3天以上涨停
        # condition1_frame = filter_stock_by_zt_condition(daily_frame, condition='ZT', zt_num=3)

        #{"concept":concept_frame, "concept":concept_frame2}
        # concept_frame: index TICKER_SYMBOL 5_chg 25_chg N_chg rank
        self.concept_rank_dict = {}
        for concept in self.concepts:
            print concept
            concept_stock_list = list(concept_frame[concept_frame.concept==concept].stockid.values)
            # 去除掉rmv对应的股票，以及加上mst对于的股票
            if concept in self.rmv_dict.keys():
                concept_stock_list = [x for x in concept_stock_list if x not in self.rmv_dict[concept]]

            if concept in self.mst_dict.keys():
                concept_stock_list.extend(self.mst_dict[concept])

            # 概念对应的所有股票的日线数据
            concept_daily_frame = daily_frame[daily_frame.TICKER_SYMBOL.isin(concept_stock_list)]
            # 统计出其涨幅排行
            concept_rank_chg_frame = add_rank_chg(concept_daily_frame, chg_days=[5, 25], sort_v=5)

            # 得到连续N个涨停以上的股票
            condition1_frame = filter_stock_by_zt_condition(daily_frame[daily_frame.TICKER_SYMBOL.isin(concept_stock_list)],
                                                            condition='ZT', zt_num=self.direct10_num[concept])
            # print concept,self.direct10_num[concept]

            # 得到涨幅排行前N的股票
            if len(condition1_frame) < 3:
                tail_n = 10 - len(condition1_frame)
            else:
                tail_n = 5
            stock_list = list(concept_rank_chg_frame.sort_values(by=['rank'], ascending=False).tail(tail_n).TICKER_SYMBOL.values)
            stock_list.extend(condition1_frame.TICKER_SYMBOL.values)

            # 再加上必须关注的股票
            if concept in self.mst_dict.keys():
                stock_list.extend(self.mst_dict[concept])

            stock_list = list(set(stock_list))
            # 记录到mongo中daily_interesting_concept_stocks
            self.write_mongo_concept_day(stock_list, concept, self.running_day)

            # 画图
            k_line_frame_list = []
            for stock in stock_list:
                stock_frame = fq_daily_frame[fq_daily_frame.TICKER_SYMBOL == stock][[u'TRADE_DATE', 'OPEN_PRICE', 'CLOSE_PRICE', 'HIGHEST_PRICE', 'LOWEST_PRICE',
                                                                       'TURNOVER_VOL', 'TICKER_SYMBOL', 'rate', 'lrate', 'hrate', 'SEC_SHORT_NAME']]
                stock_frame.columns=['date', 'open', 'close', 'high', 'low', 'volume', 'code', 'rate', 'lrate', 'hrate', 'name']
                stock_frame['name'] = stock_frame['name'].apply(lambda x: x.encode('gb2312'))
                # index row，date，open, close, high, low, volume, code
                # stock_frame = stock_frame.sort('date', ascending='True')
                stock_frame = stock_frame.sort_values(by=['date'], ascending='True')
                stock_frame.reset_index(inplace=True)
                stock_frame['name'] = stock_frame['name'].apply(lambda x: x.decode("gbk").encode("utf-8") )
                del stock_frame['index']
                k_line_frame_list.append(stock_frame)

            # 只显示感兴趣的股票的排行和涨幅数据
            concept_rank_chg_frame = concept_rank_chg_frame[concept_rank_chg_frame.TICKER_SYMBOL.isin(stock_list)]
            concept_rank_chg_frame = concept_rank_chg_frame.sort_values(by=['rank'], ascending=True)
            concept_rank_chg_frame['stock_name'] = concept_rank_chg_frame['TICKER_SYMBOL'].apply(lambda x: common.QueryStockMap(x)[0])
            names = [x for x in concept_rank_chg_frame.columns if x not in ['stock_name', 'TICKER_SYMBOL']]
            valid_name = ['stock_name']
            valid_name.extend(names)
            concept_rank_chg_frame = concept_rank_chg_frame[valid_name]

            # 构造一个OPTION4&6，左边为K线图，右边为条形图，以及下面一系列的k线图
            plot_frame_list = [[k_line_frame_list[0], concept_rank_chg_frame]]
            plot_frame_list.extend(k_line_frame_list[1:])

            html_types=['4and6']
            html_types.extend([4]*len(k_line_frame_list[1:]))

            title_list = [['A_stock', 'accum_ratio']]
            title_list.extend(['A_stocks']*len(k_line_frame_list[1:]))

            # 在加一个统计区间涨跌幅
            # range_ratio = {
            #     concept_name:[[start1, end1],[start2, end2], [start3, end3], ...],
            #     concept_name2:[[start1, end1],[start2, end2], [start3, end3], ...],
            # }

            # 说明该概念需要画出不同时期的涨跌幅对比
            if concept in self.range_ratio_dict.keys():
                range_ratio_frame = pd.DataFrame()
                for [sday, eday] in self.range_ratio_dict[concept]:
                    col_name = "%s-%s"%(common.format_date(sday, "%Y%m%d"), common.format_date(eday, "%Y%m%d"))
                    for stock in stock_list:
                        range_ratio_frame.loc[stock, col_name] = common.time_range_accum_ratio(stock, sday, eday)
                range_ratio_frame.reset_index(inplace=True)
                range_ratio_frame.rename(columns={"index":"stock_name"}, inplace=True)
                range_ratio_frame['stock_name'] = range_ratio_frame['stock_name'].apply(lambda x: common.QueryStockMap(x)[0])
                # 添加到画图中
                plot_frame_list.append(range_ratio_frame)
                html_types.append(7)
                title_list.append('ACCUM_RATIO')

            # 输出html
            common.get_html_curve(plot_frame_list, '%s' %(concept), html_types=html_types,
                      title_list = title_list, save_dir=os.path.join(self.dump_dir, self.running_day))
            logging.getLogger().info("plot html finished for %s, %s" %(concept, self.running_day))
        print "Finished for %s" %self.running_day

    # 记录在mongo中，格式为{date:"20170709", "concept":"XX", "STOCK1":True, "STOCK2":True, ...}
    def write_mongo_concept_day(self, stock_list, concept, day):
        pass
        # 写不进去，暂且不写
        # concept_stock_dict = {
        #     "date":common.format_date(day, "%Y%m%d"),
        #     "concept":concept
        # }
        # for stock in stock_list:
        #     concept_stock_dict[stock] = True
        # self.mongodb.stock.daily_interesting_concept_stocks.update({"date":day, "concept":concept},{"$set":concept_stock_dict}, True)

    # 将当天的html汇总到该页面，便于查看
    def daily_html_summary(self):
        scan_dir = os.path.join(self.dump_dir, self.running_day)
        fHandler = open(os.path.join(scan_dir, "integrate.html"), 'w')
        pre_content = u'''
        <div style="line-height:30px">
        <pre>
        <a href="%s" target="_blank">主页</a>
        <a href="%s" target="_blank">板块变化</a>
        \n''' % (os.path.join(self.path, "tree.html"), "ABC")
        fHandler.write(pre_content.encode("utf-8").replace("\t", ""))
        for hname in os.listdir(scan_dir):
            if ".html" in hname:
                concept_name = hname.replace(ur'.html', u'')
                if concept_name in [u'板块变化', u'integrate']:
                    continue
                line_content = u'\t<a href="%s" target="_blank">%s</a>\n'%(os.path.join(scan_dir, hname), concept_name)
                fHandler.write(line_content.encode("utf-8"))
        fHandler.write(u"</pre>".encode("utf-8"))
        fHandler.write(u"</div>".encode("utf-8"))


    def tree_html(self):
        filepath = os.path.join(self.path, "tree.html")
        dirname_list = []
        for dirname in os.listdir(self.dump_dir):
            if len(dirname) != 8 or (not dirname.isdigit()):
                continue
            dirname_list.append(dirname)
        dirname_list.sort(reverse=True)
        pre_content = u'<div style="line-height:30px">\n<pre>\n'
        with open(filepath, 'w') as fHandler:
            fHandler.write(pre_content.encode('utf-8'))
            for dname in dirname_list:
                daily_html = "%s/integrate.html" % (os.path.join(self.path, "tree/%s"%dname))
                line_content = u'\t<a href="%s" target="_blank">%s</a>\n' % (daily_html, dname)
                fHandler.write(line_content.encode("utf-8"))
            fHandler.write(u"</pre>".encode("utf-8"))
            fHandler.write(u"</div>".encode("utf-8"))
        logging.getLogger().info("Finish tree html")

if __name__ == '__main__':
    x = ThemeDigger(running_day="20170721")
    x.plot_stocks_html()