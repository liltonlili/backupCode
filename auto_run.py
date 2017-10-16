# coding:utf-8
'''
每晚11点左右跑，便于后面的追踪、复牌，智能化
'''
import pandas as pd
import numpy as np
import sys
import os
import datetime
import time


# 复盘/日期文件下的坚持自己.bat
def run_daily_part1():
    current_day = datetime.datetime.today().strftime("%Y%m%d")
    run_dir = os.path.join(u'D:/Money/modeResee/复盘', current_day)
    # 运行该目录下的part1.bat
    if u'part1.bat' in os.listdir(run_dir):
        print 'will run part1.bat'
        os.system(os.path.join(run_dir, 'part1.bat').encode("gbk"))
        time.sleep(600)
        # 再运行part2
        os.system(os.path.join(run_dir, 'part2.bat').encode("gbk"))
    else:
        print 'no part1.bat, skip run @ %s' % current_day

if __name__ == '__main__':
    run_daily_part1()
