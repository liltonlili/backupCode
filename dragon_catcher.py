# coding:utf-8
import common
import pymongo
import shutil
import os
import pandas as pd
import datetime

class DRAGON_POOL:
    def __init__(self):
        self.mongodb = common.mongodb
        self.scan_dir = u'C:/Users/li.li/Downloads'
        self.store_dir = u'D:/Money/modeResee/彼战/tree'

    def fresh_dir(self):
        for file_name in os.listdir(self.scan_dir):
            if u'CLASSFIER_' in file_name and u'.html' in file_name:
                file_date = file_name.split("_")[1]
                concept_name = file_name.split("_")[2].split(".")[0]
                target_dir = os.path.join(self.store_dir, "%s/logs"%file_date)
                common.look_up_dir(target_dir)
                # 将文件移到指定位置
                shutil.move(os.path.join(self.scan_dir, file_name), os.path.join(target_dir, file_name))

                # 将文本内容记录到数据库
                with open(os.path.join(target_dir, file_name), 'r') as fHandler:
                    file_str = fHandler.read()
                    file_str = file_str.replace("long_flat", "longFlat").replace("double_bottom", "doubleBottom")
                    self.save_pool_dragon(file_str, concept_name, file_date)

    # 将上一天的dragon pool的内容copy到今天，如果今天没有的话
    def copy_pool_dragon(self, from_date, end_date):
        from_date = common.format_date(from_date, "%Y%m%d")
        from_results = self.mongodb.concepts.dragon_pool.find({"date":from_date})
        if from_results.count() == 0:
            raise BaseException("No dragon pool record for date:%s, failed to copy" % from_date)
        # 昨日的记录
        from_result = from_results[0]
        # 今日数据库的记录
        end_date = common.format_date(end_date, "%Y%m%d")
        end_results = self.mongodb.concepts.dragon_pool.find({"date":end_date})
        end_result = {}
        if end_results.count() > 0:
            end_result = end_results[0]
            del end_result['_id']

        # 二者合并，以end_date的记录进行覆盖式添加
        del from_result['_id']
        del from_result['date']
        for concept in end_result:
            if len(end_result[concept]) > 0:
                from_result[concept] = end_result[concept]
        from_result['date'] = end_date
        self.mongodb.concepts.dragon_pool.update({"date":end_date}, from_result, upsert=True)


    # strcontent格式为：Dragon_002225_false;Wind_002225_true;Remove_002225_false;Dragon_002182_false;
    # 存储格式为：{date:xxxx, "conceptA":{"dragon":[xxxxxx], "wind":[xxx]}}, ...}  # Dragon, Wind类
    # 存储格式为：{date:xxxx, "ticker":"value"}  # up, down ,flat类
    # 每次都是覆盖写入，不支持增添等
    def save_pool_dragon(self, strcontent, concept_name ,tdate):
        # 分成3类， dragon_list, wind_list, remove_list
        str_list = strcontent.split(";")
        dragon_list = [x.split("_")[1] for x in str_list if (u'Dragon' in x and u'true' in x)]
        wind_list = [x.split("_")[1] for x in str_list if (u'Wind' in x and u'true' in x)]
        remove_list = [x.split("_")[1] for x in str_list if (u'Remove' in x and u'true' in x)]
        catch_dict = {}

        # 读取excel
        dframe = pd.read_excel(os.path.join(u'D:/Money/modeResee/彼战', u'战区.xlsx'), encoding='gbk', sheetname=u'类型')
        for idx in dframe.index.values:
            code_str = dframe.loc[idx, u'源码']
            tmp_list = [x.split("_")[1] for x in str_list if (code_str in x and u'true' in x)]
            catch_dict[code_str] = tmp_list

        # 将remove的存到增减排除.csv中
        xframe = pd.read_csv(os.path.join(u'D:/Money/modeResee/彼战', u'增减排除.csv'), encoding='gbk')
        max_id = max(xframe.index.values)+1
        for ticker in remove_list:
            xframe.loc[max_id, 'concept'] = concept_name
            xframe.loc[max_id, 'name'] = common.QueryStockMap(id=ticker)[0]
            xframe.loc[max_id, 'status'] = 'spy'
            max_id += 1
        xframe.to_csv(os.path.join(u'D:/Money/modeResee/彼战', u'增减排除.csv'), encoding='gbk', index=False)



        # 将dragon和wind存到mongo中的concepts, dragon_pool表中
        save_dict = {"date":tdate}
        results = self.mongodb.concepts.dragon_pool.find({"date":tdate})
        if results.count() > 0:
            save_dict = results[0]

        save_dict[concept_name] = {}
        if len(dragon_list) > 0:
            save_dict[concept_name]['dragon'] = dragon_list

        if len(wind_list) > 0:
            save_dict[concept_name]['wind'] = wind_list

        self.mongodb.concepts.dragon_pool.update({"date":tdate}, save_dict, upsert=True)

        # 将up, down, flat存放到mongo中的pattern, trend表中
        for code_str in catch_dict.keys():
            tmp_list = catch_dict[code_str]
            for ticker in tmp_list:
                self.mongodb.pattern.trend.update({"date":tdate, "ticker":ticker},
                                                  {"date":tdate, "ticker":ticker, "trend": code_str},
                                                  upsert=True)

# 将昨天以及之前记录的龙头、排除等信息更新到存储中，今天生成新的文件就会包含昨天的笔记
if __name__ == '__main__':
    x = DRAGON_POOL()
    # 将上一日的copy到今日
    today = datetime.datetime.today().strftime("%Y%m%d")
    lastday = common.get_lastN_date(today, 1)
    x.copy_pool_dragon(lastday, today)
    x.fresh_dir()
    print "dragon pool update finished!"
