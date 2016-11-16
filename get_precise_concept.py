#coding:utf-8

# 将两个源的股票和概念合并
import pymongo
import pandas as pd
import common

mongo_url = "localhost"
mongodb = pymongo.MongoClient(mongo_url)
jrjConcepts = mongodb.stock.jrj_concept.find({"concept":u"SZGZ"})
ycjConcepts = mongodb.stock.ycj_concept.find({"concept":u"SZGZ"})

jrj_dict = {}
for jrjconcept in jrjConcepts:
    stockid = jrjconcept['stockid']
    reason = jrjconcept['reason'].strip().replace("\n","")
    stockname = jrjconcept['stockname']
    # percent = jrjconcept['percenoct']
    jrj_dict[str(stockid)] = {'reason':reason, 'name':stockname}
    # jrj_dict[stockid]['percent'] = percent

ycj_dict = {}
for ycjconcept in ycjConcepts:
    stockid = ycjconcept['stockid']
    reason = ycjconcept['reason'].strip().replace("\n","")
    percent = ycjconcept['percent']
    stockname = ycjconcept['stockname']
    ycj_dict[str(stockid)] = {'reason':reason, "percent":percent, "name":stockname}

total_list = ycj_dict.keys()
total_list.extend(jrj_dict.keys())
total_list = list(set(total_list))

total_dict = {}
for x in total_list:
    if x in ycj_dict.keys() and x not in jrj_dict.keys():
        total_dict[x] = ycj_dict[x]
    elif x in jrj_dict.keys() and x not in ycj_dict.keys():
        total_dict[x] = jrj_dict[x]
    else:
        total_dict[x] = ycj_dict[x]
        total_dict[x]['reason'] = total_dict[x]['reason'].strip().replace("\n","") + "|" + jrj_dict[x]['reason'].strip().replace("\n","")

start_date = "20150810"
end_date = "20160818"
count = 0
tframe = pd.DataFrame()
for item in total_dict:
    tframe.loc[count, 'stockid'] = item
    if 'percent' in total_dict[item].keys():
        tframe.loc[count, 'percent'] = total_dict[item]['percent']
    tframe.loc[count, 'name'] = total_dict[item]['name']
    ZT_frame, DT_frame = common.zt_stats(item, start_date, end_date)
    tframe.loc[count, 'zt_num'] = len(ZT_frame)
    tframe.loc[count, 'dt_num'] = len(DT_frame)
    tframe.loc[count, 'reason'] = total_dict[item]['reason']
    count += 1

tframe.to_csv(u"./全概念/SZGZ.csv",encoding='gbk')



