#coding:utf-8
from flask import Flask, request
from flask_restful import Resource, Api
import pymongo
import redis
import time

class Monitor_concept():
    def __init__(self):
        mongo_url = "localhost"
        self.mongodb = pymongo.MongoClient(mongo_url)
        self.redis = redis.Redis(host='localhost', port=6379, db=1)
        self.concepts = []
        self.concept_stock_dict = {}
        self.get_concept_list()

    def get_concept_list(self):
        self.concepts = self.mongodb.stock.myconcept.distinct("concept")
        for concept in self.concepts:
            # print concept
            results = self.mongodb.stock.myconcept.find({"concept":concept})
            self.concept_stock_dict[concept] = []
            for result in results:
                stockid = result['stockid']
                stockname = result['name']
                # print stockname
                self.concept_stock_dict[concept].append([stockid, stockname])

    def run(self):
        while 1:
            for concept_name in self.concept_stock_dict:
                try:
                    value_list = []
                    for stockid, stockname in self.concept_stock_dict[concept_name]:
                        try:
                            # print stockid, stockname
                            rate = eval(self.redis.get(stockid))[1]
                            value_list.append([stockid, stockname, rate])
                        except:
                            pass
                    value_list.sort(lambda x,y: cmp(y[2],x[2]))
                    self.redis.set(concept_name, value_list)
                except Exception,err:
                    print err
            time.sleep(5)

if __name__=='__main__':
    z=Monitor_concept()
    z.run()