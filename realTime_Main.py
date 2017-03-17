#coding:utf-8
import logging
import redis
import RealPrice
import monitor_concept
from flask import Flask, request, app, jsonify
from flask_restful import Resource, Api
import multiprocessing
import os
import tfp_scan
import time
import pymongo

app = Flask(__name__)

global rediser
rediser = redis.Redis(host='localhost', port=6379, db=1)

@app.route('/conceptList/<conceptName>')
def ConceptResponse(conceptName):
    global rediser
    if conceptName == u'ldc':
        conceptName = u'锂电池'
    response = rediser.get(conceptName)
    logging.getLogger().info(response)
    return response

def getdata2redis():
    # 获取实时数据到redis
    realTimePrice=RealPrice.RealPrice()
    realTimePrice.run()

def concept_calculate():
    # 实时监控各个板块的动向
    Monitor = monitor_concept.Monitor_concept()
    Monitor.run()

def tfp_update():
    # 定时更新停复牌表
    TFPer = tfp_scan.TFP_Crawler()
    mongodb = pymongo.MongoClient("localhost")
    while 1:
        ttime=time.localtime()
        thour=ttime.tm_hour
        tmin=ttime.tm_min

        # 数据库中记录的上午刷新时间
        dict_am = mongodb.stock.FP.find({"flag_attr":"am"})[0]
        am_last_time = dict_am['am_time']

        # 数据库中记录的下午刷新时间
        dict_pm = mongodb.stock.FP.find({"flag_attr":"pm"})[0]
        pm_last_time = dict_pm['pm_time']

        # 如果数据库记录时间超过了早晨时间，说明已经更新过，不再更新
        if am_last_time >= "%s 9:20"%time.strftime("%Y-%m-%d", time.localtime()):
            pass
        # 否则需要更新早晨状态
        else:
            if thour > 9 or ((thour == 9) and tmin >= 20):  # 说明应该更新上午的停复牌信息
                TFPer.crawl()
                mongodb.stock.FP.update({"flag_attr":"am"},
                                        {"$set":{"flag_attr":"am", "am_time":"%s" % time.strftime("%Y-%m-%d %H:%M", time.localtime())}},
                                        True, True)

        # 如果数据库记录时间超过了下午时间，说明已经更新过，不再更新
        if pm_last_time >= "%s 12:40"%time.strftime("%Y-%m-%d", time.localtime()):
            pass
        # 否则需要更新中午状态
        else:
            if thour > 12 or ((thour == 12) and tmin >= 40):  # 说明应该更新下午的停复牌信息
                TFPer.crawl()
                mongodb.stock.FP.update({"flag_attr":"pm"},
                                        {"$set":{"flag_attr":"pm", "pm_time":"%s" % time.strftime("%Y-%m-%d %H:%M", time.localtime())}},
                                        True, True)
        # 6点之后更新一次，再break
        if pm_last_time >= "%s 18:00"%time.strftime("%Y-%m-%d", time.localtime()):
            TFPer.crawl()
            break

        time.sleep(600)

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(threadName)s Line:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S.000',
                    filename=os.path.join('D:/Money/lilton_code/Market_Mode/rocketup/logs,Center_Chain.log'),
                    filemode='w+')


    p1 = multiprocessing.Process(target=getdata2redis)
    p1.start()

    p2 = multiprocessing.Process(target=tfp_update)
    p2.start()
    # p1 = multiprocessing.Process(target=concept_calculate)
    # p1.start()

    # # flask API, 用来相应get请求
    # while True:
    #     try:
    #         api = Api(app)
    #         # api.add_resource(SubmitTask, "/pdf2html/tasks")
    #         app.run(host="0.0.0.0", port=8080, debug=False)
    #     except Exception,err:
    #         logging.getLogger().error("unexpected exception in api, err:%s" %err)


