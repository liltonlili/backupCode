#coding:utf-8
import logging
import redis
import RealPrice
import monitor_concept
from flask import Flask, request, app, jsonify
from flask_restful import Resource, Api
import multiprocessing

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


if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(threadName)s Line:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S.000',
                    filename='./logs/Center_Chain.log',
                    filemode='w+')


    p1 = multiprocessing.Process(target=getdata2redis)
    p1.start()

    p1 = multiprocessing.Process(target=concept_calculate)
    p1.start()

    # flask API, 用来相应get请求
    while True:
        try:
            api = Api(app)
            # api.add_resource(SubmitTask, "/pdf2html/tasks")
            app.run(host="0.0.0.0", port=8080, debug=False)
        except Exception,err:
            logging.getLogger().error("unexpected exception in api, err:%s" %err)


