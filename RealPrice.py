#coding:utf-8
# __author__ = 'li.li'
import pandas as pd
from pandas import DataFrame
import os
import requests
import time
import numpy as np
import multiprocessing
import threading
from threading import *
import tushare as ts
import logging
import redis
import sys
sys.path.append("D:/projects/report_download/src/lib")
import http_downloader
import common

frame_list=[]
global redisc
redisc = redis.Redis(host='localhost', port=6379, db=1)

class RealPrice():
    def __init__(self):
        self.priceFrame = DataFrame()       #实时价格，总frame
        self.initial_stock_list()

    def run(self):
        status = False
        while 1:
            try:
                ttime = time.localtime()
                thour = ttime.tm_hour
                tmin = ttime.tm_min
                if (thour == 10 and tmin < 3) or (thour == 11 and tmin < 3) or (thour == 13 and tmin < 10 and tmin >= 8):
                    if not status:
                        self.initial_stock_list()
                    status = True
                else:
                    self.runBatch()
                    # print self.priceFrame.head(5)
                    self.update_redis()
                    if (thour > 15) or (thour == 15 and tmin > 5):
                        print "today's monitor finished!"
                        break
                    status = False
                    time.sleep(20)
            except Exception, err:
                print "Error when do job, err:%s" % err
                # logging.getLogger().exception("Error when do job, err:%s" % err)
                time.sleep(20)




    # 获取股票代码列表
    def initial_stock_list(self):
        # 清空redis
        global redisc
        redisc.flushdb()
        try:
            stock_list = common.get_stock_list_from_many_site()
            print "initialize stocklist finished!"

            stock_lists=[]

            for code in stock_list:
                code = '0'*(6-len(str(code)))+str(code)
                if code[0:2] == '60':
                    code = 'sh'+code
                else:
                    code = 'sz'+code
                stock_lists.append(code)
            self.stock_lists=list(set(stock_lists))
            self.groupID=range(len(stock_lists)/200+1)
        except Exception, err:
            print "Encount error when initial stock list, err:%s" % err
            # logging.getLogger().error("Encount error when initial stock list, err:%s" % err)

    def get_data(self,stock_list,timestamp,i):
        dir = 'D:\Money\Realtime'
        slist=','.join(stock_list)
        url = "http://hq.sinajs.cn/list=%s"%slist
        # print url
        try:
            r=requests.get(url)
        except:
            count = 0
            while True:
                ip = http_downloader.get_proxyip(dynamic=False)
                proxies = {'http':'http://{}:{}'.format(ip['host'], ip['port'])}
                try:
                    r=requests.get(url, proxies=proxies)
                    if r.status_code == 200 and len(r.content) > 50:
                        break
                except:
                    print "will retry %s times to get the sina data"%count
                    count += 1

        content=r.content.decode('gbk')
        Dframe=self.parse_content(content,timestamp)
        Dframe.to_csv(os.path.join(dir,'%s_realtime.csv'%i))
        return Dframe

    def parse_content(self,content,timestamp):
        Inframe=DataFrame()
        i = 0
        strarray=content.split(';')
        for item in strarray:
            item_array=item.split(',')
            if len(item_array)<10:
                continue
            stockid = item_array[0][14:20]
            stockid = item_array[0].split('=')[0].split('str_')[1][2:]
            close = item_array[3]
            preclose = item_array[2]
            high = item_array[4]
            low = item_array[5]
            # if high == '0.000':
            #     high = close
            #     low =
            Inframe.loc[i,'time']=timestamp
            Inframe.loc[i,'stcid']=stockid
            Inframe.loc[i,'close']=close
            Inframe.loc[i,'preclose']=preclose
            Inframe.loc[i,'high']=high
            Inframe.loc[i,'low']=low

            i+=1
        try:
            Inframe['rate']=100*(Inframe['close'].astype(np.float64)-Inframe['preclose'].astype(np.float64))/Inframe['preclose'].astype(np.float64)
        except Exception, err:
            print "Exceptions when parse content"
            print content
        Inframe['rate']=Inframe['rate'].round(decimals=2)
        # Inframe['hate']=100*(Inframe['high'].astype(np.float64)-Inframe['preclose'].astype(np.float64))/Inframe['preclose'].astype(np.float64)
        # Inframe['hate']=Inframe['hate'].round(decimals=2)`
        return Inframe

    # priceFrame
    # time   stcid  close  preclose   high   rate
    def update_redis(self):
        global redisc
        tmpframe = self.priceFrame[['close', 'preclose', 'high', 'low', 'stcid', "rate"]]
        tmpframe.set_index("stcid", inplace=True)
        # price_dict = dict(tmpframe['close'])
        for key in tmpframe.index.values:
            close = tmpframe.loc[key,'close']
            preclose = tmpframe.loc[key,'preclose']
            high = tmpframe.loc[key,'high']
            low = tmpframe.loc[key,'low']
            rate = tmpframe.loc[key, 'rate']
            key = "0" * (6-len(str(key))) + str(key)
            # if key == "002867":
            #     print close, rate
            redisc.set(key, [close, preclose, high, low, rate])
        logging.getLogger().info("update redis finished!")


    '''
    #       time   stcid  close  preclose   high   rate
    # 0  08:41:52  603515  21.51     14.94  21.51  43.98
    # 1  08:41:52  601390   7.98      7.25   7.98  10.07
    # 2  08:41:52  600187   6.13      5.57   6.13  10.05
    # 3  08:41:52    2264  10.63      9.66  10.63  10.04
    # 4  08:41:52    2212  15.02     13.65  15.02  10.04
    '''
    def runBatch(self):
        timestamp=time.strftime("%X",time.localtime())
        for i in self.groupID:
            if (i+1)*200 > len(self.stock_lists):
                subproc=multiprocessing.Process(target=self.get_data,args=(self.stock_lists[i*200:],timestamp,i))
            else:
                subproc=multiprocessing.Process(target=self.get_data,args=(self.stock_lists[i*200:(i+1)*200],timestamp,i))
            subproc.start()
        subproc.join(60)
        self.priceFrame=self.get_summary()


    def get_summary(self):
        dir = 'D:\Money\Realtime'
        frame_list=[]
        for i in self.groupID:
            tmpframe=pd.read_csv(os.path.join(dir,'%s_realtime.csv'%i))
            del tmpframe['Unnamed: 0']
            frame_list.append(tmpframe)
        ttframe=pd.concat(frame_list,axis=0)
        return ttframe


if __name__== '__main__':
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(threadName)s Line:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S.000',
                    filename='./logs/RealTimePrice.log',
                    filemode='w+')

    realTimePrice = RealPrice()
    realTimePrice.run()




