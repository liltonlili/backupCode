#coding:utf-8
import cv2
import numpy as np
import requests as rq
import tushare as ts
import time
import datetime
import common
import pandas as pd
import pymongo
import os
import shutil
import sys
import intelligent_eye

mongodb = pymongo.MongoClient('localhost')
results = mongodb.stock.ZDT_by_date.find({"date":{"$gte":"20161010", "$lte":"20161010"}})
for result in results:
    date = result['date']
    date = common.format_date(date, "%Y%m%d")
    print date
    x = intelligent_eye.IntelliGentEye(day = date)
    x.scan()


