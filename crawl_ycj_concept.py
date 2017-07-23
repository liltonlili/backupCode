#coding:utf-8
import requests as rs
import time
import json
import logging
import pymongo
from lxml import etree
import common

headers = {
        "Accept":"application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding":"gzip, deflate",
        "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
        "Host":"www.yuncaijing.com",
        "Origin":"http://www.yuncaijing.com",
        "Referer":"http://www.yuncaijing.com/quote/sz002436.html",
        "X-Requested-With":"XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0"
    }

proxies = {'http':'http://10.20.205.162:1080'}

class CrawlYcjConcept:
    def __init__(self):
        mongourl = "localhost"
        self.mongodb = pymongo.MongoClient(mongourl)
        self.crawl_dict_list = []

    # crawl_dict_list = [
    # {
    #         "topicid": "%s"%i,
    #         "concept": u"雄安新区"
    #     }, {}
    # ,]
    def add_crawl_concept(self, conceptid, conceptname):
        self.crawl_dict_list.append({"topicid":conceptid, "concept":conceptname})

    def crawl_multi_concepts(self):
        return_status = {}
        for crawl_dict in self.crawl_dict_list:
            ycj_len, add_len, rmv_len = self.crawl(crawl_dict)
            return_status[crawl_dict['concept']] = [ycj_len, add_len, rmv_len]
        return return_status

    def crawl(self, conceptDict):
        topicid = conceptDict['topicid']
        concept = conceptDict['concept']
        concept = common.get_top_dns_concept(concept)
        url = "http://www.yuncaijing.com/story/details/id_%s.html" % topicid

        count = 5
        while count > 0:
            r = rs.get(url = url, headers = headers, proxies=proxies)
            if r.status_code == 200:
                break
            logging.getLogger().error("retry to get %s"%url)
        if r.status_code != 200:
            raise Exception("can't reach %s"%url)

        ycj_stock_list = self.parse_html(r.content)
        # 查询数据库中已有的stock_list，并进行动态更新
        db_stock_list = common.get_ycj_stocks(concept)

        add_stock_list = [x for x in ycj_stock_list if x not in db_stock_list]
        rmv_stock_list = [x for x in db_stock_list if x not in ycj_stock_list]

        for stockid in add_stock_list:
            self.insert_mongo(stockid, concept, topicid)
        for stockid in rmv_stock_list:
            self.rmv_mongo(stockid, concept)
        return len(ycj_stock_list), len(add_stock_list), len(rmv_stock_list)


    def parse_html(self, htmlcontent):
        root = etree.HTML(htmlcontent)
        stock_list = []
        for x in root.xpath('//table[@class="table table-ycj table-hover today"]/tbody/tr/@data-code'):
            stock_list.append(x)
        return stock_list


    def insert_mongo(self, stockid, stock_concept, id_v):
        stock_name = common.QueryStockMap(id=stockid)[0]
        self.mongodb.stock.ycj_concept.insert({"stockid": stockid, "concept": stock_concept, "stockname":stock_name, "id":str(id_v)})

    def rmv_mongo(self, stockid, stock_concept):
        self.mongodb.stock.ycj_concept.remove({"stockid": stockid, "concept": stock_concept})

if __name__ == "__main__":
    crawler = CrawlYcjConcept()
    for i in range(2505, 2506):
        print i
        conceptDict = {
            "topicid": "%s"%i,
            "concept": u"雄安新区"
        }
        try:
            crawler.crawl(conceptDict)
            print "crawl finished"
        except Exception,err:
            print "crawl failed"
        finally:
            time.sleep(2)