#coding:utf8
from mysqldb import *
import pandas as pd
import datetime
import os
import numpy as np
import tushare as ts
import time
import requests
import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')
import pymongo
from pandas import DataFrame,Series
import matplotlib.pyplot as plt
from Tkinter import *
from tkMessageBox import *
import Tkinter as tk
import json
import shutil
from lxml import etree

mongourl = "localhost"
global mongodb, backsee_csv
mongodb = pymongo.MongoClient(mongourl)
backsee_csv = u'D:/Money/modeResee/复盘'

# def connectdb():
#     mydbs='a'
#     mydb='b'
#     dydb='c'
#     localdb='a'
#     cardb='b'
#     souhudbs='c'
#     souhudbi='c'
#     return (mydbs,mydb,dydb,localdb,cardb,souhudbs,souhudbi)
#

# 仅限于在公司
def connectdb():
    # mydbs='a'
    # mydb='b'
    # dydb='c'
    mydbs=mysqldber({'host': 'db-bigdata-ro.wmcloud.com', 'user': 'app_bigdata_ro', 'pw': 'Welcome_20141217', 'db': 'bigdata', 'port': 3312})
    dydb  = mysqldber({'host': 'db-datayesdb-ro.wmcloud.com', 'user': 'app_gaea_ro', 'pw': 'EQw6WquhnCKPp8Li', 'db': 'datayesdbp', 'port': 3313})
    mydb = mysqldber({'host': '10.21.232.43', 'user': 'app_gaea_ro', 'pw': 'Welcome20150416', 'db': 'MarketDataL1', 'port': 5029})  ##分笔，分钟级
    # cardb = mysqldber({'host': 'db-news.wmcloud-stg.com', 'user': 'app_bigdata_ro', 'pw': 'Welcome_20141217', 'db': 'news', 'port': 3310})
    cardb = 'A'
    souhudbs = mysqldber({'host': 'db-datayesdb-ro.wmcloud.com', 'user': 'app_gaea_ro', 'pw': 'EQw6WquhnCKPp8Li', 'db': 'datayesdb', 'port': 3313})
    # souhudbi = mysqldb({'host': 'db-bigdata.wmcloud-qa.com', 'user': 'app_bigdata_ro', 'pw': 'Welcome_20141217', 'db': 'bigdata', 'port': 3312})
    souhudbi = 'a'
    # souhudbi = mydbs
    # localdb = mysqldb({'host': '127.0.0.1', 'user': 'root', 'pw': '', 'db': 'stock', 'port': 3306})
    localdb = None
    return (mydbs,mydb,dydb,localdb,cardb,souhudbs,souhudbi)

class mysqldata:
    def __init__(self):
        (self.mydbs,self.mydb,self.dydb,self.localdb,self.cardb,self.souhudbs,self.souhudbi)=connectdb()

    def dydbs_query(self,sqlquery):
        self.mydbs.db.ping(True)
        self.mydbs.db.cursor()
        return pd.read_sql(sqlquery,con=self.mydbs.db)

    def dydb_query(self,sqlquery):
        self.dydb.db.ping(True)
        self.dydb.db.cursor()
        return pd.read_sql(sqlquery,con=self.dydb.db)

    def mydb_query(self,sqlquery):
        self.mydb.db.ping(True)
        self.mydb.db.cursor()
        return pd.read_sql(sqlquery,con=self.mydb.db)

    def localdb_query(self,sqlquery):
        self.localdb.db.ping(True)
        self.localdb.cursor()
        return pd.read_sql(sqlquery,con=self.localdb.db)

    def car_query(self,sqlquery):
        self.cardb.db.ping(True)
        self.cardb.db.cursor()
        return pd.read_sql(sqlquery,con=self.cardb.db)

    def souhus_query(self,sqlquery):
        self.souhudbs.db.ping(True)
        self.souhudbs.db.cursor()
        return pd.read_sql(sqlquery,con=self.souhudbs.db)

    def souhui_query(self,sqlquery):
        self.souhudbi.db.ping(True)
        self.souhudbi.db.cursor()
        return pd.read_sql(sqlquery,con=self.souhudbi.db)
    ## stockid,stockname,concept1,concept2,concept3,concept4,concept5,concept6
    def generate_localdb_query(self,*args):
        id=args[0]
        name=args[1]
        item1=args[2]
        arrs=['NPC','NPC','NPC','NPC','NPC']
        for i in range(3,len(args)):
            arrs[i-3]=args[i]
        sqlcomd="insert into `stock_concept` values(%s,'%s','%s','%s','%s','%s','%s','%s')"%(id,name,item1,arrs[0],arrs[1],arrs[2],arrs[3],arrs[4])
        return sqlcomd


    def localdb_write(self,sqlquery):
        try:
            self.localdb.upload(sqlquery)
            return 1
        except Exception,e:
            return e

global mysqldb
mysqldb = mysqldata()

## [(2010,1),(2010,2)]
def get_ympair(sty,stm,eny,enm):
    tlist=[]
    cur_y=sty
    cur_m=stm
    while(True):
        tlist.append((cur_y,cur_m))
        if cur_m == 12:
            cur_m = 1
            cur_y += 1
        else:
            cur_m += 1

        if cur_y > eny:
            break
        elif (cur_y==eny) and (cur_m > enm):
            break
    return tlist

def get_day(value,str_date):
    calframe=pd.read_csv(os.path.join("D:\Money","cal.csv"))
    del calframe['0']
    calframe.columns=['Time']
    daylist=list(calframe['Time'].values)
    date_value=calframe[calframe.Time<=str_date].tail(1).Time.values
    index=daylist.index(date_value)
    tar_index=index+value
    tar_date=calframe.loc[tar_index,'Time']
    return tar_date




## 根据起始年月和终止年月，得到日期列表
## ["2015/01/01",'2015/01/02",...]
class gm_date:
    def __init__(self,sty,stm,eny,enm):
        self.sty=sty
        self.stm=stm
        self.eny=eny
        self.enm=enm
        self.run()

    def run(self):
        self.month_list=[]
        tmp_y=self.sty
        tmp_m=self.stm
        calframe=pd.read_csv(os.path.join("D:\Money","cal.csv"))
        del calframe['0']
        calframe.columns=['Time']
        start_day=datetime.date(year=self.sty,month=self.stm,day=1).strftime("%Y/%m/%d")
        try:
            end_day=datetime.date(year=self.eny,month=self.enm,day=31).strftime("%Y/%m/%d")
        except:
            try:
                end_day=datetime.date(year=self.eny,month=self.enm,day=30).strftime("%Y/%m/%d")
            except:
                try:
                    end_day=datetime.date(year=self.eny,month=self.enm,day=29).strftime("%Y/%m/%d")
                except:
                    try:
                        end_day=datetime.date(year=self.eny,month=self.enm,day=28).strftime("%Y/%m/%d")
                    except:
                            end_day=datetime.date(year=self.eny,month=self.enm,day=27).strftime("%Y/%m/%d")
        calframe=calframe[(calframe.Time>=start_day) & (calframe.Time<=end_day)]
        calList=calframe['Time'].values
        self.calList=list(calList)


## 根据起始年月和终止年月，得到日期列表
## ["2015/01/01",'2015/01/02",...]
def getDate(startdate,enddate):
    startdate = format_date(startdate,"%Y/%m/%d")
    enddate = format_date(enddate,"%Y/%m/%d")
    calframe=pd.read_csv(os.path.join("D:\Money","cal.csv"))
    del calframe['0']
    calframe.columns=['Time']
    calframe=calframe[(calframe.Time>=startdate) & (calframe.Time<=enddate)]
    calList=calframe['Time'].values
    return list(calList)

# 得到股票某日的情况
# 返回值为 涨幅，收盘是否涨停，收盘是否跌停，最高是否涨停，最低是否涨停
def get_day_k_status(stockid, date):
    try:
        dframe = get_mysqlData([stockid], [date])
        change_rate = round(100*(dframe.loc[0, 'CLOSE_PRICE'] - dframe.loc[0, 'PRE_CLOSE_PRICE'])/dframe.loc[0, 'PRE_CLOSE_PRICE'], 2)
        zt_price = round(1.1 * dframe.loc[0, 'PRE_CLOSE_PRICE'], 2)
        dt_price = round(0.9 * dframe.loc[0, 'PRE_CLOSE_PRICE'], 2)
        close_zt_status = (zt_price == dframe.loc[0, 'CLOSE_PRICE'])
        close_dt_status = (dt_price == dframe.loc[0, 'CLOSE_PRICE'])
        high_zt_status = (zt_price == dframe.loc[0, 'HIGHEST_PRICE'])
        low_dt_status = (zt_price == dframe.loc[0, 'LOWEST_PRICE'])
        return change_rate, close_zt_status, close_dt_status, high_zt_status, low_dt_status
    except:
        return None, None, None, None, None


## 输入格式不限
## 根据股票代码和日期获取交易数据
## 如果stock_list长度为0，则选出所有股票
## 输出dataFrame格式为：

#      TICKER_SYMBOL SEC_SHORT_NAME  TRADE_DATE  PRE_CLOSE_PRICE  OPEN_PRICE    HIGHEST_PRICE   LOWEST_PRICE  CLOSE_PRICE ACT_PRE_CLOSE_PRICE TURNOVER_VOL
# 0           000033          *ST新都  2016-04-27            10.38        0.00           0.00          0.00        10.38
# 1           600710          *ST常林  2016-04-27             9.36        0.00         10.61         10.52        10.57
# 一般情况用vmkt_equd（没有考虑复权），但是在判断是否涨停时必须用equd，而在算一段时间的涨跌幅时要用vmkt_equd_adj（复权数据）
def get_mysqlData(stock_list, date_list, db_table='vmkt_equd'):
    # mysqldb = mysqldata()
    global mysqldb
    stock_list_zs = [x for x in stock_list if u"ZS" in x]   # 指数
    stock_list = [str(x).replace('sh',"").replace('sz',"").replace(".","").replace("SH","").replace("SZ","") for x in stock_list if u'ZS' not in x]
    stock_list = ['0'*(6-len(str(x)))+str(x) for x in stock_list]
    date_list = [format_date(x,"%Y-%m-%d") for x in date_list]
    date_list = str(date_list).replace("[","(").replace("]",")")

    dataFrame = DataFrame()
    # 个股
    table= db_table
    if len(stock_list) > 0:
        stock_list = str(stock_list).replace("[","(").replace("]",")")
        query = "SELECT TICKER_SYMBOL, SEC_SHORT_NAME, TRADE_DATE, PRE_CLOSE_PRICE, OPEN_PRICE, HIGHEST_PRICE, LOWEST_PRICE, CLOSE_PRICE, ACT_PRE_CLOSE_PRICE, TURNOVER_VOL " \
                "from %s where TICKER_SYMBOL in %s and TRADE_DATE in %s"%(table,stock_list, date_list)
        dataFrame = mysqldb.dydb_query(query)
    # else:
    #     query = 'SELECT TICKER_SYMBOL, SEC_SHORT_NAME, TRADE_DATE, PRE_CLOSE_PRICE, OPEN_PRICE, HIGHEST_PRICE, LOWEST_PRICE, CLOSE_PRICE, ACT_PRE_CLOSE_PRICE  ' \
    #             'from %s where TRADE_DATE in %s and TICKER_SYMBOL < "700000" '%(table,date_list)
    # dataFrame = mysqldb.dydb_query(query)

    # 指数
    stock_list_zs = [x.replace("ZS", "") for x in stock_list_zs]
    stock_list_zs = ['0'*(6-len(str(x))) + str(x) for x in stock_list_zs]
    table = "vmkt_idxd"
    if len(stock_list_zs) > 0:
        stock_list_zs = str(stock_list_zs).replace("[","(").replace("]",")")
        query = "SELECT TICKER_SYMBOL, SEC_SHORT_NAME, TRADE_DATE, PRE_CLOSE_INDEX, OPEN_INDEX, HIGHEST_INDEX, LOWEST_INDEX, CLOSE_INDEX, TURNOVER_VOL " \
                "from %s where TICKER_SYMBOL in %s and TRADE_DATE in %s"%(table,stock_list_zs, date_list)
        dataFrame2 = mysqldb.dydb_query(query)
        dataFrame2.columns = ["TICKER_SYMBOL", "SEC_SHORT_NAME", "TRADE_DATE", "PRE_CLOSE_PRICE", "OPEN_PRICE", "HIGHEST_PRICE", "LOWEST_PRICE", "CLOSE_PRICE", "TURNOVER_VOL"]
        dataFrame2['ACT_PRE_CLOSE_PRICE'] = dataFrame2['PRE_CLOSE_PRICE']
        dataFrame = pd.concat([dataFrame, dataFrame2], axis=0)

    # 如果high或者low为0，则需要用close进行填充
    if len(dataFrame) > 0:
        dataFrame['OPEN_PRICE'] = dataFrame.apply(fill_sqlframe_na, args=('OPEN_PRICE',), axis=1)
        dataFrame['HIGHEST_PRICE'] = dataFrame.apply(fill_sqlframe_na, args=('HIGHEST_PRICE',), axis=1)
        dataFrame['LOWEST_PRICE'] = dataFrame.apply(fill_sqlframe_na, args=('LOWEST_PRICE',), axis=1)

    # for col in ['PRE_CLOSE_PRICE', "OPEN_PRICE", "HIGHEST_PRICE", "LOWEST_PRICE", "CLOSE_PRICE"]:
    #     dataFrame[col] = dataFrame[col].round(2)
    return dataFrame


def fill_sqlframe_na(df, col_name):
    if df[col_name] == 0:
        return df['CLOSE_PRICE']
    else:
        return df[col_name]

#      TICKER_SYMBOL SEC_SHORT_NAME  TRADE_DATE  PRE_CLOSE_PRICE  OPEN_PRICE    HIGHEST_PRICE   LOWEST_PRICE  CLOSE_PRICE  ACT_PRE_CLOSE_PRICE TURNOVER_VOL rate
# 0           000033          *ST新都  2016-04-27            10.38        0.00           0.00          0.00        10.38
# 1           600710          *ST常林  2016-04-27             9.36        0.00         10.61         10.52        10.57
# 单个股票
def get_single_ticker_tushare(ticker, start_date, end_date):
    start_date = format_date(start_date, '%Y-%m-%d')
    end_date = format_date(end_date, '%Y-%m-%d')
    x = ts.get_hist_data(ticker,start=start_date,end=end_date)
    x['PRE_CLOSE_PRICE'] = x['close'] - x['price_change']
    x.reset_index(inplace=True)
    x.rename(columns={"date":"TRADE_DATE","open":"OPEN_PRICE", "high":"HIGHEST_PRICE", "low":"LOWEST_PRICE",
                                   "close":"CLOSE_PRICE","volume":"TURNOVER_VOL", 'p_change':"rate"}, inplace=True)
    x['ACT_PRE_CLOSE_PRICE'] = x['PRE_CLOSE_PRICE']
    x['TICKER_SYMBOL'] = ticker
    x['SEC_SHORT_NAME'] = ts.get_realtime_quotes(ticker).name.values[0]
    x = x[['TICKER_SYMBOL', 'SEC_SHORT_NAME', 'TRADE_DATE', 'PRE_CLOSE_PRICE', 'OPEN_PRICE', 'HIGHEST_PRICE',
          'LOWEST_PRICE', 'CLOSE_PRICE', 'ACT_PRE_CLOSE_PRICE', 'TURNOVER_VOL', 'rate']]
    return x.sort("TRADE_DATE", ascending=True)

## 输入格式不限
# 承接上面的单个股票，这里是多个股票
## 根据股票代码和日期获取交易数据
## 和上面不同的是，stock_list必须有值，而且data_list为交易日的开始日期和结束日期
## 输出dataFrame格式为：

#      TICKER_SYMBOL SEC_SHORT_NAME  TRADE_DATE  PRE_CLOSE_PRICE  OPEN_PRICE    HIGHEST_PRICE   LOWEST_PRICE  CLOSE_PRICE  ACT_PRE_CLOSE_PRICE TURNOVER_VOL
# 0           000033          *ST新都  2016-04-27            10.38        0.00           0.00          0.00        10.38
# 1           600710          *ST常林  2016-04-27             9.36        0.00         10.61         10.52        10.57

def get_mysqlData_tushare(stock_list,start_date, end_date):
    frame_list = []
    for ticker in list(set(stock_list)):
        frame_list.append(get_single_ticker_tushare(ticker, start_date, end_date))
    tframe = pd.concat(frame_list, axis=0)
    tframe.reset_index(inplace=True)
    del tframe['index']
    return tframe

## 执行mysql，返回dataframe
def get_mysqlData_sqlquery(sqlquery):
    # mysqldb = mysqldata()
    global mysqldb
    dataFrame = mysqldb.dydb_query(sqlquery)
    return dataFrame

## 执行mysql，返回dataframe
def get_mydb_sqlquery(sqlquery):
    # mysqldb = mysqldata()
    global mysqldb
    dataFrame = mysqldb.mydb_query(sqlquery)
    return dataFrame

#             open  high  close   low     volume     amount    pre_close   change_rate
# date
# 2014-03-21  4.51  4.67   4.65  4.44  116133536  534399872    XXXX            0.1
# 得到股票在某一天,以及前一天的的交易数据
# 输入date为['2016-03-27']
def get_value(stoc_list,date):
    try:
        date = datetime.datetime.strptime(date,"%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        try:
            date = datetime.datetime.strptime(date,"%Y/%m/%d").strftime("%Y-%m-%d")
        except:
            try:
                date = datetime.datetime.strptime(date,"%Y%m%d").strftime("%Y-%m-%d")
            except:
                pass
    last_date=get_last_date(date)
    vframe=pd.DataFrame()
    # sqldb=mysqldata()
    global mysqldb
    sqldb = mysqldb
    #      TICKER_SYMBOL SEC_SHORT_NAME  TRADE_DATE  PRE_CLOSE_PRICE  OPEN_PRICE    HIGHEST_PRICE   LOWEST_PRICE  CLOSE_PRICE
# 0           000033          *ST新都  2016-04-27            10.38        0.00           0.00          0.00        10.38
# 1           600710          *ST常林  2016-04-27             9.36        0.00         10.61         10.52        10.57
    vframe = get_mysqlData(stoc_list,[date])
    vframe = vframe[['TICKER_SYMBOL','OPEN_PRICE','HIGHEST_PRICE','CLOSE_PRICE','LOWEST_PRICE','PRE_CLOSE_PRICE','TRADE_DATE']]
    vframe.columns=['stcid','open','high','close','low','pre_close','date']
    vframe['change_rate']=100*(vframe['close'].astype(np.float64)-vframe['pre_close'].astype(np.float64))/vframe['pre_close'].astype(np.float64).round(decimals = 2)
    # for stoc in stoc_list:
    #     ## this entry is to get data from tushare but too slow and too many exceptions
    #     # try:
    #     #     tmpframe=ts.get_h_data(stoc,start=last_date,end=date)
    #     # except:
    #     #     print "re-connect"
    #     #     time.sleep(5)
    #     #     tmpframe=ts.get_h_data(stoc,start=last_date,end=date)
    #     ##
    #     try:
    #         ## this entry is to get data from datayes database
    #         tmpframe=get_tushare_frame(stoc,last_date,date,sqldb)
    #         #             stcid open  high  close   low     volume     amount
    #         # date
    #         tframe=tmpframe[tmpframe.index==datetime.datetime.strptime(date,"%Y-%m-%d").date()]
    #         tframe['pre_close']=tmpframe[tmpframe.index==datetime.datetime.strptime(last_date,"%Y-%m-%d").date()].close.values[0]
    #         tframe['change_rate']=100*(float(tframe.close.values[0])-float(tframe.pre_close.values[0]))/float(tframe.pre_close.values[0])
    #         tframe['change_rate']=tframe['change_rate'].round(decimals=2)
    #         vframe=pd.concat([vframe,tframe],axis=0)
    #     except Exception,e:
    #         pass
    return vframe

#             stcid open  high  close   low     volume     amount
# date
# 2014-03-21  601989 4.51  4.67   4.65  4.44  116133536  534399872
# 得到股票在某一天以及前一天的交易数据，数据来源：数据库
# 输入date为['2016-03-27']
## 股票代码为：601989

def get_tushare_frame(stoc,last_date,date,sqldb):
    last_date = format_date(last_date,"%Y-%m-%d")
    date = format_date(date,"%Y-%m-%d")
    table="vmkt_equd"
    # sql='select TRADE_DATE,TICKER_SYMBOL,OPEN_PRICE,HIGHEST_PRICE,CLOSE_PRICE,LOWEST_PRICE,CLOSE_PRICE,CLOSE_PRICE from %s \
    #     where TICKER_SYMBOL="%s" and TRADE_DATE in ("%s","%s") order by TRADE_DATE DESC'%(table,stoc,date,last_date)
    sql = 'select TRADE_DATE,TICKER_SYMBOL,OPEN_PRICE,HIGHEST_PRICE,CLOSE_PRICE,LOWEST_PRICE,CLOSE_PRICE,CLOSE_PRICE from %s \
        where TICKER_SYMBOL = "%s" and TRADE_DATE in ("%s","%s") order by TRADE_DATE DESC'%(table,stoc,date,last_date)
    adata=sqldb.dydb_query(sql)

    adata.columns=['date','stcid','open','high','close','low','volume','amount']
    adata.set_index("date",inplace=True)
    return adata



# date为['2016-03-27'],output为['2016-03-26']
def get_last_date(date):
    calframe=pd.read_csv(os.path.join("D:\Money","cal.csv"))
    del calframe['0']
    calframe.columns=['Time']
    format_str = format_date(date,"%Y/%m/%d")
    index=calframe[calframe.Time==format_str].index
    last_index=index-1
    last_date=str(calframe.loc[last_index,:]['Time'].values[0])
    last_date = format_date(last_date,"%Y-%m-%d")
    return last_date

# 上一个交易日
# date为['2016-03-27'],output为['2016-03-26']
def get_lastN_date(date,n):
    calframe=pd.read_csv(os.path.join("D:\Money","cal.csv"))
    del calframe['0']
    calframe.columns=['Time']
    format_str=format_date(date,"%Y/%m/%d")
    index=calframe[calframe.Time <= format_str].tail(1).index.values[0]
    last_index= index-n
    if last_index > calframe.index.values[-1]:
        last_index = calframe.index.values[-1]
        last_date=str(calframe.loc[last_index,'Time'])
    else:
        last_date=str(calframe.loc[last_index,'Time'])
    last_date=datetime.datetime.strptime(last_date,"%Y/%m/%d").strftime("%Y-%m-%d")
    return last_date

## inDate: "2018-08-08","2018/08/08","20180808",或者date()类型
def format_date(inDate,formatType):
    inDate = str(inDate)
    try:
        formatDate=datetime.datetime.strptime(inDate,"%Y%m%d").strftime(formatType)
    except:
        try:
            formatDate=datetime.datetime.strptime(inDate,"%Y/%m/%d").strftime(formatType)
        except:
            try:
                formatDate=datetime.datetime.strptime(inDate,"%Y-%m-%d").strftime(formatType)
            except:
                try:
                    formatDate=inDate.strftime(formatType)
                except:
                    formatDate="20000000"
    return formatDate

#     TRADE_DATE    TICKER_SYMBOL  rate       type
# 0   2016-04-30      601989        10.01      ZT
# 1   2016-05-01

## 在一个frame中，根据close和preclose得到涨跌停对象
def get_zdt(tarframe,close,preclose):
    tarframe['ZT']=(tarframe[preclose].astype(np.float64)*1.1).round(2)
    tarframe['DT']=(tarframe[preclose].astype(np.float64)*0.9).round(2)
    tarframe['rate']=100*(tarframe[close].astype(np.float64)-tarframe[preclose].astype(np.float64))/tarframe[preclose].astype(np.float64)
    tarframe['rate']=tarframe['rate'].round(decimals=2)
    ztframe=tarframe[tarframe.CLOSE_PRICE>=tarframe.ZT][['TRADE_DATE','TICKER_SYMBOL','rate']]
    dtframe=tarframe[tarframe.CLOSE_PRICE<=tarframe.DT][['TRADE_DATE','TICKER_SYMBOL','rate']]
    ztframe['type']=np.array(['ZT']*len(ztframe))
    dtframe['type']=np.array(['DT']*len(dtframe))
    return ztframe,dtframe

## 判断股票是否强势,如果成交量比前6日的成交量还要大，暂定为巨量
## date格式任意
## vol为当前成交量，支持盘中
def volStatus(stoc,date,vol):
    try:
        date = format_date(date,"%Y-%m-%d")
        pre_date=get_lastN_date(date,6)
        vframe=ts.get_h_data(stoc,start=pre_date,end=date)
        print "------------------%s,%s,%s-------------------------"%(stoc,pre_date,date)
        vframe.index=pd.to_datetime(vframe.index.values)
        ## remove the same date as compared
        if datetime.datetime.strptime(date,'%Y-%m-%d').date() == vframe.index[0].date():
            vframe.drop(vframe.index.values[0],inplace=True)
        if float(vol) > 1.5*float(max(vframe.volume.values)):
            return 1
        else:
            return 0
    except:
        return 0

#slist 为字符串list，可以包含sh，也可以不包含,位数可以是6位，也可以不为6位
# output
#        time        date   stcid  close  preclose   high    low  vol  amount  rate    name
# 0  11:15:12  2016-04-07  002785  27.20     25.08  27.50  25.00  115516   3.01   8.45    中国重工
# 1  11:15:12  2016-04-07  603866  33.36     32.94  33.75  32.95   34952   1.17   1.28    招商银行
def get_sina_data(slist):
    stoc=slist[0]
    if stoc[:2] in ["sh","sz"]:
        pass
    else:
        slist=[str(x) if (len(str(x))==6) else'0'*(6-len(str(x)))+str(x) for x in slist]
        slist=["sh"+str(x) if str(x)[:2] in ["60","90"] else "sz"+str(x) for x in slist]
    aframe = pd.DataFrame()
    if len(slist) > 200:
        for i in range(0,len(slist)/200+1):
            if i != len(slist)/200:
                tmpslist = slist[200*i:200*(i+1)]
            else:
                tmpslist = slist[200*i:]

            tmpframe = get_little_sina_data(tmpslist)
            aframe = pd.concat([aframe,tmpframe],axis=0)
    else:
        aframe = get_little_sina_data(slist)
    return aframe

def get_little_sina_data(slist):
    str_list=",".join(slist)
    url = "http://hq.sinajs.cn/list=%s"%str_list
    #     print url
    try:
        r=requests.get(url)
    except:
        r=requests.get(url)
    content=r.content.decode('gbk')
    Dframe=parse_content(content)
    return Dframe


## 解析从新浪下载的数据
def parse_content(content,timestamp=time.strftime("%X",time.localtime())):
    Inframe=DataFrame()
    i = 0
    strarray=content.split(';')
    for item in strarray:
        item_array=item.split(',')
        if len(item_array)<10:
            continue
        stockid = item_array[0][14:20]
        stockid = item_array[0].split('=')[0].split('str_')[1][2:]
        stockname = item_array[0].split("=")[1].replace('"','')
        open = item_array[1]
        close = item_array[3]
        preclose = item_array[2]
        high = item_array[4]
        low = item_array[5]
        vol = item_array[8]   ##成交量，股
        amount = item_array[9]  ##成交额，元


        if close == '0.00':
            continue
        Inframe.loc[i,'time']=timestamp
        Inframe.loc[i,'date']=datetime.date.today()
        Inframe.loc[i,'stcid']=stockid
        Inframe.loc[i,'name']=stockname
        Inframe.loc[i,'close']=round(float(close),2)
        Inframe.loc[i,'preclose']=round(float(preclose),2)
        Inframe.loc[i,'high']=round(float(high),2)
        Inframe.loc[i,'low']=round(float(low),2)
        Inframe.loc[i,'vol']=round(float(vol),0)
        Inframe.loc[i,'amount']=round(float(amount),0)
        i+=1

    Inframe['rate']=100*(Inframe['close'].astype(np.float64)-Inframe['preclose'].astype(np.float64))/Inframe['preclose'].astype(np.float64)
    Inframe['rate']=Inframe['rate'].round(decimals=2)
    # Inframe['hate']=100*(Inframe['high'].astype(np.float64)-Inframe['preclose'].astype(np.float64))/Inframe['preclose'].astype(np.float64)
    # Inframe['hate']=Inframe['hate'].round(decimals=2)
    return Inframe

## 根据日期，更新连续涨跌停个数
def update_numZD(cdate,predate,mongodb):
    num_ucont={"2":0,"3":0,"4":0,"5":0,"6":0,"+6":0}    #连张股票个数统计
    stoc_ucont={"1":[],"2":[],"3":[],"4":[],"5":[],"6":[],"+6":[]}   #连涨股票代码
    num_dcont={"2":0,"3":0,"4":0,"5":0,"6":0,"+6":0}    #连张股票个数统计
    stoc_dcont={"1":[],"2":[],"3":[],"4":[],"5":[],"6":[],"+6":[]}   #连涨股票代码

    predate = format_date(predate,"%Y%m%d")
    tDicts=mongodb.stock.ZDT_by_date.find_one({"date":predate})
    print predate,cdate
    if tDicts.has_key('details'):
        stoc_ucont=tDicts['details']["stoc_ucont"]
        stoc_dcont=tDicts['details']["stoc_dcont"]

    if tDicts.has_key('num_ucont'):
        num_ucont=tDicts["num_ucont"]
        num_dcont=tDicts["num_dcont"]

    cdate = format_date(cdate,"%Y%m%d")
    cDicts=mongodb.stock.ZDT_by_date.find_one({"date":cdate})
    # zt_list=cDicts['ZT_stocks'].split("_")
    zt_list=cDicts['actulZtStocks'].split("_")  ##去除次新股影响
    dt_list=cDicts['DT_stocks'].split("_")

    ##去除重复的股票
    zt_num = len(set(zt_list))
    zt_list_str="_".join(set(zt_list))
    dt_num = len(set(dt_list))
    dt_list_str="_".join(set(dt_list))

    if zt_num == 1:
        if zt_list[0] == u'':
            zt_num = 0

    if dt_num == 1:
        if dt_list[0] == u'':
            dt_num = 0

    zt_list = list(set(zt_list))
    dt_list = list(set(dt_list))
    if dt_list == [""]:
        dt_list=[]
    (stoc_ucont,num_ucont,stoc_dcont,stoc_dcont)=cont_stat(zt_list,dt_list,num_ucont,stoc_ucont,num_dcont,stoc_dcont)
    dicts={
    "details":{
        "stoc_ucont":stoc_ucont,
        "stoc_dcont":stoc_dcont},
    "num_ucont":num_ucont,
    "num_dcont":num_dcont
    }
    write_mongo(mongodb,cdate,dicts,zt_num,zt_list_str,dt_num,dt_list_str)


## 用来计算连续涨跌停个数
def cont_stat(zt_list,dt_list,num_ucont,stoc_ucont,num_dcont,stoc_dcont):
        ## 涨停
        pre_up6=stoc_ucont['+6']+stoc_ucont['6']
        stoc_ucont['+6']=[x for x in zt_list if x in pre_up6]
        num_ucont['+6']=len(stoc_ucont['+6'])
        for num in [6,5,4,3,2]:
            last_num="%s"%(num-1)
            num = "%s"%num
            pre_up=stoc_ucont[last_num]
            stoc_ucont[num]=[x for x in zt_list if x in pre_up]
            num_ucont[num]=len(stoc_ucont[num])
        stoc_ucont["1"]=zt_list

        ##跌停
        pre_dn6=stoc_dcont['+6']+stoc_dcont['6']
        stoc_dcont['+6']=[x for x in dt_list if x in pre_dn6]
        num_dcont['+6']=len(stoc_dcont['+6'])
        for num in [6,5,4,3,2]:
            last_num="%s"%(num-1)
            num = "%s"%num
            pre_dn=stoc_dcont[last_num]
            stoc_dcont[num]=[x for x in dt_list if x in pre_dn]
            num_dcont[num]=len(stoc_dcont[num])
        stoc_dcont["1"]=dt_list
        return (stoc_ucont,num_ucont,stoc_dcont,stoc_dcont)

def write_mongo(mongo,date,dicts,ztNum,ztStr,dtNum,dtStr):
    mongo_obj=mongo.report
    try:
        format_date=datetime.datetime.strptime(date,"%Y-%m-%d").strftime("%Y%m%d")
    except:
        try:
            format_date=datetime.datetime.strptime(date,"%Y/%m/%d").strftime("%Y%m%d")
        except:
            format_date=datetime.datetime.strptime(date,"%Y%m%d").strftime("%Y%m%d")
    obj_mongo=mongo.stock.ZDT_by_date.find_one({"date":format_date})
    if obj_mongo:

        mongo.stock.ZDT_by_date.update_one({"date":format_date},
                                   {"$set":{
                                       "details":dicts['details'],
                                       "num_ucont":dicts["num_ucont"],
                                       "num_dcont":dicts["num_dcont"],
                                       "ZT_num":ztNum,
                                       "DT_num":dtNum,
                                       # "ZT_stocks":ztStr,
                                       # "DT_stocks":dtStr
                                    }
                                   })
        print "successfully update,%s"%format_date

## 根据日期类型，查询mongo中的类型
def get_mongoDicts(dateEq='19890928',dateStart = '19890928', dateEnd = '19890928'):
    mongoUrl = "localhost"
    mongodb = pymongo.MongoClient(mongoUrl)
    dateEq = format_date(dateEq, "%Y%m%d")
    dateStart = format_date(dateStart, "%Y%m%d")
    dateEnd = format_date(dateEnd, "%Y%m%d")
    if dateEq != "19890928":
        dateDicts=mongodb.stock.ZDT_by_date.find({"date":dateEq})
    elif dateEnd != "19890928":
        dateDicts=mongodb.stock.ZDT_by_date.find({"date":{"$gte":dateStart,"$lte":dateEnd}})
    elif dateStart != "19890928":
        dateDicts=mongodb.stock.ZDT_by_date.find({"date":{"$gte":dateStart}})
    else:
        dateDicts = None

    return dateDicts


##画图
# 通过x指定x轴
# 通过y=[[],[]]指定每一个子subplot中的列
# point代表多少个刻度
# marker代表是否用o标注数据
def plotFrame(dataFrame,x='',y=[],titles=[],point=100, marker=False):

    colors = ['r','b','y','g','m','c','y','k']
    fz = 8

    listLabels = ''
    if x != "":
        listLabels = dataFrame[x].values
    step = len(dataFrame)/point
    baseline = range(len(dataFrame)/step+1)
    baseline = [int(x) * step for x in baseline]
    fig = plt.figure(figsize=(12,8))
    count = 221

    for groupNum in range(len(y)):
        groups = y[groupNum]
        ax = fig.add_subplot(count)
        if len(titles) >0:
            ax.set_title("%s"%titles[groupNum])

        lines=[]
        des=[]

        group = groups[0]
        line1,=ax.plot(dataFrame.index,dataFrame[group].values,'r-',label=group)
        if marker:
            line12,=ax.plot(dataFrame.index,dataFrame[group].values,'ro',label=group)
        ax.grid(True)
        ax.set_xticks(baseline)
        ax.set_ylim([min(dataFrame[group].values),max(dataFrame[group].values)])
        if len(listLabels) > 1:
            ax.set_xticklabels(listLabels[baseline],fontsize=fz)
        ax.set_xlim([min(dataFrame.index.values),max(dataFrame.index.values)])
        lines.append(line1)
        des.append(group)

        if len(groups)  == 2:
            group = groups[1]
            ax2=ax.twinx()
            line2,=ax2.plot(dataFrame.index,dataFrame[group].values,'b-',label=group)
            if marker:
                line22,=ax2.plot(dataFrame.index,dataFrame[group].values,'bo',label=group)
            ax2.grid(True)
            ax2.set_xticks(baseline)
            ax2.set_ylim([min(dataFrame[group].values),max(dataFrame[group].values)])
            lines.append(line2)
            des.append(group)

        ax.legend(lines,des)
        # ax1.legend([line11,line12,line13],('up10%','dn10%','sh_change'),'upper left',ncol=3)
        # plt.show()
        count += 1

    plt.show()

#查找数据库中的股票,name可以是股票代码，也可以是股票名字
# 返回是['中国重工', 601989]
def QueryStockMap(id='',name=''):
    global mongodb

    try:
        if id == 'ZS000001':
            return [u'上证指数', u'ZS000001']
        if id != '':
            id = str(int(float(id)))
            id = "0" * (6-len(id)) + id
            # queryResult = mongodb.stock.stockmap.find_one({"stockid":id})
            queryResult = mongodb.stock.stockmap.find({"stockid":id}).sort("updatetime",pymongo.DESCENDING)[0]
            if queryResult is not None:
                return [queryResult['stock_name'],queryResult['stockid']]
            else:
                return ["",""]
        elif name != '':
            # queryResult = mongodb.stock.stockmap.find_one({"stock_name":name})
            queryResult = mongodb.stock.stockmap.find({"stock_name":name}).sort("updatetime",pymongo.DESCENDING)[0]
            if queryResult is not None:
                return [queryResult['stock_name'],queryResult['stockid']]
            else:
                print "don't find the match ,name:%s, id:%s" %(name, id)
                return ["",""]
        else:
            print "don't find the match ,name:%s, id:%s" %(name, id)
            return ["",""]
    except:
        print "don't find the match ,name:%s, id:%s" %(name, id)
        return ["",""]

# 根据条件，对stockList中的股票进行弹窗提示，返回符合条件的List,股票代码
def WindowShow(stockList, operate, number, message):
    result = set()
    curframe = get_sina_data(stockList)
    number = float(number)
    if "g" in operate:
        tarframe = curframe[curframe.rate >= number]
    elif "l" in operate:
        tarframe = curframe[curframe.rate <= number]

    if len(tarframe) < 1:
        return result

    telllist = tarframe.stcid.values
    tellname = tarframe.name.values
    tellstr = "_".join(telllist)
    tellnamestr = "_".join(tellname)
    # showinfo(message, "---- %s ------\n%s\n%s" % (message,tellstr, tellnamestr))
    showinfos("---- %s ------\n\n%s\n\n%s" % (message,tellstr, tellnamestr))
    return telllist

def showinfos(message):
    return
    root = tk.Tk()
    # root.withdraw()
    root.title("Say Hello")
    label = tk.Label(root, text=message)
    label.pack(side="top", fill="both", expand=True, padx=20, pady=20)
    button = tk.Button(root, text="OK", command=lambda: root.destroy())
    button.pack(side="bottom", fill="none", expand=True)
    root.mainloop()
    print "will return"


def get_realtime_news(stock):
    count = 3
    news = ""
    r = requests.get("http://www.yuncaijing.com/stock/get_line/"+stock)
    while r.status_code != 200 or count < 0:
        r = requests.get("http://www.yuncaijing.com/stock/get_line/"+stock)
        time.sleep(5)
        count -= 1
    if r.status_code != 200:
        return news
    contents = json.loads(r.content)
    jsonContent = contents['data']['lEvtNews']
    news = parse_news(jsonContent)
    return news

def get_hist_news(stock):
    count = 10
    news = ""
    r = requests.get("http://www.yuncaijing.com/stock/get_kline/"+stock)
    while r.status_code != 200 or count < 0:
        r = requests.get("http://www.yuncaijing.com/stock/get_kline/"+stock)
        time.sleep(5)
        count -= 1
    contents = json.loads(r.content)
    jsonContent = contents['data']['kEvtNews']
    news = parse_news(jsonContent)
    return news

def parse_news(jsonContent):
    news = ""
    if jsonContent is None:
        return news
    count = 5
    try:
        keys = jsonContent.keys()
        keys.sort()
        for key in keys:
            if count < 1:
                break
            # news = news + "%s %s, %s\n" % (jsonContent[key]['date'], jsonContent[key]['time'], jsonContent[key]['title'])
            news = news + "%s, %s\n" % (jsonContent[key]['day'], jsonContent[key]['title'])
            count -= 1
    except:
        for dictContent in jsonContent:
            if count < 1:
                break
            news += "%s, %s\n" % (dictContent['day'].replace("<kbd>","").replace("<\\/kbd>",""), dictContent['title'])
            count -= 1
    return news

def get_latest_news(stock):
    stock = '0'*(6-len(stock))+stock
    count = 10
    print "get news for %s" % stock
    real_content = ''
    hist_content = ''
    # tmp
    # return ""
    try:
        # 首先看实时新闻
        real_content = get_realtime_news(stock)
    except:
        real_content = 'no valid news\n'

    try:
        # 再看历史新闻
        hist_content = get_hist_news(stock)
    except Exception,err:
        hist_content = 'no valid news\n'

    news = real_content + hist_content
    return news

# 某只股票，某段时间内的涨停情况
def zt_stats(stcid, start_date, end_date):
    global mongodb
    end_date = format_date(end_date, "%Y%m%d")
    start_date = format_date(start_date, "%Y%m%d")
    ZTFrame = DataFrame()
    HDFrame = DataFrame()
    results = mongodb.stock.ZDT_by_date.find({"date":{"$gte":start_date, "$lte":end_date}})
    i = 0
    j = 0
    for result in results:
        if "ZT_stocks" in result.keys() and stcid in result['ZT_stocks'].split("_"):
            ZTFrame.loc[i, "zt_date"] = result['date']
            i += 1

        elif "HD_stocks" in result.keys() and stcid in result['HD_stocks'].split("_"):
            HDFrame.loc[j, "hd_date"] = result['date']
            j += 1
    return ZTFrame, HDFrame

## 添加均线,利用CLOSE_PRICE,得到mean5,mean10,mean20...
def add_mean(dframe):
    for ma in [5,10,20,60,120]:
        dframe['mean%s'%ma]=dframe['CLOSE_PRICE'].rolling(window=ma).mean()

# 得到股票代码在某些天内的日线数据
# 格式匹配交割单图
# 1代表个股，0代表指数
def get_daily_frame(code, start_date, end_date, id_type = 1):
    if id_type == 1:
        code = "0"*(6-len(str(int(code))))+str(int(code))
        sql = "SELECT TICKER_SYMBOL, SEC_SHORT_NAME, TRADE_DATE, PRE_CLOSE_PRICE, OPEN_PRICE, HIGHEST_PRICE, LOWEST_PRICE, CLOSE_PRICE, \
        DEAL_AMOUNT from vmkt_equd_adj where TRADE_DATE >= '%s' and TRADE_DATE <='%s' and TICKER_SYMBOL = '%s'"%(start_date,end_date,code)
        sub = get_mysqlData_sqlquery(sql)
    elif id_type == 0:
        # idxcode = "000001"
        if code not in ["000001", "399006"]:
            idxcode = "000001"
        else:
            idxcode = code
        idxsql = "SELECT TICKER_SYMBOL, SEC_SHORT_NAME, TRADE_DATE, PRE_CLOSE_INDEX, OPEN_INDEX, HIGHEST_INDEX, LOWEST_INDEX, CLOSE_INDEX, \
        TURNOVER_VOL from vmkt_idxd where TRADE_DATE >= '%s' and TRADE_DATE <='%s' and TICKER_SYMBOL = '%s'"%(start_date,end_date,idxcode)
        sub = get_mysqlData_sqlquery(idxsql)
        sub.columns=[["TICKER_SYMBOL", "SEC_SHORT_NAME", "TRADE_DATE", "PRE_CLOSE_PRICE", "OPEN_PRICE", "HIGHEST_PRICE", "LOWEST_PRICE", "CLOSE_PRICE", "DEAL_AMOUNT"]]
    add_mean(sub)
    return sub

# 得到股票代码在某天内的分钟级数据
# 格式匹配交割单图
# 1代表个股，0代表指数
def get_minly_frame(stockid, endDate, id_type =1):
    tableTime = format_date(endDate,"%Y%m")
    endDate = format_date(endDate,"%Y%m%d")
    if id_type == 1:    # 个股
        if int(float(stockid)) < 600000:
            exchange = 'XSHE'   # 深圳
        else:
            exchange = 'XSHG'   # 上海
        # stockid = "0"*(6-len(str(int(float(stockid)))))+str(int(float(stockid)))
        stockid = int(float(stockid))
        # print stockid
        # table = "equity_pricefenbi%s"%tableTime
        table = "MarketDataTDB.equity_pricemin%s"%tableTime
        dtsql = 'SELECT * from %s where ticker = %s and datadate = %s and exchangecd = "%s"'%(table,stockid,endDate, exchange)
        dtv = get_mydb_sqlquery(dtsql)
        if len(dtv) == 0:
            table = "MarketDataL1.equity_pricemin%s"%tableTime
            dtsql = 'SELECT * from %s where ticker = %s and datadate = %s and exchangecd = "%s"'%(table,stockid,endDate, exchange)
            dtv = get_mydb_sqlquery(dtsql)
    else:
        table = "MarketDataTDB.equity_pricemin%s"%tableTime
        zssql = 'SELECT * from %s where datadate = %s and ticker = 1 and shortnm = "上证指数"'%(table,endDate)
        dtv = get_mydb_sqlquery(zssql)
        if len(dtv) == 0:
            table = "MarketDataTDB.equity_pricemin%s"%tableTime
            zssql = 'SELECT * from %s where datadate = %s and ticker = 1 and shortnm = "上证综指"'%(table,endDate)
            dtv = get_mydb_sqlquery(zssql)
    return dtv

# 得到股票代码在某天内的分钟级数据
# datadate, datatime, ticker, exchangecd, lastprice, volume, side
def get_fenbi_frame(stockid, endDate):
    tableTime = format_date(endDate,"%Y%m")
    endDate = format_date(endDate,"%Y%m%d")
    stockid = "0"*(6-len(str(int(stockid))))+str(int(stockid))
    # table = "equity_pricefenbi%s"%tableTime
    if int(stockid) < 600000:
        exchange = 'XSHE'   # 深圳
    else:
        exchange = 'XSHG'   # 上海
    table = "MarketDataTDB.equity_pricefenbi%s"%tableTime
    dtsql = 'SELECT * from %s where ticker = %s and datadate = %s and  exchangecd = "%s"'%(table, int(stockid), int(endDate), exchange)
    dtv = get_mydb_sqlquery(dtsql)
    if len(dtv) == 0:
        table = "MarketDataL1.equity_pricefenbi%s"%tableTime
        dtsql = 'SELECT * from %s where ticker = %s and datadate = %s and exchangecd = "%s"'%(table, int(stockid), int(endDate), exchange)
        dtv = get_mydb_sqlquery(dtsql)
    return dtv

# generate a html file
'''
series =
[
    {
        name: '3քָ˽',
        type: 'line',
        data: [1, 3, 9, 27, 81, 247, 741, 2223, 6669]
    },
    {
        name: '2քָ˽',
        type: 'line',
        data: [1, 2, 4, 8, 16, 32, 64, 128, 256]
    },
    {
        name: '1/2քָ˽',
        type: 'line',
        data: [1/2, 1/4, 1/8, 1/16, 1/32, 1/64, 1/128, 1/256, 1/512]
    }
]
'''



# 将frame_work中的option进行替换，方便自由组合，options是准备好的text, 为list
# option分顺序
def set_frameWork_option(options):
    count = 1
    toption = []    # 最后网页中的总option
    for option in options:
        option = option.replace("option", "option%s"%count)
        toption.append(option)
        count += 1
    toption = ";\n".join(toption) + ";"
    return toption, count


# flag_list分别代表龙头，跟风，排除
# 再加上excel中指定的众多类型
def gen_checkbox_form(stock_code, flag_list):
    [v1, v2, v3] = ['checked="checked"' if x else "" for x in flag_list]

    cbase1 = '<form action="" method="get">'
    checkbox_base = '''
    <label><input id="Dragon_%s" type="checkbox" %s  />龙头 </label>
    <label><input id="Wind_%s" type="checkbox" %s  />跟风 </label>
    <label><input id="Remove_%s" type="checkbox" %s />排除 </label>
    ''' % (stock_code, v1, stock_code, v2, stock_code, v3)

    checkbox_append_list = []
    # 读取excel中的内容
    dframe = pd.read_excel(os.path.join(u'D:/Money/modeResee/彼战', u'战区.xlsx'), encoding='gbk', sheetname=u'类型')
    for idx in dframe.index.values:
        code_str = dframe.loc[idx, u'源码']
        name_str = dframe.loc[idx, u'网页标识']
        str_v = u'<label><input id="%s_%s" type="checkbox" />%s </label>' % (code_str, stock_code, name_str)
        checkbox_append_list.append(str_v.encode("utf-8"))
    checkbox_append = "\n".join(checkbox_append_list)
    check_base2 = "</form>"
    checkbox_base = cbase1 + checkbox_base + checkbox_append + check_base2
    return checkbox_base





# 根据option的个数，动态调整网页中的图表个数
# gdate为生成html的日期，str类型，格式为 20170908
def set_frameWork_charts(count, gdate, width=1600, height=400, chart_connect=0, plot_stock_list=[], html_name='AAA'):
    inner_base = '''
    var myChartNum = ec.init(document.getElementById('chartdivNum'));
    myChartNum.setOption(optionNum);
    '''

    dragon_list = []
    wind_list = []
    # 各个板块的龙头
    concept_dragon_list = get_concept_dragon_list(gdate)
    if html_name in concept_dragon_list.keys():
        if 'dragon' in concept_dragon_list[html_name].keys():
            dragon_list = concept_dragon_list[html_name]['dragon']
        if 'wind' in concept_dragon_list[html_name].keys():
            wind_list = concept_dragon_list[html_name]['wind']


    front_base = '<div id="chartdivNum" style="width:%spx;height:%spx"></div>' % (width, height)

    inner = []
    front = []
    for i in range(1, count):
        inner.append(inner_base.replace("Num", str(i)))
        front.append(front_base.replace("Num", str(i)))
        stock_code = str(plot_stock_list[i-1])
        if len(stock_code) == 6:
            if stock_code in dragon_list:
                flag_list = [True, False, False]    # 龙头，跟风，排除
            elif stock_code in wind_list:
                flag_list = [False, True, False]
            else:
                flag_list = [False, False, False]
            txt = gen_checkbox_form(stock_code, flag_list)
            front.append("%s%s%s"%("\n", txt, "\n"))

    inner = "\n".join(inner)
    front = "\n".join(front)
    # 增加记录按钮
    button = u'\n<input type="button" value="记录" onClick="checkCheckBox();" />'.encode("utf-8")
    front += button

    # 所有的都要连接到一起
    if chart_connect == 1:
        str_pre = "echarts.connect(["
        for i in range(1, count):
            if i != count-1:
                str_pre += "myChart%s," % i
            else:
                str_pre += "myChart%s" % i
        str_pre += "]);"
        inner += "\n%s" % str_pre
    return front, inner

# LEGEND_REPLACE = ['legendA','legendB']
# dframe 列必须为： index  bartime, stockid1, stockid2, ...
# 根据dframe的每一个stockid列，生成一个曲线，可以点击取消
def curve_option1(dframe, title = "compare", html_src = os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", "")):
    with open(os.path.join(html_src, "OPTION1.html"), 'rb') as fHandler:
        x = fHandler.read()
    list_series = []
    list_legend = []
    for index in range(1, len(dframe.columns)):
        name = dframe.columns[index]        # 股票ID
        # print name
        data_list = str(list(dframe.loc[:, name]))
        time_list = str(list(dframe.loc[:, 'barTime']))
        time_list = time_list.replace("u", "")
        # data = str([[time_list[i], data_list[i]] for i in range(len(data_list))])
        c_name = QueryStockMap(id = name)[0].encode("utf-8")
        if 'ZS' in name:
            yAxis = 1
            tmp_dict = {
                "name":c_name,
                "type":'line',
                "data":data_list,
                "yAxisIndex":yAxis,
                "itemStyle": {"normal":{"type":'dashed', "color":'rgba(255, 255, 0, 0.8)'}}
            }
        else:
            yAxis = 0
            tmp_dict = {
                "name":c_name,
                "type":'line',
                "data":data_list,
                "yAxisIndex":yAxis,
            }
        if len(c_name) < 0:
            c_name = name
        list_legend.append(c_name)
        list_series.append(tmp_dict)
    list_series = list2str(list_series, delimiter="")
    list_series = list_series.replace('"[','[').replace(']"',"]")
    list_legend = list2str(list_legend)
    text = x.replace("SERIES_REPLACE", list_series).replace("LEGEND_REPLACE", list_legend).replace("XAXIS_REPLACE", time_list).replace("TITLE", title)
    return text


# group: [[0,0,2, "中信国安_银鸽投资"], [], [], ...]
# character: "ZT"
# concepts: 股权_上国改_...
# days: 1201_1202_1203...
def get_dataframe_option3(detail_group, concepts, days, character):
    dframe = DataFrame()
    for i in range(0, len(detail_group)):
        dframe.loc[i, 'row'] = detail_group[i][0]
        dframe.loc[i, 'column'] = detail_group[i][1]
        dframe.loc[i, 'num'] = detail_group[i][2]
        dframe.loc[i, 'stocks'] = detail_group[i][3]
    dframe['comment'] = np.array([1]*len(dframe))
    dframe.iloc[-1, -1] = concepts
    dframe.iloc[-2, -1] = days
    dframe.iloc[-3, -1] = character
    return dframe


# 为option1准备dataframe, 如果是指数，则可以配置扩大涨跌幅
def get_dataframe_option1(stock_list, date, zs_amplifier = 1):
    dframe = DataFrame()
    date = format_date(date, "%Y-%m-%d")
    stock_list = list(set(stock_list))
    # stock_list = ['601800', '600528']
    dframe_list = []
    for stock in stock_list:
        if stock == u'ZS000001':    # 上证指数
            tmp_frame = get_minly_frame(stock, date, id_type=0)
            zs_amplifier = 1
        else:
            tmp_frame = get_minly_frame(stock, date)
        tmp_frame = tmp_frame[['bartime', 'closeprice']]
        yesterday = get_lastN_date(date, 1)
        yeframe = get_mysqlData([stock],[yesterday])
        if len(yeframe) > 0:
            pre_close = yeframe.loc[0,'CLOSE_PRICE']
        else:
            pre_close = 10000
        # 计算涨跌幅，可以扩大幅度
        tmp_frame['closeprice'] = zs_amplifier * normalize_frame(tmp_frame['closeprice'], pre_close)
        tmp_frame.columns = ['barTime', stock]
        tmp_frame.set_index('barTime', inplace=True)
        dframe_list.append(tmp_frame)
    dframe = pd.concat(dframe_list, axis=1)

    dframe.reset_index(range(len(dframe)), inplace=True)
    return dframe


# dframe 格式为： index row，column，num，stocks，comment
# comment列最后一个是concepts_concepts_..., 该列倒数第二个是day_day_day..., 倒数第三个是title
# 据此生成html
def curve_option3(dframe, html_src=os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", "")):
    # 先还原出来data
    # dframe['data'] = dframe['row'] + "," + dframe['column'] + "," + dframe['num'] + dframe['stocks']
    data = []
    for idx in dframe.index.values:
        data.append([dframe.loc[idx, 'row'], dframe.loc[idx, 'column'], dframe.loc[idx, 'num'], dframe.loc[idx, 'stocks']])

    # data = list(dframe.data.values)
    # data = [[x] for x in data]
    data = list2str(data, delimiter="")
    # 再还原出来concepts
    concepts = dframe.iloc[-1, -1].split("_")
    concepts = list2str(concepts)
    days = dframe.iloc[-2, -1].split("_")
    days = list2str(days)
    title = dframe.iloc[-3, -1]
    with open(os.path.join(html_src, "OPTION3.html"), 'rb') as fHandler:
        text = fHandler.read()
    text = text.replace("DAYS", str(days)).replace("CONCEPTS", str(concepts)).replace("DATA", str(data)).replace("TITLE", "'%s'"%title).replace(".0,", ",")
    return text


# dframe 格式为： index row，date，open, close, high, low, volume, code, rate, name(utf-8)编码
# date格式为"%Y-%m-%d"
# 据此生成K线图的html
def curve_option4(dframe, html_src=os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", "")):
    data = []
    for idx in dframe.index.values:
        data.append([dframe.loc[idx, 'date'], dframe.loc[idx, 'open'],
                     dframe.loc[idx, 'close'], dframe.loc[idx, 'low'],
                     dframe.loc[idx, 'high'], dframe.loc[idx, 'rate'],
                     dframe.loc[idx, 'hrate'], dframe.loc[idx, 'lrate'],
                      dframe.loc[idx, 'volume']])

    data = list2str(data, delimiter="")
    with open(os.path.join(html_src, "OPTION4.html"), 'rb') as fHandler:
        text = fHandler.read()
        try:
            text = text.replace("STOCK_DATA", str(data)).replace("STOCK_NAME", dframe.loc[0, 'name'])
        except:
            try:
                text = text.replace("STOCK_DATA", str(data)).replace("STOCK_NAME", dframe.loc[0, 'name'].decode("gbk"))
            except:
                try:
                    text = text.replace("STOCK_DATA", str(data)).replace("STOCK_NAME", dframe.loc[0, 'name'].encode("gbk"))
                except:
                    text = text.replace("STOCK_DATA", str(data)).replace("STOCK_NAME", dframe.loc[0, 'name'].decode("utf-8"))
    return text


# dframe 格式为： index row，date，ratio, count, desc, data_flag(将一个dframe拆分成2个dframe，根据标号分别为1, 2)
# 据此生成散点图
#
def curve_option5(dframe, data_name_list=['A', 'B'], title='concept_position', x_name='date', y_name=u'新能源', size1='6', size2='6', html_src=os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", "")):
    data1 = []
    dframe1 = dframe[dframe.data_flag == 1]

    for idx in dframe1.index.values:
        if 'desc' in dframe1.columns:
            data1.append([dframe1.loc[idx, 'date'], dframe1.loc[idx, 'ratio'],
                     dframe1.loc[idx, 'count'], dframe1.loc[idx, 'desc']])
        else:
            data1.append([dframe1.loc[idx, 'date'], dframe1.loc[idx, 'ratio'],
                         dframe1.loc[idx, 'count']])
    data2 = []
    dframe2 = dframe[dframe.data_flag == 2]
    for idx in dframe2.index.values:
        if 'desc' in dframe1.columns:
            data2.append([dframe2.loc[idx, 'date'], dframe2.loc[idx, 'ratio'],
                     dframe2.loc[idx, 'count'], dframe2.loc[idx, 'desc']])
        else:
            data2.append([dframe2.loc[idx, 'date'], dframe2.loc[idx, 'ratio'],
                         dframe2.loc[idx, 'count']])

    data1 = [str(x) for x in data1]
    data2 = [str(x) for x in data2]
    data1 = list2str(data1, delimiter="")
    data2 = list2str(data2, delimiter="")

    with open(os.path.join(html_src, "OPTION5.html"), 'rb') as fHandler:
        text = fHandler.read()
        text = text.replace("DATA1_NAME", data_name_list[0]).replace("DATA2_NAME", data_name_list[1]).replace("TITLE_TEXT", title)
        text = text.replace('DATA1', data1).replace("DATA2", data2).replace("SIZE1", size1).replace("SIZE2", size2)
        text = text.replace("X_NAME", x_name).replace("CONCEPT_y_NAME", y_name)
        text = text.replace('"[', '[').replace(']"', ']')
    return text


def curve_option4and5(dframe_list, data_name_list=['A', 'B'], title='concept_position', x_name='date', y_name='ratio%', size1='2', size2='8', html_src = os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", "")):
    [dframe4, dframe5] = dframe_list
    # 先处理dframe4的
    data4 = []
    for idx in dframe4.index.values:
        data4.append([dframe4.loc[idx, 'TRADE_DATE'], dframe4.loc[idx, 'OPEN_PRICE'],
                     dframe4.loc[idx, 'CLOSE_PRICE'], dframe4.loc[idx, 'LOWEST_PRICE'],
                     dframe4.loc[idx, 'HIGHEST_PRICE'], dframe4.loc[idx, 'TURNOVER_VOL'],
                      dframe4.loc[idx, 'rate'], dframe4.loc[idx, 'hrate'],
                      dframe4.loc[idx, 'lrate']])

    data4 = list2str(data4, delimiter="")


    # 再处理dframe5的
    data1 = []
    dframe1 = dframe5[dframe5.data_flag == 1]

    for idx in dframe1.index.values:
        if 'desc' in dframe1.columns:
            data1.append([dframe1.loc[idx, 'date'], dframe1.loc[idx, 'ratio'],
                     dframe1.loc[idx, 'count'], dframe1.loc[idx, 'desc']])
        else:
            data1.append([dframe1.loc[idx, 'date'], dframe1.loc[idx, 'ratio'],
                         dframe1.loc[idx, 'count']])
    data2 = []
    dframe2 = dframe5[dframe5.data_flag == 2]
    for idx in dframe2.index.values:
        if 'desc' in dframe1.columns:
            data2.append([dframe2.loc[idx, 'date'], dframe2.loc[idx, 'ratio'],
                     dframe2.loc[idx, 'count'], dframe2.loc[idx, 'desc']])
        else:
            data2.append([dframe2.loc[idx, 'date'], dframe2.loc[idx, 'ratio'],
                         dframe2.loc[idx, 'count']])

    data1 = [str(x) for x in data1]
    data2 = [str(x) for x in data2]
    data1 = list2str(data1, delimiter="")
    data2 = list2str(data2, delimiter="")


    with open(os.path.join(html_src, "OPTION4and5.html"), 'rb') as fHandler:
        # 替换掉OPTION4相关的
        text = fHandler.read()
        text = text.replace("STOCK_DATA", str(data4)).replace("STOCK_NAME", dframe4.iloc[0, :]['TICKER_SYMBOL'])
        # 替换掉OPTION5相关的
        text = text.replace("DATA1_NAME", data_name_list[0]).replace("DATA2_NAME", data_name_list[1].encode("utf-8")).replace("STOCK_ID", title)
        text = text.replace('DATA1', data1).replace("DATA2", data2).replace("SIZE1", size1).replace("SIZE2", size2)
        text = text.replace("X_NAME", x_name).replace("CONCEPT_y_NAME", data_name_list[1])
        text = text.replace('"[', '[').replace(']"', ']')
    return text

# LEGEND_REPLACE = ['legendA','legendB']
# dframe 列必须为： barTime(index), stockid1, Num, Details, oNum, oDetails
# num为此刻的涨停数, details为对应的涨停股票s
# 根据dframe的每一个stockid列，生成一个曲线，可以点击取消
def curve_option2(dframe, html_src = os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", "")):
    # 开始替换，代码待会儿再写
    dframe.reset_index(len(dframe), inplace=True)
    x1_name = dframe.columns[1]      # 第一个legend的name
    x2_name = dframe.columns[2]      # 第二个legend的name
    x3_name = dframe.columns[4]
    axis_data = list(dframe.barTime.values)     # x轴的横坐标
    axis_data = str(axis_data).replace("u","")
    x1_data = list(dframe[x1_name].values) # 指数的分时涨幅
    x1_data = [round(x, 2) if x != "'-'" else x for x in x1_data]
    filter_frame = dframe[['barTime', 'Num', 'Details']].dropna()
    filter_frame['x2_data'] = "['" + filter_frame['barTime'] + "', " + filter_frame['Num'].apply(lambda x : str(x)) + ", '" + filter_frame['Details'] + "']"
    x2_data = list(filter_frame.x2_data.values)
    x2_data = [x.encode('utf-8') for x in x2_data]
    x2_data = list2str(x2_data).replace('"','').replace(".0,", ",").replace("0, ]", "0, ' ']")

    filter_frame = dframe[['barTime', 'oNum', 'oDetails']].dropna()
    filter_frame['x3_data'] = "['" + filter_frame['barTime'] + "', " + filter_frame['oNum'].apply(lambda x : str(x)) + ", '" + filter_frame['oDetails'] + "']"
    x3_data = list(filter_frame.x3_data.values)
    x3_data = [x.encode('utf-8') for x in x3_data]
    x3_data = list2str(x3_data).replace('"','').replace(".0,", ",").replace("0, ]", "0, ' ']")
    with open(os.path.join(html_src, "OPTION2.html"), 'rb') as fHandler:
        text = fHandler.read()
    if x1_name == u'000001':
        x1_name = '上证指数'
    text = text.replace("X1_NAME", "'%s'"%x1_name).replace("X2_NAME", "'%s'"%str(x2_name)).replace("X3_NAME", "'%s'"%str(x3_name)).replace("AXIS_DATA", axis_data)
    text = text.replace("X1_DATA", str(x1_data)).replace("X2_DATA", str(x2_data)).replace("X3_DATA", str(x3_data))
    return text


# dframe 格式为： any_name(可修改，utf-8编码，共有轴), data_name1, data_name2, data_name3, ...， dframe值为对应的数字或者字符串
# 生成横向条形图，条个数为data_name的个数
def curve_option6(dframe, title='NO_TITLE', html_src=os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", "")):
    columns = dframe.columns
    dframe.rename(columns={columns[0]:'COMMON_NAME'}, inplace=True)
    common_data = list2str(dframe['COMMON_NAME'].values)
    series_data_list = []
    legend_name_list = []
    for col_name in dframe.columns:
        if col_name == 'COMMON_NAME':
            continue
        legend_name_list.append(col_name)
        tmp_dict = {
            'name':col_name,
            'type':'bar',
            'data':list2str([str(x) for x in list(dframe[col_name].values)])
        }
        series_data_list.append(tmp_dict)

    str_series_data = list2str(series_data_list, delimiter='x').replace(r'\"', '').replace('"[', '[').replace(']"', ']')
    str_legend_name = list2str(legend_name_list)

    with open(os.path.join(html_src, "OPTION6.html"), 'rb') as fHandler:
        text = fHandler.read()
        try:
            text = text.replace("TITLE", title).replace("LEGEND_NAME", str_legend_name)
            text = text.replace("COMMON_Y_DATA", str(common_data)).replace("SERIES_DATA", str_series_data)
        except:
            print "Error"
    return text

# K线和横向的条状图
# dframe4： index date, open, close, low, high, rate, hrate, lrate, volume
# dframe6: any_name(可修改，utf-8编码，共有轴), data_name1, data_name2, data_name3, ...， dframe值为对应的数字或者字符串
def curve_option4and6(dframe_list, title_list=['A', 'B'], html_src=os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", "")):
    [dframe4, dframe6] = dframe_list
    [title4, title6] = title_list
    # 先处理dframe4的
    data4 = []
    for idx in dframe4.index.values:
        data4.append([dframe4.loc[idx, 'date'], dframe4.loc[idx, 'open'],
                     dframe4.loc[idx, 'close'], dframe4.loc[idx, 'low'],
                     dframe4.loc[idx, 'high'], dframe4.loc[idx, 'rate'],
                     dframe4.loc[idx, 'hrate'], dframe4.loc[idx, 'lrate'],
                      dframe4.loc[idx, 'volume']])

    data4 = list2str(data4, delimiter="")


    # 再处理dframe6的
    columns = dframe6.columns
    dframe6.rename(columns={columns[0]:'COMMON_NAME'}, inplace=True)
    common_data = list2str(dframe6['COMMON_NAME'].values)
    series_data_list = []
    legend_name_list = []
    for col_name in dframe6.columns:
        if col_name == 'COMMON_NAME':
            continue
        legend_name_list.append(col_name)
        tmp_dict = {
            'name':col_name,
            'type':'bar',
            'data':list2str([str(x) for x in [round(x, 2) for x in dframe6[col_name].values]]),
            'xAxisIndex':2,
            'yAxisIndex':2,
            'label':{"normal":{"show":"true","position": 'inside'}}
        }
        series_data_list.append(tmp_dict)

    str_series_data = list2str(series_data_list, delimiter='x').replace(r'\"', '').replace('"[', '[').replace(']"', ']')
    str_series_data = str_series_data.replace("[{", "{").replace("}]", "}")
    str_legend_name = list2str(legend_name_list)



    with open(os.path.join(html_src, "OPTION4and6.html"), 'rb') as fHandler:
        # 替换掉OPTION4相关的
        text = fHandler.read()
        text = text.replace("STOCK_DATA", str(data4)).replace("STOCK_NAME", str(dframe4.iloc[0, :]['name']))
        # 替换掉OPTION6相关的
        text = text.replace("BAR_NAME", str(title6)).replace("LEGEND_NAME", str(str_legend_name))
        text = text.replace("COMMON_Y_DATA", common_data.encode("utf-8")).replace("SERIES_DATA", str(str_series_data))
    return text

# dframe 格式为： any_name(可修改，utf-8编码), data_name1, data_name2, data_name3, ...
# date格式为"%Y-%m-%d"
# 据此生成正常情况下的柱状图
def curve_option7(dframe, title='NO_TITLE', html_src=os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", "")):
    columns = dframe.columns
    dframe.rename(columns={columns[0]:'COMMON_NAME'}, inplace=True)
    common_data = list2str(dframe['COMMON_NAME'].values)
    series_data_list = []
    legend_name_list = []
    for col_name in dframe.columns:
        if col_name == 'COMMON_NAME':
            continue
        legend_name_list.append(col_name)
        tmp_dict = {
            'name':col_name,
            'type':'bar',
            'markLine' : {
                'data' : [
                    {'type' : 'average', 'name': '平均值'}
                ]
            },
            'data':list2str([str(x) for x in list(dframe[col_name].values)])
        }
        series_data_list.append(tmp_dict)

    str_series_data = list2str(series_data_list, delimiter='x').replace(r'\"', '').replace('"[', '[').replace(']"', ']')
    str_legend_name = list2str(legend_name_list)

    with open(os.path.join(html_src, "OPTION7.html"), 'rb') as fHandler:
        text = fHandler.read()
        try:
            text = text.replace("TITLE", title).replace("LEGEND_NAME", str_legend_name)
            text = text.replace("COMMON_X_DATA", common_data.encode("utf-8")).replace("SERIES_DATA", str_series_data.replace(",p,", ",'p',").replace(",p,", ",'p',").replace(",p,", ",'p',").replace(",p]", ",'p']").replace("[p,", "['p',"))
        except:
            print "Error"
    return text







# 将一个np.array的closePrice变成%
def normalize_frame(np_arr, last_price):
    open_arr = np.array([last_price] * len(np_arr))
    tmp_array = 100*(np_arr - open_arr)/open_arr
    tmp_array = tmp_array.round(2)
    return tmp_array

# 从日期/daydayup.csv 中 根据group进行归类，也需要将anotation里面的股票加进来
# 得到一个dict：{"属性名":[股票id], "属性名2":[股票id]}
def get_concept_list(day, csvfile = ""):
    tdict = {}
    day = format_date(day, "%Y%m%d")
    if csvfile == "":
        csvfile = os.path.join(u"D:/Money/modeResee/复盘/%s"%day, "daydayup.csv")
    dframe = pd.read_csv(csvfile, encoding='gbk')
    dframe.dropna(subset=['group'], inplace=True)
    for idx in dframe.index.values:
        attr = dframe.loc[idx, 'group']
        stcid = [int(float(dframe.loc[idx, 'stock']))]
        if u'anotation' in dframe.columns:
            anotations = dframe.loc[idx, 'anotation']
        else:
            anotations = 'AAA'
        if (anotations == anotations) and (anotations != 'AAA'):
            anotations = anotations.replace(u'，', u',')
            anotations = anotations.split(u",")
            anotation_stcid = [QueryStockMap(name = x.replace(u' ', u''))[1].encode("utf-8") for x in anotations]
            stcid.extend(anotation_stcid)
        stcid = ['0'*(6-len(str(x)))+str(x) for x in stcid if len(str(x)) > 0]
        if attr not in tdict:
            tdict[attr] = stcid
        else:
            tmp_dict = tdict[attr]
            tmp_dict.extend(stcid)
            tdict[attr] = tmp_dict
    return tdict

# return: {"银行":{"龙头":[], "跟风":[]}
def get_concept_dragon_list(gdate):
    global mongodb
    # 获取最近的一个交易日
    find_date = format_date(get_lastN_date(gdate, 0), "%Y%m%d")
    # 获取上一个交易日
    find_date1 = format_date(get_lastN_date(gdate, 1), "%Y%m%d")
    # 从mongo中找对应日期的龙头、跟风记录（即前一天的龙头信息）
    results = mongodb.concepts.dragon_pool.find({"date":{"$lte":find_date, "$gte":find_date1}}).sort("date",pymongo.DESCENDING)
    if results.count() == 0:
        return {}
        # raise Exception("No record for date:%s in concepts.dragon_pool" % find_date)
    else:
        return results[0]


# dframes 为 [dframe]， 为各个option的输入数据
# html_types 为 [html_type]， 为各个option对于的网页源码类型
# html_name就是概念名字
# plot_stock_list = ['600036', '300088']
def get_html_curve(dframes, html_name, html_types = [1], title_list = [], data_name_list=['A','B'],
                   width=1600, height=400, save_dir = "./", chart_connect=0,
                   html_src=os.path.join(u"D:/Money/lilton_code/Market_Mode/rocketup/src", ""), plot_stock_list=[],
                   generate_date=datetime.datetime.today().strftime("%Y%m%d")):


    # 如果有plot_stock_list，则得到对应的概念
    if len(plot_stock_list) == 0:
        plot_stock_list = [0]*len(html_types)

    # 读取html框架
    with open(os.path.join(html_src, "frame_work.html"), 'rb') as fHandler:
        frameWork = fHandler.read()
        # 替换掉框架中的日期和概念字段，目前用在tree-summary下面
        frameWork = frameWork.replace(u'ConceptVar', u'%s' %html_name).replace(u'DateVar', u'%s' % generate_date)
        frameWork = frameWork.encode("utf-8")
    text_list = []
    # 分别得到各个option类型的text
    for i in range(0, len(html_types)):
        html_type = html_types[i]
        dframe = dframes[i]
        title = title_list[i]
        option = ""
        if html_type == 1:      # 类型1， 多个股票的分时图对比
            option = curve_option1(dframe, title=title)
        elif html_type == 2:    # 类型2， 上证分时图（line）同涨停的分时个数（scatter）
            option = curve_option2(dframe)
        elif html_type == 3:    # 类型3， 直角坐标系下的热力图，显示每天对应概念的热度
            option = curve_option3(dframe)
        elif html_type == 4:    # 类型4， K线图
            option = curve_option4(dframe)
        elif html_type == 5:    # 类型5， 散点图
            option = curve_option5(dframe, data_name_list=data_name_list, title=title)
        elif html_type == '4and5':
            option = curve_option4and5(dframe, data_name_list=data_name_list, title=title)
        elif html_type == 6:    # 类型4， K线图
            option = curve_option6(dframe, title)
        elif html_type == '4and6':
            option = curve_option4and6(dframe, title)
        elif html_type == 7:
            option = curve_option7(dframe, title)

        if len(option) > 0:
            text_list.append(option)

    # 合并，修改成多图连动,回来弄
    option, count = set_frameWork_option(text_list)

    front, inner = set_frameWork_charts(count, generate_date, width=width, height=height, chart_connect=chart_connect,
                                        plot_stock_list=plot_stock_list, html_name=html_name)

    frameWork = frameWork.replace("BODY_HEADER", front)
    frameWork = frameWork.replace("OPTIONS", option)
    frameWork = frameWork.replace("MYCHARTS", inner)

    # 输出
    if not os.path.exists(os.path.join(save_dir, "conf/")):
        os.mkdir(os.path.join(os.path.join(save_dir, "conf/")))
    curdir = os.path.join("D:/Money/lilton_code/Market_Mode/rocketup", "")
    if not os.path.exists(os.path.join(save_dir, "conf/jquery-3.1.0.min.js")):
        shutil.copy(os.path.join(curdir, "./conf/jquery-3.1.0.min.js"), os.path.join(save_dir, "conf/jquery-3.1.0.min.js"))
    if not os.path.exists(os.path.join(save_dir, "conf/echarts.min.js")):
        shutil.copy(os.path.join(curdir, "./conf/echarts.min.js"), os.path.join(save_dir, "conf/echarts.min.js"))
    fHandler = open(os.path.join(save_dir,"%s.html"%html_name), 'wb')
    fHandler.write(frameWork)
    fHandler.close()


# 同一个html下，可以查看多个股票多个日期的分时图走势
def get_html_curve1_multi_date(stock_list, date_list, save_dir, html_name):
    dframe_list = []
    title_list = []
    html_types = []
    for date in date_list:
        dframe = get_dataframe_option1(stock_list, date)
        dframe_list.append(dframe)
        title_list.append(date)
        html_types.append(1)

    get_html_curve(dframe_list, html_name, html_types=html_types, title_list=title_list, save_dir=save_dir)


# 判断一个股票在某天，是否最高点涨停过
# 条件1： 滤除开盘就涨停的时间段，从打开涨停之后算
# fenbi_frame: datadate, datatime, ticker, exchangecd, lastprice, volume, side
# 20161101 09:25:03 1 XSHE 9.140 89400 B
def get_hit_status(stockid, day):
    fenbi_frame = get_fenbi_frame(stockid, day) # 得到了分钟线数据
    last_day = get_last_date(day)
    last_close = get_mysqlData([stockid], [last_day]).loc[0, 'CLOSE_PRICE']   # 昨日收盘价
    zt_price = round(last_close*1.1, 2)
    fenbi_frame = fenbi_frame[fenbi_frame.datatime >= "09:30:00"]   # 不考虑集合竞价的情况
    fenbi_frame = fenbi_frame[fenbi_frame.volume != 0]  # 成交量为0，滤除
    fenbi_frame.to_csv("tmp_trace.csv", encoding='gbk')
    for idx in fenbi_frame.index.values:
        if float(fenbi_frame.loc[idx, 'lastprice']) != zt_price:
            break
    filtered_frame = fenbi_frame.loc[idx:,:]
    hit_frame = filtered_frame[filtered_frame.lastprice == zt_price]
    if len(hit_frame) > 0:
        return True
    else:
        return False


# 输入格式为 u'09:25:11' , 输出为 u'09:30'
def convert_second_time(x_time):
    [hour, minu, secd] = x_time.split(":")
    if hour == u'09' and minu < u'30':
        minu = u'30'
    return u"%s:%s" % (hour, minu)


# 将list转换为str
# lista = ['30', '中国'] , 变成str也应该是 ['30', '中国'], 不能用str，因为str会变成unicode，\\
# 默认用双引号分开
def list2str(lista, delimiter='"'):
    if delimiter == '"':
        return '["'+'","'.join(lista) + '"]'
    elif delimiter == "'":
        return "['"+"','".join(lista) + "']"
    else:
        return json.dumps(lista, ensure_ascii=False)


# 在分钟级数据中，将指数和个股区分开
def get_min_stock_id_type(stockid):
    if "ZS" in stockid:
        stockid = stockid.replace("ZS", "")
        id_type = 0
    else:
        stockid = stockid
        id_type = 1
    return stockid, id_type


# 分钟级，各个stock的涨幅
def get_minly_ratio_frame(stockids, gdate):
    dframe = DataFrame()
    stockids = ['0'*(6-len(str(x))) + str(x) for x in stockids]
    tmp_frame_list = []
    for stock in stockids:
        yesterday = get_lastN_date(gdate, 1)
        yeframe = get_mysqlData([stock],[yesterday])
        stock, id_type = get_min_stock_id_type(stock)
        tmp_frame = get_minly_frame(stock, gdate, id_type=id_type)
        tmp_frame = tmp_frame[['bartime', 'closeprice']]

        if len(yeframe) > 0:
            pre_close = yeframe.loc[0,'CLOSE_PRICE']
        else:
            pre_close = 10000
        tmp_frame['closeprice'] = normalize_frame(tmp_frame['closeprice'], pre_close)
        tmp_frame.columns = ['barTime', stock]
        tmp_frame.set_index('barTime', inplace=True)
        tmp_frame_list.append(tmp_frame)
    dframe = pd.concat(tmp_frame_list, axis=1)
    dframe.reset_index(range(len(dframe)), inplace=True)
    return dframe


# 看一个股票涨停时间
# 返回 closetime, nonstabletime, 都是list
# closetime 为最后一次封死后就不再开板的时间，为长度为1的list，可能为空
# nonstabletime为临时封板的时间，长度不固定，可能为空
# 最后会做一次统一，将秒级数据变成分钟级
def zt_time_details(stockid, day):
    # a0 = time.time()
    dframe = get_fenbi_frame(stockid, day)        # 用分笔细节数据来看
    # a1 = time.time()
    # print "%s to get fenbidata"%(a1 - a0)
    last_day = get_last_date(day)
    # a2 = time.time()
    last_close = get_mysqlData([stockid], [last_day])
    if len(last_close) == 0:
        print "[warnings] no last close for %s, last_day:%s, will skip" %(stockid, last_day)
        return [], []
    last_close = last_close.loc[0, 'CLOSE_PRICE']   # 昨日收盘价
    # a3 = time.time()
    # print "%s to get last close price" % (a3 - a2)
    zt_price = round(last_close*1.1, 2)

    dframe['minus_zt'] = dframe['lastprice'] - zt_price
    dframe['shifted_price'] = dframe['lastprice'].shift(1)
    dframe.fillna(value=0, inplace=True)
    tag = 0
    if dframe.lastprice.values[-1] == zt_price:
        tag = 1     # 当天收涨停
    dframe = dframe[(dframe.lastprice == zt_price) & (dframe.lastprice > dframe.shifted_price)]
    if len(dframe) == 0:
        return [], []
    if tag == 1:
        closetime = [dframe.datatime.values[-1]]
        nonstabletime = list(dframe.datatime.values[:-1])
    else:
        closetime = []
        nonstabletime = list(dframe.datatime.values)
    # close_flag = -1 # -1代表初始态, 1代表所有的涨停都为临时性涨停, 0代表下一个涨停就是最终涨停
    # revindexs = list(dframe.index.values)
    # revindexs.reverse()
    # last_price = 0
    # closetime = []
    # nonstabletime = []
    # # a4 = time.time()
    # # print "%s for preparation" % (a4 - a3)
    # for idx in revindexs:
    #     if close_flag == -1:    # 初始态
    #         if float(dframe.loc[idx, 'lastprice']) == zt_price:
    #             close_flag = 0
    #         else:
    #             close_flag = 1
    #     else:
    #         curr_price = float(dframe.loc[idx, 'lastprice'])
    #         if last_price == zt_price and curr_price < zt_price:    # 下一个时刻涨停，此时刻还没涨停
    #             if close_flag == 0:
    #                 closetime.append(dframe.loc[idx+1, 'datatime'])
    #                 close_flag = 1
    #             else:
    #                 nonstabletime.append(dframe.loc[idx+1, 'datatime'])
    #
    #     last_price = float(dframe.loc[idx, 'lastprice'])
    # a5 = time.time()
    # print "%s to for loop" %(a5 - a4)
    # 将秒级别数据变成分钟级
    closetime = [convert_second_time(x) for x in closetime]
    nonstabletime = [convert_second_time(x) for x in nonstabletime]
    nonstabletime = [x for x in nonstabletime if x not in closetime]
    nonstabletime = list(set(nonstabletime))
    # a6 = time.time()
    # print "%s to convert" % (a6 - a5)
    return closetime, nonstabletime


def look_up_dir(dir_path):
    if not os.path.exists(os.path.join(dir_path,"")):
        os.makedirs(dir_path)


# 给出一个stockid，日期
# 找到对应的concept，以及相关股票id
# 先从前10日的csv中找，如果没找到，则从L1中找，如果没找到，再到L2中找，再没找到，就为空
# 从前10日的csv找到概念之后，先去L1找关联股票，找不到时候再去L2
# 返回['concept', [关联股票ids]]
def find_concept(stockid, date):
    concept = ""
    ids = []
    stockid = str(int(float(stockid)))
    stockid = '0'*(6-len(stockid)) + stockid
    csv_concept = get_csv_concept(stockid, date)
    if csv_concept == '':       # 在前10日的daydayup中找不到
        L1_concept = get_cacheinfos_by_id(stockid, cache=1)
        if L1_concept[0] == "":     # 在L1中也找不到
            L2_concept = get_cacheinfos_by_id(stockid, cache=2)
            concept = L2_concept[0]
            ids = L2_concept[1]
        else:
            concept = L1_concept[0]
            ids = L1_concept[1]
    else:
        concept = csv_concept
        ids = find_ids(concept)
    return [concept, ids]


# 找到对应的股票
def find_ids(concept):
    ids = get_id_from_concept(concept, cache=1)
    if len(ids) == 0:
        ids = get_id_from_concept(concept, cache=2)
    return ids


# 根据日期，从csv中找到股票的concept，默认是从昨天到5天之前
# 返回是'concept'，如果找不到，则是''
def get_csv_concept(stockid, date, period=10):
    global backsee_csv
    concept = ''
    for i in range(1,period+1):
        search_date = get_lastN_date(date, i)   # 搜索日期
        search_date = format_date(search_date, "%Y%m%d")
        try:
            dframe = pd.read_csv(os.path.join(backsee_csv, "%s/daydayup.csv" % search_date), encoding='gbk')
            dframe.dropna(subset=['stock'], inplace=True)
            dframe['stockid'] = dframe['stock'].apply(lambda x: int(float(x)))      # 都转换成整数型
            dframe.dropna(subset=['group'], inplace=True)   # 将不含group的行删除
            tframe = dframe[dframe.stock == int(float(stockid))]
            columns = list(tframe.columns)
            n_group = columns.index(u'group')
            if len(tframe) > 0:
                concept = tframe.iloc[0, n_group]
                break
        except Exception, err:
            print "Search Error for daydayup on %s, err:%s, will skip this day" % (search_date, err)
    return concept


# 从数据库cache中找到股票对于的concept以及关联stocks
# 返回['概念名称', '相关概念的所有股票列表']
# 如果没找到，则返回['', []]
def get_cacheinfos_by_id(stockid, cache=1):
    global mongodb
    if cache == 1:
        result = mongodb.concepts.L1.find_one({"stockid": stockid})
    else:
        result = mongodb.concepts.L2.find_one({"stockid": stockid})

    if result is None:  # 说明在cache中，没有该股票
        return ["", []]
    else:
        return result['concept'], get_id_from_concept(result['concept'], cache)


# 从数据库cache中，根据concept得到所有的股票ID，返回list，如果L1中不存在该概念，则返回[]
def get_id_from_concept(concept, cache=1):
    global mongodb
    ids = []

    if cache == 1:
        results = mongodb.concepts.L1.find({"concept": concept})
    else:
        results = mongodb.concepts.L2.find({"concept": concept})

    if results.count() == 0:
        return ids
    else:
        for result in results:
            ids.append(result['stockid'])
        return ids


# 从csv中得到具体信息，返回为 redict
# redict = { "ZT": {"concept1": ["stockid1", "stockid2"]},
#             "HD": {"concept1": ["stockid1"]},
#             "DT": ...,
#             "hole": ...,
#             "meat": ...,
#            }
def get_csv_details(date, file_dir = u'D:/Money/modeResee/复盘', file_name = 'daydayup.csv'):
    date = format_date(date, "%Y%m%d")
    tdict = {"ZT":{}, "HD":{}, "DT":{}, "meat":{}, "hole":{}}
    dframe = pd.read_csv(os.path.join(file_dir, "%s/%s" % (date, file_name)), encoding='gbk')
    dframe['group'].fillna(value=u'未明', inplace=True)
    # 规整化为000014
    dframe['stock'] = dframe['stock'].apply(lambda x: '0'*(6-len(str(int(float(str(x)))))) + str(int(float(str(x)))))
    for idx in dframe.index.values:
        stockid = dframe.loc[idx, 'stock']
        type = dframe.loc[idx, 'type']
        group = dframe.loc[idx, 'group']
        if group == u'未明':
            group = find_concept(stockid, date)[0]
            if group == '':
                group = u'未明'
        if group not in tdict[type].keys():
            tdict[type][group] = [stockid]
        else:
            tdict[type][group].append(stockid)
    return tdict


# 根据历史上某日的daydayup.csv，生成基于某日行情的html
# date代表历史上记录csv的某日
# tdate代表行情日
def generate_html(date, tdate=datetime.datetime.today().strftime("%Y%m%d"), file_dir=u'D:/Money/modeResee/复盘', file_name='daydayup.csv'):
    # 读取csv内容，生成tdict
    tdict = get_csv_details(date, file_dir, file_name)
    # 大盘数据
    dataframe = get_minly_ratio_frame(["ZS000001"], tdate)
    dataframe.fillna(value = "'-'", inplace=True)
    dataframe.set_index('barTime', inplace=True)
    dframe_list = []
    title_list = []
    type_list = []
    for types in tdict.keys():
        for concept in tdict[types].keys():
            # print concept
            stock_list = tdict[types][concept]
            # 增加上证指数
            stock_list.append("ZS000001")
            tmp_dframe = get_dataframe_option1(stock_list, tdate)
            dframe_list.append(tmp_dframe)
            add_concept = u'%s_%s' %(types,concept)
            add_concept = add_concept.encode('utf-8')
            title_list.append(add_concept)
            type_list.append(1)
    save_day = format_date(tdate, "%Y%m%d")
    get_html_curve(dframe_list, u"learn_from_history", html_types = type_list, title_list=title_list, save_dir=os.path.join(u"D:/Money/modeResee/复盘/%s"%save_day,""))


# 判断股票、概念组合是否在cache中
def exist_in_cache(stockid, concept, cache = 1):
    global mongodb
    if concept == "":
        return 0
    else:
        stockid = '0'*(6-len(str(int(float(stockid))))) + str(int(float(stockid)))
        if cache == 1:
            result = mongodb.concepts.L1.find_one({"stockid": stockid, "concept":concept})
        else:
            result = mongodb.concepts.L2.find_one({"stockid": stockid, "concept":concept})
        if result is None:
            return 0
        else:
            return 1


def regulize_stockid(id):
    if id != id:
        return ""
    elif len(str(id).replace(u' ', u'')) == 0:
        return ""
    else:
        return '0'*(6-len(str(int(float(id))))) + str(int(float(id)))

def get_stockids_from_concept(concept, cache=1):
    global mongodb
    if cache == 1:
        results = mongodb.concepts.L1.find({"concept":concept})
    else:
        results = mongodb.concepts.L2.find({"concept":concept})
    stockids = [result['stockid'] for result in results]
    stocknames = [result['name'] for result in results]
    return stockids, stocknames


#从mongo中读取focused concept
def get_focused_concepts():
    global mongodb
    concepts = []
    results = mongodb.concepts.focused_concepts.find()
    for result in results:
        concepts.append(result['concept'])
    return concepts


# 从东方财富网得到股票代码和名称
#index_col CODE NAME
def get_stoclist_dc():
    url = "http://quote.eastmoney.com/stocklist.html"
    stoc_df = pd.DataFrame()
    rs_count = 2
    while rs_count >0:
        try:
            r = requests.get(url)
            if r.status_code != 200:
                print "Error: get stock list from DC failed"
                break
            root = etree.HTML(r.content)
            stock_infos = root.xpath(u'//div[@id="quotesearch"]/ul/li/a/text()')
            dict_list = []
            for stock_info in stock_infos:
                stock_info_list = stock_info.split("(")
                stock_name = stock_info_list[0]
                stock_code = str(stock_info_list[1].replace(u")", ""))
                if (len(stock_code)!= 6) or (stock_code[:2] not in ["00", "60", "30"]):
                    continue
                dict_list.append({"name":stock_name, "code":stock_code})
            stoc_df = pd.read_json(json.dumps(dict_list))
            stoc_df.reset_index(inplace=True)
            del stoc_df['index']
            stoc_df['code'] = stoc_df['code'].astype(np.str)
            if len(stoc_df) > 1000:
                break
            rs_count -= 1
        except:
            rs_count -= 1
    return stoc_df

# 从tushare、东方财富网拿到股票list
def get_stock_list_from_many_site():
    mdir = 'D:\Money\lilton_code'
    # 从tushare拿到股票list
    zs = pd.DataFrame()
    ts_count = 2
    print "Get stock list from TUSHARE"
    try:
        # raise ValueError("EEE")
        while ts_count > 0:
            try:
                zs = ts.get_stock_basics()
                if len(zs) > 1000:
                    zs.reset_index(inplace=True)
                    zs = zs[['code', 'name']]
                    break
                print "Failed to get stock basics, len:%s" %len(zs)
                ts_count -= 1
                time.sleep(5)
            except:
                print "Failed to get stock basics"
                ts_count -= 1
                time.sleep(5)
        # print ""
        if ts_count <= 0:
            raise Exception("Connect Error from Tushare")
    except:
        print "Failed to get stock list from TUSHARE"
        zs = pd.read_csv(os.path.join(mdir, "stock_list.csv"), encoding='gbk', index_col=0)
        # print zs.columns
        zs.columns = [u'code', u'name']

    stock_list=list(zs.code.values)
    # print "Get stock list from DFCF"
    # # 从东方财富网拿到股票list
    # stocklist_dc = get_stoclist_dc()

    print "Get latest stock from MONGO"
    # 再加上最近一周更新的个股
    global mongodb
    today = datetime.datetime.today().strftime("%Y%m%d")
    five_days_before = datetime.datetime.today() - datetime.timedelta(days=30)
    five_days_before = five_days_before.strftime("%Y%m%d")
    results = mongodb.stock.ZDT_by_date.find({"date":{"$gt":five_days_before, "$lt":today}})
    for result in results:
        if "Add_newStocks" in result.keys():
            stock_list.extend(result['Add_newStocks'].keys())
    stock_list = list(set(stock_list))

    #
    #
    # if len(zs) < 1000:
    #     zs = stocklist_dc
    # else:
    #     zs = zs.merge(stocklist_dc, left_on=['code', 'name'], right_on=['code', 'name'], how='outer')

    zs.to_csv(os.path.join(mdir,'stock_list.csv'), encoding='gbk')

    return stock_list


# 抽取股金神话中的复盘数据
def extract_gjsh_records(contents, tdate):
    contents = etree.HTML(contents)
    lines = contents.xpath('//div[@class="detail"]/p/text()')
    if len(lines) == 0:
        lines = contents.xpath('//div[@class="detail"]/text()')
    match_str = r'\d{6}'
    extract_infos = {"source":"GJSH", "date":tdate}
    for eline in lines:
        # print eline
        try:
            if re.search(match_str, eline):
                # print "hit"
                eline = eline.replace("\t", " ").replace(u"\xa0", u' ')
                line_infos = eline.split(" ")
                line_infos = [x for x in line_infos if len(x)>0]
                stockid = line_infos[0]
                stockname = line_infos[1]
                for idx in range(2, len(line_infos)):
                    if u':' in line_infos[idx]:
                        # print 'hit2'
                        zt_time = line_infos[idx]
                        zt_reason = "_".join(line_infos[idx+1:])
                        extract_infos[stockid] = {"name":stockname, "reason":zt_reason, "zttime":zt_time, "type":"ZT"}
                        break
        except:
            pass
    print "Get ZT INFO from GJSH: %s in total" %(len(extract_infos) - 1)
    return extract_infos


# 抽取股金神话中的复盘数据
# 增加了大概念，即 xxxx概念：
def extract_gjsh_records_big_concept(contents, tdate):
    # 将+换成加
    contents = contents.replace(r'+', u'加')
    contents = etree.HTML(contents)
    lines = contents.xpath('//div[@class="detail"]/p/text()')
    if len(lines) == 0:
        lines = contents.xpath('//div[@class="detail"]/text()')
    match_str = r'\d{6}'
    extract_infos = {"source":"GJSH_B", "date":tdate}
    big_concept = ""
    last_line = ""
    last_valid_status = False
    first_type_concept = False
    for eline in lines:
        eline = eline.strip()
        try:
            if re.search(match_str, eline):
                eline = eline.replace("\t", " ").replace(u"\xa0", u' ')
                line_infos = eline.split(" ")
                line_infos = [x for x in line_infos if len(x)>0]
                stockid = line_infos[0]
                stockname = line_infos[1]
                for idx in range(2, len(line_infos)):
                    if u':' in line_infos[idx]:

                        # 第二种含有big_concept的类型，即该行符合要求，如果上一行不符合要求，则上一行可能是（再排除掉点评之类的）
                        # 条件一： 上一行不是300043 xxx 之类的
                        # 条件二： 上一行不为空
                        # 条件三： 不存在类型1的big concept
                        if not last_valid_status and len(last_line) > 1 and not first_type_concept and u'点评' not in last_line and u'代码' not in last_line:
                            big_concept = last_line.strip()
                        zt_time = line_infos[idx]
                        zt_reason = "_".join(line_infos[idx+1:])
                        extract_infos[stockid] = {"name":stockname, "reason":zt_reason, "zttime":zt_time, "type":"ZT", "big_concept":big_concept}
                        last_valid_status = True
                        if len(eline) > 0:
                            last_line = eline
                        break
            else:
                last_valid_status = False
                if len(eline.strip()) > 0:
                    last_line = eline
        except:
            last_valid_status = False
            if len(eline.strip()) > 0:
                last_line = eline
    print "Get ZT INFO from GJSH: %s in total" %(len(extract_infos) - 1)
    return extract_infos


# 指定访问股金神话页面，以及日期
def directly_gjsh_page(url, tdate):
    general_headers = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate, sdch",
        "Accept-Language":"zh-CN,zh;q=0.8",
        "Connection":"keep-alive",
        "Host":"www.xueqiu.com",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
        }

    general_headers1 = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection":"keep-alive",
        "Host":"xueqiu.com",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }

    main_page = "https://www.xueqiu.com"
    s = requests.Session()
    s.get(main_page, headers=general_headers)
    global mongodb
    next_url = url
    status = False
    # 开始获取信息
    t_count = 5
    while t_count > 0:
        try:
            r = s.get(next_url, headers = general_headers1)
            if r.status_code != 200:
                raise Exception("访问股金神话具体页面失败")
            # record_infos = extract_gjsh_records(r.content.decode("utf-8"), tdate)
            record_infos = extract_gjsh_records_big_concept(r.content.decode("utf-8"), tdate)
            # 更新到mongo中
            mongodb.stock.mirror_info.update({"source":"GJSH_B", "date":tdate}, {"$set":record_infos}, upsert=True, multi=False)
            status = True
            break
        except Exception, e:
            t_count -= 1
            time.sleep(3)





# 爬取股金神话的复盘信息
# 存储到FP_INFO_DAILY
# {"600036":{'name':名字, 'reason':原因, 'time':涨停时间},"":{}, xxxxxx,  "source":"GJSH"}
def resee_info_gjsh(tdate=datetime.datetime.today().strftime("%Y%m%d")):
    tdate = format_date(tdate, "%Y%m%d")
    tyear = tdate[:4]
    tmonth = str(int(tdate[4:6]))
    tday = str(int(tdate[6:]))

    general_headers = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate, sdch",
        "Accept-Language":"zh-CN,zh;q=0.8",
        "Connection":"keep-alive",
        "Host":"www.xueqiu.com",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
        }

    general_headers1 = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection":"keep-alive",
        "Host":"xueqiu.com",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }

    main_page = "https://www.xueqiu.com"
    s = requests.Session()
    s.get(main_page, headers=general_headers)


    # 查看股金神话的页面
    page1 = "https://xueqiu.com/statuses/search.json?q=%E6%B6%A8%E5%81%9C%E6%9D%BF%E5%A4%8D%E7%9B%98&page=1&uid=4172966218&sort=time"

    r = s.get(page1, headers=general_headers1)
    if r.status_code != 200:
        print "Error: 访问股金神话主页失败!"

    # content = r.content.decode("utf-8")
    content = json.loads(r.content)
    user_id = 0
    file_id = 0
    for infos in content['list']:
        text = infos['title']
        if tyear in text and tmonth in text and tday in text:
            # print text
            user_id = infos['user_id']
            file_id = infos['id']
            break
    next_url = "https://xueqiu.com/%s/%s" % (user_id, file_id)

    global mongodb
    status = False
    # 开始获取信息
    t_count = 5
    while t_count > 0:
        try:
            r = s.get(next_url, headers = general_headers1)
            if r.status_code != 200:
                raise Exception("访问股金神话具体页面失败")
            record_infos = extract_gjsh_records(r.content.decode("utf-8"), tdate)
            # 更新到mongo中
            mongodb.stock.mirror_info.update({"source":"GJSH", "date":tdate}, {"$set":record_infos}, upsert=True)
            status = True
            break
        except:
            t_count -= 1
            time.sleep(3)
    return status


# 爬取股金神话的复盘信息, 所有记录
# 存储到FP_INFO_DAILY
# {"600036":{'name':名字, 'reason':原因, 'time':涨停时间},"":{}, xxxxxx,  "source":"GJSH"}
def resee_info_gjsh_all(date_list=[]):
    general_headers = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate, sdch",
        "Accept-Language":"zh-CN,zh;q=0.8",
        "Connection":"keep-alive",
        "Host":"www.xueqiu.com",
        "Upgrade-Insecure-Requests":"1",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
        }

    general_headers1 = {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate, sdch, br",
        "Accept-Language":"zh-CN,zh;q=0.8",
        # "Cache-Control":"max-age=0",
        "Connection":"keep-alive",
        "Host":"xueqiu.com",
        "Upgrade-Insecure-Requests":"1",
        "Cookie":"remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token.sig=2n-f94Awog8FKA2ybxv4_HDcBu0; xq_r_token.sig=xrk1OoOf1b8zwqRy9nmPq68vIOI; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u.sig=Jgc8-j-5LK9Cu1KqQXwSKYg6Bdg; s=fp119z4o52; bid=c37ccb2fbbe1d07851272cff174d2d1a_j2vmf50p; webp=0; aliyungf_tc=AQAAAA3MtUgpdAQAXvKh01OyiY2Zo99Z; snbim_minify=true; xq_a_token=7306517b0e334b458892241394125c3a9733bc86; xqat=7306517b0e334b458892241394125c3a9733bc86; xq_r_token=b9ba5f2b2f6f62504431c69784442712253d4373; xq_token_expire=Fri%20Jun%2023%202017%2015%3A49%3A39%20GMT%2B0800%20(CST); xq_is_login=1; u=7362972133; __utmt=1; __utma=1.2102918026.1495184813.1496042939.1496047155.13; __utmb=1.1.10.1496047155; __utmc=1; __utmz=1.1495611549.7.2.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; Hm_lvt_1db88642e346389874251b5a1eded6e3=1495523552,1495611549,1495713657,1496042934; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1496047159",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }

    main_page = "https://www.xueqiu.com"
    s = requests.Session()
    s.get(main_page, headers=general_headers)

    total_count = 1
    for tpage in range(1, 30):
        try:
            # 查看股金神话的页面
            # page1 = "https://xueqiu.com/statuses/search.json?q=%E5%A4%8D%E7%9B%98&page=" + str(tpage) + "&uid=4172966218&sort=time&comment=0"
            # 直接扫描原始页码
            page1 = "https://xueqiu.com/v4/statuses/user_timeline.json?user_id=4172966218&type=&_=1495715494896&page=" + str(tpage)
            print page1
            r = s.get(page1, headers=general_headers1)
            if r.status_code != 200:
                print "Error: 访问股金神话主页失败!"

            global mongodb
            # content = r.content.decode("utf-8")
            content = json.loads(r.content)
            user_id = 0
            file_id = 0
            # for infos in content['list']:
            for infos in content['statuses']:
                text = infos['title'].replace(u'年', u'.').replace(u'月', u'.').replace(u'日', u'')
                if u'复'not in text and u'盘' not in text:
                    continue
                date_pattern = r'(\d{4}).(\d+).(\d+)'
                p = re.search(date_pattern, text)
                if p is not None:
                    tyear = p.group(1)
                    tmonth = p.group(2)
                    tday = p.group(3)
                    tdate = int(tyear)*10000 + int(tmonth)*100 + int(tday)
                    tdate = str(tdate)
                    if len(date_list) == 0:
                        pass
                    else:
                        if tdate not in date_list:
                            continue
                    print tdate
                    # # 如果mongo中存在了，就不要了
                    # if mongodb.stock.mirror_info.find({"date":tdate}).count() > 0:
                    #     continue
                    user_id = infos['user_id']
                    file_id = infos['id']
                    # print tdate
                    next_url = "https://xueqiu.com/%s/%s" % (user_id, file_id)
                    # 开始获取信息
                    t_count = 5
                    while t_count > 0:
                        try:
                            r = s.get(next_url, headers = general_headers1)
                            if r.status_code != 200:
                                raise Exception("访问股金神话具体页面失败")
                            record_infos = extract_gjsh_records_big_concept(r.content.decode("utf-8"), tdate)
                            # 更新到mongo中
                            mongodb.stock.mirror_info.update({"source":"GJSH_B", "date":tdate}, {"$set":record_infos}, upsert=True)
                            total_count += 1
                            break
                        except:
                            t_count -= 1
                            time.sleep(3)
        except Exception, e:
            print "Exception when handle page:%s" %tpage


# 根据concept名字获取云财经的概念
def get_ycj_stocks(concept):
    global mongodb
    stock_list = []
    results = mongodb.stock.ycj_concept.find({"concept":concept})
    if results.count() > 0:
        stock_list.extend([x['stockid'] for x in results])
    return stock_list

# 根据concept名字获取云财经中对于的概念id
def get_ycj_concept_id(concept):
    global mongodb
    concept_id = ""
    result = mongodb.stock.ycj_concept.find_one({"concept":concept})
    if result != None:
        concept_id = result["id"]
    return concept_id


# 根据concept名字获取金融界的概念
def get_jrj_stocks(concept):
    global mongodb
    stock_list = []
    results = mongodb.stock.jrj_concept.find({"concept":concept})
    if results.count() > 0:
        stock_list.extend([x['stockid'] for x in results])
    return stock_list


# 得到概念的同义词列表
# {概念1:[同义词1， 同义词2，本身词1]}, 概念2:[], ...}
def get_close_concept(filepath = u'D:/Money/modeResee/彼战/盟军列表.txt'):
    with open(filepath, 'rb') as fhandler:
        x = fhandler.read()
        x = x.decode('gbk')
        concept_dict = eval(x)
    return concept_dict


# 将概念的相似值作为key，便于不用记住到底是雄安还是雄安新区为主key
def get_value_close_concept(filepath = u'D:/Money/modeResee/彼战/盟军列表.txt'):
    value_dict = {}
    with open(filepath, 'rb') as fhandler:
        x = fhandler.read()
        x = x.decode('gbk')
        concept_dict = eval(x)
        for tkey in concept_dict.keys():
            for tvalue in concept_dict[tkey]:
                value_dict[tvalue] = tkey
    return value_dict



global close_concept_dict
close_concept_dict = get_close_concept()

global close_concept_value_dict
close_concept_value_dict = get_value_close_concept()


# 整理一段时间内，根据股金神话的复盘得到的概念信息
# 输出为dataframe： 17(index)  20170602(date)  合康新能(name)  雄安新区(reason)  300048(ticker)    雄安(concept)
def stock_concept_gjsh(start_date, end_date):
    global mongodb
    start_date = format_date(start_date, "%Y%m%d")
    end_date = format_date(end_date, "%Y%m%d")
    # 将每天的涨停信息转成信号存储的frame格式, key可以去reason（更细致），也可以取big_concept，最后统一都是'reason'
    def get_concept_daily_frame(result_info, ckey='reason'):
        daily_frame = pd.DataFrame()
        tcount = 0
        for dkey in result_info.keys():
            if dkey in ['_id', 'date', 'source']:
                continue
            reason = result_info[dkey][ckey]
            ticker = dkey
            name = result_info[dkey]['name']
            reason = reason.replace(u"+", u"_")
            reason_list = reason.split("_")
            # 将reason分开
            for ec_reason in reason_list:
                if ec_reason.isdigit():
                    continue
                daily_frame.loc[tcount, 'reason'] = ec_reason
                daily_frame.loc[tcount, 'ticker'] = ticker
                daily_frame.loc[tcount, 'name'] = name
                tcount += 1
        daily_frame['date'] = result_info['date']
        return daily_frame

    # 读入每天的涨停概念
    frame_list = []
    for result in mongodb.stock.mirror_info.find({"source":"GJSH_B", "date":{"$gte":start_date, "$lte":end_date}}):
        daily_frame = get_concept_daily_frame(result, ckey='big_concept')
        frame_list.append(daily_frame)
    tframe = pd.concat(frame_list, axis=0)
    tframe['reason'] = tframe['reason'].apply(lambda x: u'次新股' if x == u'次新' else x)

    # 剔除掉某些概念（新股，公告、重组类等）
    repl = re.compile(u'（.*）')
    # 剔除掉新股
    tframe = tframe[(tframe.reason!=u'新股') & (tframe.reason != u'新股上市')]
    # 括号包括括号内的内容都去掉
    tframe['reason'] = tframe['reason'].apply(lambda x: repl.sub("", x))
    # 剔除掉公告、重组类
    tframe = tframe[~((tframe.reason.str.contains(u'重组')) | (tframe.reason.str.contains(u'其它')) | (tframe.reason.str.contains(u'其他'))
                     )]
    # 剔除：以及后面的内容
    repl2 = re.compile(u'：.*')
    tframe['reason'] = tframe['reason'].apply(lambda x: repl2.sub("", x))

    # 剔除 空格以及后面的内容
    repl3 = re.compile(u' .*')
    tframe['reason'] = tframe['reason'].apply(lambda x: repl3.sub("", x))

    # 概念，概念股，概念个股字
    tframe['reason'] = tframe['reason'].apply(lambda x: x.replace(u'概念股', u'').replace(u'个股', u'').replace(u'概念', u''))

    # 读入概念同义词表
    global close_concept_dict
    # 将每一个概念都按照concept_list进行转换
    tframe['concept'] = tframe['reason']
    for concept_name in close_concept_dict.keys():
        for cchar in close_concept_dict[concept_name]:
            tframe['concept'] = tframe['concept'].apply(lambda x: concept_name if cchar in x else x)
    tframe = tframe[[u'ticker', u'concept']]
    return tframe

# 从local的csv记录中，自己标注的group组和选股宝的列得到的股票列表
# 返回的dataframe格式为： 720(index)  000916(stock)   并购重组(group) 并购重组(source_xgb)
def stock_concept_csv(start_date, end_date):
    root_dir = u'D:/Money/modeResee/复盘'
    frame_list = []
    for filename in os.listdir(root_dir):
        if u'.' in filename or len(filename) != 8 or not filename.isdigit() or filename>end_date or filename<start_date:
            continue
        try:
            tmp_frame = pd.read_csv(os.path.join(u"%s/%s" % (root_dir, filename), 'daydayup.csv'), encoding='gbk', index_col=0)
            tmp_frame = tmp_frame[tmp_frame.type.isin(['ZT', 'HD'])]
            tmp_frame['date'] = filename
            frame_list.append(tmp_frame)
            del tmp_frame['news']
        except:
            print "Error when read daydayup csv in stock_concept_gjsh for date:%s" %filename
    csvframe = pd.concat(frame_list, axis=0)
    csvframe = csvframe[[u'stock', u'source_xgb', u'group', u'date']]
    csvframe.reset_index(inplace=True)
    del csvframe['index']
    csvframe.fillna('0', inplace=True)
    for idx in csvframe.index.values:
        csvframe.loc[idx, 'source_xgb'] = csvframe.loc[idx, 'source_xgb'].split("|")[0].strip()
        csvframe.loc[idx, 'group'] = csvframe.loc[idx, 'group'].split("|")[0].strip()

    csvframe['stock'] = csvframe['stock'].apply(lambda x: str(x).zfill(6))
    return csvframe

# 根据时间区间，filter出想要概念的股票
class FindConceptStocks:
    def __init__(self, start_date, end_date):
        # 拿到时间区间内的所有的股票以及对应概念的frame
        self.gjsh_frame = stock_concept_gjsh(start_date, end_date)       # index, ticker, concept
        self.csv_frame = stock_concept_csv(start_date, end_date)         # index, stock, group, source_xgb
        global close_concept_dict, close_concept_value_dict
        self.close_concept_dict = close_concept_dict

    def filter_by_concept(self, concept):
        gjsh_frame = self.gjsh_frame.copy()
        csv_frame = self.csv_frame.copy()

        csv_frame['concept'] = csv_frame['group'] + csv_frame['source_xgb']
        del csv_frame['group']
        del csv_frame['source_xgb']
        csv_frame.rename(columns={"stock":"ticker"}, inplace=True)

        aframe = pd.concat([gjsh_frame, csv_frame], axis=0)
        aframe.reset_index(inplace=True)
        del aframe['index']

        # # 过滤出关注的概念股票
        # concept_keys = []
        # if concept in self.close_concept_dict.keys():
        #     concept_keys = self.close_concept_dict[concept]
        # else:
        #     concept_keys = [concept]

        # 相近的名称
        if concept in close_concept_dict.keys():
            concept_keys = close_concept_dict[concept]
        elif concept in close_concept_value_dict.keys():
            real_concept = close_concept_value_dict[concept]
            concept_keys = close_concept_dict[real_concept]
        else:
            concept_keys = [concept]


        match_frame_list = []
        # 再遍历concept_keys的值，匹配出对应的行
        for concept_key in concept_keys:
            match_frame_list.append(aframe[aframe.concept.str.contains(concept_key)])
            aframe = aframe[~aframe.concept.str.contains(concept_key)]

        match_frame = pd.concat(match_frame_list, axis=0)
        del match_frame['concept']
        match_frame['concept'] = concept
        match_frame.drop_duplicates(subset=['ticker'])
        return match_frame

# 某只股票时期内的涨跌幅
def time_range_accum_ratio(stock, start_date, end_date):
    try:
        start_date = get_lastN_date(start_date, 0)
        end_date = get_lastN_date(end_date, 0)
        s_close = get_mysqlData([stock], [start_date], db_table='vmkt_equd_adj').loc[0, 'CLOSE_PRICE']
        e_close = get_mysqlData([stock], [end_date], db_table='vmkt_equd_adj').loc[0, 'CLOSE_PRICE']
        ratio = 100*(e_close - s_close)/s_close
        ratio = round(ratio, 2)
    except:
        ratio = 'p'
    return ratio


# 根据盟军.txt的key作为最顶级概念域名
def get_top_dns_concept(conceptname):
    if conceptname in close_concept_value_dict.keys():
        real_concept = close_concept_value_dict[conceptname]
        conceptname = real_concept
    return conceptname


# 看一只股票是否走平了
def get_flat_status(stockid, see_date, window_size=3):
    global mysqldb
    see_date = format_date(see_date, '%Y%m%d')
    before_day = get_lastN_date(see_date, 30)
    window_date_list= getDate(before_day, see_date)[-3:]
    # 拿到see_date最近window_size的k线数据
    priceframe = get_mysqlData([stockid], window_date_list, db_table='vmkt_equd_adj')
    # if len(priceframe) != 3:
    #     raise Exception("price frame len <3, no flat status returned")
    priceframe['chg'] = 100*(priceframe['CLOSE_PRICE'] - priceframe['PRE_CLOSE_PRICE'])/priceframe['PRE_CLOSE_PRICE']
    priceframe['chg'] = priceframe['chg'].round(2)
    priceframe['abs_chg'] = abs(priceframe['chg'])

    # 规则1：每天close的幅度在2%
    check1 = (len(priceframe[(priceframe.abs_chg > 2)]) == 0)
    # 规则2：连续3天的累计涨幅在4%以下
    cum_ratio = 100*(np.cumprod(1+priceframe['chg'].values/100)[-1]-1)
    check2 = (cum_ratio<3 if cum_ratio>=0 else cum_ratio>-4)

    return check1&check2


# 跑回归测试，看准确率和召回率
def regression_flat():
    global mongodb
    results = mongodb.pattern.trend.find()
    if results.count() <=0 :
        raise Exception("No regression sample for flat")
    tcount = 0
    dframe = pd.DataFrame()
    for result in results:
        stockid = result['ticker']
        date = result['date']
        status = (result['trend'] == 'flat')
        dframe.loc[tcount , 'ticker'] = stockid
        dframe.loc[tcount, 'date'] = date
        dframe.loc[tcount, 'real_flat'] = status
        dframe.loc[tcount, 'recong_flat'] = get_flat_status(stockid, date)
        tcount += 1

    real_pos = dframe[dframe.real_flat==True]
    print "recall:%s" % str(round(float(1.0*len(real_pos[real_pos.recong_flat == True])/len(real_pos)), 3))
    pred_pos = dframe[dframe.recong_flat == True]
    print "precision:%s" % str(round(float(1.0*len(pred_pos[pred_pos.real_flat == True])/len(pred_pos)), 3))
    return dframe

#
# def window_plat_field(stockid, see_date):
#