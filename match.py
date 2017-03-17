# coding:utf-8
import requests
import time as tt
from docx import Document
from docx.shared import Inches
from lxml import etree
import common
import os
import sys
import logging
import logging.config
import spider_tgb
import pandas as pd
from pandas import DataFrame, Series
import json
import time
reload(sys)
sys.setdefaultencoding("utf8")

general_headers = {
    "Accept":"*/*",
    "Accept-Encoding":"gzip, deflate",
    "Accept-Language":"zh-CN,zh;q=0.8",
    "Connection":"keep-alive",
    "Content-type":"application/x-www-form-urlencoded; charset=UTF-8",
    # "Cookie":"tgbuser=1108357; tgbpwd=E7585F054BCo5w5qm0rynsm9i1; zhihu=1; bdshare_firstime=1481121705711; JSESSIONID=1efc8401-523f-4605-9b16-2263fc8b1444; CNZZDATA1574657=cnzz_eid%3D1495064399-1481119135-%26ntime%3D1481464764",
    "Host":"www.taoguba.com.cn",
    "Origin":"http://www.taoguba.com.cn",
    "Referer":"http://www.taoguba.com.cn/Article/1552117/1",
    "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
    "X-Requested-With":"With:XMLHttpRequest"
}

params = {
        "spMatchSeq":5,
        "lookedUserID":1,
        "lookedUserName":""
    }
def crawl_match_details(params):
    global s, match_url
    r = s.post(url=match_url, data=params, headers=general_headers, allow_redirects=True)
    if r.status_code != 200:
        print "Error when crawl %s, %s" %(params['lookedUserID'], params['lookedUserName'])
        return DataFrame()
    content = r.content.decode("utf-8")
    dict_content = json.loads(content)
    dframe = DataFrame()
    count = 0
    for dicts in dict_content['dto']['map']['listSp']:
        user = dicts['userName']  #名字
        date = dicts['endDateNum'] #日期
        date = common.format_date(date, "%Y/%m/%d")
        fistMoney = dicts['firstMoney']  # 初始资产
        preMoney = dicts['preMoney']  # 昨日资产
        nowMoney = dicts['nowMoney']  # 今日资产
        todayRate = float(dicts['todayRate'])/100  # 今日收益
        lastRate = float(dicts['preRate'])/100  # 昨日收益
        totalRate = float(dicts['totalRate'])/100  # 总收益
        position = dicts['position']  # 仓位
        stockName = []  # 持有股票代码
        stockId = []  # 持有股票名称
        urls = dicts['imgUrl'].split(u",")
        t_url = []
        for url in urls:
            if len(url) > 2:
                url = url.replace(u"../", u"")
                t_url.append(u"http://image.taoguba.com.cn/" + url)
        jgdurl = u",".join(t_url)

        for stockinfos in dicts['listStock']:
            stockName.append(stockinfos['stock']['stockName'])
            stockId.append(stockinfos['stockCode'])
        dframe.loc[count, u'名字'] = user
        dframe.loc[count, u'日期'] = date
        dframe.loc[count, u'初始资产'] = fistMoney
        dframe.loc[count, u'昨日资产'] = preMoney
        dframe.loc[count, u'今日资产'] = nowMoney
        dframe.loc[count, u'今日收益'] = todayRate
        dframe.loc[count, u'昨日收益'] = lastRate
        dframe.loc[count, u'总收益'] = totalRate
        dframe.loc[count, u'仓位'] = position
        dframe.loc[count, u'持有股票'] = "_".join(stockName)
        dframe.loc[count, u'持有股票ID'] = "_".join(stockId)
        dframe.loc[count, u'交割单'] = jgdurl
        count += 1
    return dframe

# pairs = [[1838345, u'窥股忘返'], [591447, u'著名刺客'], [525661,u'小段公子'], [97684, u'selphi81']]
pairs = [[1838345, u'窥股忘返'], [97684, u'selphi81']]
global s, match_url, pic_dir
match_url = "http://www.taoguba.com.cn/spmatch/lookSpmatch"

pic_dir = u'D:/Money/lilton_code/Market_Mode/百万杯/交割单'

# http://image.taoguba.com.cn/img/2016/12/13/luaopo5wcnct.png
# 接下来，需要把pic_dir拼凑到里面

# 开始登陆淘股吧
s = requests.Session()
login_url = 'http://www.taoguba.com.cn/newLogin'
r = s.post(url=login_url, headers=spider_tgb.headers, data=spider_tgb.data, allow_redirects=True)
if r.status_code == 200:
    print "login finished!"
else:
    print "login failed"
tdframe = DataFrame()
frame_list = []
for [id, name] in pairs:
    print "crawling %s"%name
    params['lookedUserID'] = id
    params['lookedUserName'] = name
    tmp_dframe = crawl_match_details(params)
    print "... finished!, len:%s" %len(tmp_dframe)
    frame_list.append(tmp_dframe)
    time.sleep(2)
tdframe = pd.concat(frame_list, axis=0)
# tdframe.to_csv(os.path.join(u'D:/Money/lilton_code/Market_Mode/百万杯',u'比赛记录.xlsx'))
tdframe.to_csv(os.path.join(u'D:/Money/lilton_code/Market_Mode/百万杯',u'比赛记录.csv'), encoding='utf-8')

