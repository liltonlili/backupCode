# coding:utf-8
import os
import sys
sys.path.append(u"D:/Money/lilton_code/Market_Mode/rocketup/strategy/cxhf")
import time
import ControlCX
import CxPlot

while True:
    ttime=time.localtime()
    thour=ttime.tm_hour
    tmin=ttime.tm_min
    if thour >= 10 and tmin > 1:
    # if thour >= 18 and tmin > 15:
        # 更新次新数据库
        ControlCX.reControlCx(start_day="20161201")
        # 开始画图-次新分布
        CxPlot.main(start_day = "20160108")
        break
    else:
        print "wait for summarizing html, %s"%time.strftime("%X", time.localtime())
        time.sleep(600)
