import MySQLdb
import sys

class mysqldber:
    def __init__(self,params):
        try:
            self.db=MySQLdb.connect(host=params['host'],port=params['port'],user=params['user'],passwd=params['pw'],db=params['db'],charset="utf8")
        except Exception, err:
            print "Connect %s fail, err:%s"%(params['host'], err)
            pass
    
    def query(self,query):
        curs=self.db.cursor()
        queryData = None
        try:
            curs.execute(query)
            queryData=curs.fetchall()
        except MySQLdb.Error,e:
            print 'Error in Execution. %s'%e
        return queryData

    def upload(self,query):
        curs=self.db.cursor()
        try:
            curs.execute(query)
            self.db.commit()
        except MySQLdb.Error, e:
            raise MySQLdb.Error('Error in upload. %s' %e)
            self.db.rollback()


    def __del__(self):
        self.db.close()
        # del self.db