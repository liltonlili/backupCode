#coding:utf-8
import os
from pywinauto import application
import time
import logging


class FineReader():
    op = u'打开'
    ok = u'确定'
    cancel = u'取消'
    property = u'exists enabled visible ready'

    def __init__(self,appName="D:\Program Files (x86)\ABBYY FineReader 12\FineReader.exe".decode()):
        self.app=application.Application()
        self.app.start_(appName)
        self.findReader = self.app.FineReader12MainWindowClass
        self.index=0
        self.max()
        time.sleep(2)
        self.cancelDig()
        self.findReader.Minimize()

    # def clear(self,num,mutex):
    #     mutex.acquire()
    #     self.findReader.Maximize()
    #     try:
    #         self.findReader.Wait(self.property).TypeKeys('^N')
    #         clearDlg = self.app.window_(title_re = u"ABBYY FineReader 12", class_name = "#32770")
    #         clearDlg[u"否(&N)"].Click()
    #     except Exception,e:
    #             e
    #     self.findReader.Minimize()
    #     mutex.release()

    def max(self):
        try:
            self.findReader.Maximize()
        except Exception, err:
            logging.getLogger().info("Error when max, err:%s" % err)

    def min(self):
        try:
            self.findReader.Minimize()
        except Exception, err:
            logging.getLogger().info("Error when min, err:%s" % err)

    def openDig(self):
        try:
            self.findReader.Wait(self.property).TypeKeys('^O')
        except Exception, err:
            logging.getLogger().info("Error when open, err:%s" % err)

    def saveDig(self):
        try:
            self.findReader.Wait(self.property).TypeKeys('^S')
            time.sleep(1)
        except Exception, err:
            logging.getLogger().info("Error when save, err:%s" % err)

    def cancelDig(self):
        try:
            infoDlg = self.app.window_(title_re = u"ABBYY FineReader 12", class_name = "#32770")
            if infoDlg.Exists():
                infoDlg[u'否'].Click()
        except Exception, err:
            logging.getLogger().info("Error when save, err:%s" % err)

    # 打开文件
    def open(self, fileName):
        fileName = os.path.abspath(fileName)
        tcount = 10
        logging.getLogger().info("Begin to open file:%s" % fileName)
        while tcount > 0:
            self.max()
            self.openDig()
            openDlg = self.app.window_(title=u'打开图像', class_name=u"#32770")
            while openDlg.Exists:
                try:
                    openDlg.Wait(self.property).TypeKeys(fileName.encode('gbk'))
                    openDlg[self.op].Click()
                except Exception, err:
                    logging.getLogger().info("Error when open, err:%s" %err)
                    self.min()
                finally:
                    openDlg = self.app.window_(title=u'打开图像', class_name=u"#32770")
                    if not openDlg.Exists():
                        break
                    time.sleep(1)
            # print "come out"
            tcount = 30
            while tcount > 0:
                finish_window = self.app.window_(title_re=u"正在将图像添加到文档", class_name = u"#32770")
                if finish_window.Exists():
                    try:
                        if u'处理已完成' in finish_window.Static2.WindowText():
                            finish_window[u'关闭'].Click()
                            break
                    except:
                        pass
                else:
                    time.sleep(2)
                    tcount -= 1
            time.sleep(1)
            self.min()
            return True
        return False

    # 开始转换, 默认是转换的，所以此处不管
    def save(self, outPath):
        outPath = os.path.abspath(outPath)
        tcount = 10
        while tcount > 0:
            self.max()
            self.saveDig()
            saveDlg = self.app.window_(title_re=u'将文档另存为', class_name = "#32770")
            while saveDlg.Exists():
                saveDlg.Wait(self.property).TypeKeys(outPath)
                try:
                    saveDlg[u'保存'].Click()
                    time.sleep(1)
                    saveDlg = self.app.window_(title_re=u'将文档另存为', class_name = "#32770")
                    if not saveDlg.Exists():
                        self.min()
                        self.delete()
                        return True
                except Exception, err:
                    pass
                    self.delete()
                    self.min()
                    return True
            self.delete()
            self.min()
            return False

    # 删除当前页面
    def delete(self):
        try:
            self.max()
            self.findReader.Wait(self.property).TypeKeys('^D')
            infoDlg = self.app.window_(title_re = u"ABBYY FineReader 12", class_name = "#32770")
            while infoDlg.Exists():
                infoDlg[u'是'].Click()
                infoDlg = self.app.window_(title_re = u"ABBYY FineReader 12", class_name = "#32770")
        except Exception,err:
            print "Error when delete page, %s" %err

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(threadName)s Line:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S.000',
                    filename='./logs/FineReader.log',
                    filemode='w+')

    reader = FineReader()
    pic_dir = u"D:/Money/lilton_code/Market_Mode/learnModule/lhc_pic"
    save_dir = u"D:/Money/lilton_code/Market_Mode/learnModule/lhc_pic/save"
    for pic_name in os.listdir(pic_dir):
        if ".png" not in pic_name:
            continue
        # pic_name = u'2015-06-06_94.png'
        status = reader.open(os.path.join(pic_dir, pic_name))
        if status:
            file_name = pic_name.replace(".png",".txt")
            reader.save(os.path.join(save_dir, file_name))
            print "finished %s" %pic_name