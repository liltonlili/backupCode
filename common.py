#coding:utf8
from mysqldb import *
import pandas as pd
import datetime
import os
import numpy as np
import tushare as ts
import time
import requests
import pymongo
from pandas import DataFrame,Series
import matplotlib.pyplot as plt
from Tkinter import *
from tkMessageBox import *
import Tkinter as tk
import json
import shutil

mongourl = "localhost"
global mongodb
mongodb = pymongo.MongoClient(mongourl)

def connectdb():
    # mydbs='a'
    # mydb='b'
    # dydb='c'
    mydbs=mysqldb({'host': 'db-bigdata.wmcloud-qa.com', 'user': 'app_bigdata_ro', 'pw': 'Welcome_20141217', 'db': 'bigdata', 'port': 3312})
    mydb = mysqldb({'host': '10.21.232.43', 'user': 'app_gaea_ro', 'pw': 'Welcome20150416', 'db': 'MarketDataL1', 'port': 5029})  ##分笔，分钟级
    dydb  = mysqldb({'host': 'db-datayesdb-ro.wmcloud.com', 'user': 'app_gaea_ro', 'pw': 'EQw6WquhnCKPp8Li', 'db': 'datayesdbp', 'port': 3313})
    cardb = mysqldb({'host': 'db-news.wmcloud-stg.com', 'user': 'app_bigdata_ro', 'pw': 'Welcome_20141217', 'db': 'news', 'port': 3310})
    souhudbs = mysqldb({'host': 'db-datayesdb-ro.wmcloud.com', 'user': 'app_gaea_ro', 'pw': 'EQw6WquhnCKPp8Li', 'db': 'datayesdb', 'port': 3313})
    souhudbi = mysqldb({'host': 'db-bigdata.wmcloud-qa.com', 'user': 'app_bigdata_ro', 'pw': 'Welcome_20141217', 'db': 'bigdata', 'port': 3312})
    # souhudbi = mydbs
    # localdb = mysqldb({'host': '127.0.0.1', 'user': 'root', 'pw': '', 'db': 'stock', 'port': 3306})
    localdb = None
    return (mydbs,mydb,dydb,localdb,cardb,souhudbs,souhudbi)

class mysqldata:
    def __init__(self):
        (self.mydbs,self.mydb,self.dydb,self.localdb,self.cardb,self.souhudbs,self.souhudbi)=connectdb()

    def dydbs_query(self,sqlquery):
        return pd.read_sql(sqlquery,con=self.mydbs.db)

    def dydb_query(self,sqlquery):
        return pd.read_sql(sqlquery,con=self.dydb.db)

    def mydb_query(self,sqlquery):
        return pd.read_sql(sqlquery,con=self.mydb.db)

    def localdb_query(self,sqlquery):
        return pd.read_sql(sqlquery,con=self.localdb.db)

    def car_query(self,sqlquery):
        return pd.read_sql(sqlquery,con=self.cardb.db)

    def souhus_query(self,sqlquery):
        return pd.read_sql(sqlquery,con=self.souhudbs.db)

    def souhui_query(self,sqlquery):
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

#      TICKER_SYMBOL SEC_SHORT_NAME  TRADE_DATE  PRE_CLOSE_PRICE  OPEN_PRICE    HIGHEST_PRICE   LOWEST_PRICE  CLOSE_PRICE
# 0           000033          *ST新都  2016-04-27            10.38        0.00           0.00          0.00        10.38
# 1           600710          *ST常林  2016-04-27             9.36        0.00         10.61         10.52        10.57

def get_mysqlData(stock_list,date_list):
    # mysqldb = mysqldata()
    global mysqldb
    stock_list = [str(x).replace('sh',"").replace('sz',"").replace(".","").replace("SH","").replace("SZ","") for x in stock_list]
    stock_list = ['0'*(6-len(str(x)))+str(x) for x in stock_list]
    date_list = [format_date(x,"%Y-%m-%d") for x in date_list]
    date_list = str(date_list).replace("[","(").replace("]",")")
    # print stock_list
    # print date_list

    table="vmkt_equd"
    if len(stock_list) > 0:
        stock_list = str(stock_list).replace("[","(").replace("]",")")
        query = "SELECT TICKER_SYMBOL, SEC_SHORT_NAME, TRADE_DATE, PRE_CLOSE_PRICE, OPEN_PRICE, HIGHEST_PRICE, LOWEST_PRICE, CLOSE_PRICE, ACT_PRE_CLOSE_PRICE " \
                "from %s where TICKER_SYMBOL in %s and TRADE_DATE in %s"%(table,stock_list, date_list)
    else:
        query = 'SELECT TICKER_SYMBOL, SEC_SHORT_NAME, TRADE_DATE, PRE_CLOSE_PRICE, OPEN_PRICE, HIGHEST_PRICE, LOWEST_PRICE, CLOSE_PRICE, ACT_PRE_CLOSE_PRICE  ' \
                'from %s where TRADE_DATE in %s and TICKER_SYMBOL < "700000" '%(table,date_list)
    dataFrame = mysqldb.dydb_query(query)
    return dataFrame



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


# date为['2016-03-27'],output为['2016-03-26']
def get_lastN_date(date,n):
    calframe=pd.read_csv(os.path.join("D:\Money","cal.csv"))
    del calframe['0']
    calframe.columns=['Time']
    format_str=format_date(date,"%Y/%m/%d")
    index=calframe[calframe.Time==format_str].index
    last_index= index-n
    if last_index > calframe.index.values[-1]:
        last_index = calframe.index.values[-1]
        last_date=str(calframe.loc[last_index,'Time'])
    else:
        last_date=str(calframe.loc[last_index,:]['Time'].values[0])
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
                    formatDate="19890928"
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
    print baseline
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
    if id != '':
        queryResult = mongodb.stock.stockmap.find_one({"stockid":id})
        if queryResult is not None:
            return [queryResult['stock_name'],queryResult['stockid']]
        else:
            return [0,0]
    elif name != '':
        queryResult = mongodb.stock.stockmap.find_one({"stock_name":name})
        if queryResult is not None:
            return [queryResult['stock_name'],queryResult['stockid']]
        else:
            return [0,0]
    else:
        return [0,0]

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
        DEAL_AMOUNT from vmkt_equd where TRADE_DATE >= '%s' and TRADE_DATE <='%s' and TICKER_SYMBOL = '%s'"%(start_date,end_date,code)
        sub = get_mysqlData_sqlquery(sql)
    elif id_type == 0:
        idxcode = "000001"
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
    if id_type == 1:
        stockid = "0"*(6-len(str(int(stockid))))+str(int(stockid))
        # table = "equity_pricefenbi%s"%tableTime
        table = "MarketDataTDB.equity_pricemin%s"%tableTime
        dtsql = "SELECT * from %s where ticker = %s and datadate = %s"%(table,stockid,endDate)
        dtv = get_mydb_sqlquery(dtsql)
        if len(dtv) == 0:
            table = "MarketDataL1.equity_pricemin%s"%tableTime
            dtsql = "SELECT * from %s where ticker = %s and datadate = %s"%(table,stockid,endDate)
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
    table = "MarketDataTDB.equity_pricefenbi%s"%tableTime
    dtsql = "SELECT * from %s where ticker = %s and datadate = %s"%(table,int(stockid),int(endDate))
    dtv = get_mydb_sqlquery(dtsql)
    if len(dtv) == 0:
        table = "MarketDataL1.equity_pricefenbi%s"%tableTime
        dtsql = "SELECT * from %s where ticker = %s and datadate = %s"%(table,int(stockid),int(endDate))
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
# LEGEND_REPLACE = ['legendA','legendB']
# dframe 列必须为： index  bartime, stockid1, stockid2, ...
# 根据dframe的每一个stockid列，生成一个曲线，可以点击取消
def curve_html(dframe):
    x = '''
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
    <html>
        <head>
           <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <title>amCharts Example</title>
            <!--link rel="stylesheet" href="style.css" type="text/css"-->
            <script src="./conf/jquery-3.1.0.min.js" type="text/javascript"></script>
            <script src="./conf/echarts.min.js" type="text/javascript"></script>
            <script type="text/javascript">
            var chart;

            window.onload = function() {
                show_pic();
            }

            function show_pic() {
                var series=[];
                var option = {
                    title: {
                        text: 'compare',
                        left: 'center'
                    },
                    tooltip: {
                        trigger: 'item',
                        formatter: '{a} <br/>{b} : {c}'
                    },
                    legend: {
                        data: LEGEND_REPLACE,
                        left:'left'
                    },
                    xAxis: {
                        type: 'category',
                        name: 'x',
                        splitLine: {show: false},
                        data: XAXIS_REPLACE
                    },
                    yAxis: {
                      //  type: 'value',
                       // min: -10,
                        //max:10
                    },
                    series: SERIES_REPLACE
                };
                var legend={left:"left",data:[]};
                var xAxis={
                    type: 'category',
                    name: 'x',
                    splitLine: {show: false},
                    data: []
                }

                //alert(option)
                //option["title"]={text:"hello", left:'center'};
                //option["xAxis"]=xAxis;
                //option["legend"]=legend;
                //option["series"]=series;
                console.log(option)
                var myChart = echarts.init(document.getElementById('chartdiv'));
                myChart.setOption(option);
                //writeObj(option['legend'])
            }



            </script>
        </head>
        <body style="background-color:#EEEEEE">
            <div id="chartdiv" style="width:800; height:800px; background-color:#FFFFFF"></div>
        </body>
    </html>
'''
    list_series = []
    list_legend = []
    for index in range(1, len(dframe.columns)):
        name = dframe.columns[index]
        # print name
        data_list = str(list(dframe.loc[:, name]))
        time_list = str(list(dframe.loc[:, 'barTime']))
        time_list = time_list.replace("u", "")
        # data = str([[time_list[i], data_list[i]] for i in range(len(data_list))])
        c_name = QueryStockMap(id = name)[0].encode("utf-8")
        tmp_dict = {
            "name":name,
            "type":'line',
            "data":data_list
        }
        list_legend.append(name)
        list_series.append(tmp_dict)
    list_series = str(list_series)
    list_series = list_series.replace('"[','').replace("'data': '[","data:[").replace("]'","]").replace("'type':","type:").replace("'name':","name:")
    list_legend = str(list_legend)
    text = x.replace("SERIES_REPLACE", list_series).replace("LEGEND_REPLACE", list_legend).replace("XAXIS_REPLACE", time_list)
    return text

# 将一个np.array的closePrice变成%
def normalize_frame(np_arr, last_price):
    open_arr = np.array([last_price] * len(np_arr))
    tmp_array = 100*(np_arr - open_arr)/open_arr
    tmp_array = tmp_array.round(2)
    return tmp_array


def get_html_curve(dframe, html_name, save_dir = "./"):
    text = curve_html(dframe)
    if not os.path.exists(os.path.join(save_dir, "conf/")):
        os.mkdir(os.path.join(os.path.join(save_dir, "conf/")))
    print os.curdir
    if not os.path.exists(os.path.join(save_dir, "conf/jquery-3.1.0.min.js")):
        shutil.copy(os.path.join(os.curdir, "./conf/jquery-3.1.0.min.js"), os.path.join(save_dir, "conf/jquery-3.1.0.min.js"))
    print os.curdir
    if not os.path.exists(os.path.join(save_dir, "conf/echarts.min.js")):
        shutil.copy(os.path.join(os.curdir, "./conf/echarts.min.js"), os.path.join(save_dir, "conf/echarts.min.js"))
    fHandler = open(os.path.join(save_dir,"%s.html"%html_name), 'wb')
    fHandler.write(text)
    fHandler.close()

# 判断一个股票在某天，是否最高点涨停过
# 条件1： 滤除开盘就涨停的时间段，从打开涨停之后算
# fenbi_frame: datadate, datatime, ticker, exchangecd, lastprice, volume, side
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