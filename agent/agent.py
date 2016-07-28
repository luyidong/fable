#!/usr/bin/python
#coding=utf-8
import Queue
import threading
from time import time,sleep,ctime
import json
import urllib2
import socket
import commands
import sys, os
reload(sys)
sys.setdefaultencoding('utf8')


import pdb #调试
from moniItems import mon #采集模块

#把..目录加入import模块的默认搜索路径中
sys.path.insert(1, os.path.join(sys.path[0], '..'))
#导入Agent发送数据的函数
from nbNet.nbNetFramework import sendData_mh

#Agent 将会向上游的trans模块发送采集到的监控数据
#trans可用地址是一个list
trans_l = ['localhost:50000']

#
exitFlag_coll = 0
exitFlag_send = 0


class antsThread (threading.Thread):
    def __init__(self, name, q, ql=None, interval=None):
        #初始化参数
        threading.Thread.__init__(self) #构造器继承
        self.name = name
        self.q = q #queue size 任务队列
        self.queueLock = ql #queue size 任务队列
        self.interval = interval
        # sendData_mh 采用长连接，这个list用来保存可用的连接
        self.sock_l = [None]

    def run(self):
        #重写run()函数，线程 '蚁人' 从此函数开始执行
        #创建2个分支函数 开启collect采集线程或者sendjson发送数据线程
        #将数据放在任务队列中，sendjson线程负责从任务队列中取出监控数据
        #并将数据通过socket发送给trans
        if self.name.find('collect') != -1:
            print 'Starting ',self.name,'at:',ctime()
            self.put_data()
            print 'Exiting ',self.name,'at:',ctime()
        elif self.name.find('sendjson') != -1:
            print 'Starting ',self.name,'at:',ctime()
            self.get_data()
            print 'Exiting ',self.name,'at:',ctime()


    def put_data(self):
        #collect 进程逻辑
        m = mon()
        atime = int(time())
        print 'put flag', exitFlag_coll
        while not exitFlag_coll:
            self.queueLock.acquire()
            data = m.runAllGet()#采集系统项
            print 'put data:',data,self.getName
            self.q.put(data)
            #规避采集时间间隔不准确 保证采集是self.interval秒/次
            btime = int(time())
            sleep(self.interval-((btime-atime)%self.interval))
            self.queueLock.release()
            sleep(0.01)
    
    def get_data(self):
        #sendjson进程逻辑
        print 'get flag',exitFlag_send
        while not exitFlag_send:
            self.queueLock.acquire()
            if not self.q.empty():
                data = self.q.get()
                print 'get data:',data,self.getName
                #pdb.set_trace() #埋点 设置调试pdb断点
                #通过sendData_mh发送监控数据
                self.queueLock.release()
                sleep(0.01)
          #      sendData_mh(self.sock_l,trans_l,json.dumps(data))
            else:
                self.queueLock.release()
            sleep(self.interval)
        


def main():
    #初始化一个任务队列，队列长度为10，超过10个任务没有被消费，put操作将会阻塞
    q1 = Queue.Queue(10)
    collList = ["collect-1", "collect-2", "collect-3"]
    sendList = ["sendjson-1", "sendjson-2", "sendjson-3"]
    collThreads = []
    sendThreads = []
    ql1 = threading.Lock()
    ql2 = threading.Lock()

    for tName in collList:
        collect = antsThread(tName,q1,ql1,interval=5)
        collect.start()#开启采集线程
        print 'collect',collect
        collThreads.append(collect)

#    sleep(0.1)

    for tName in sendList:
        sendjson = antsThread(tName,q1,ql2,interval=3)
        sendjson.start()#开启采集线程
        sendThreads.append(sendjson)


    while not q1.empty():
        pass
    #通知线程退出
    exitFlag_coll = 1
    exitFlag_send = 1

    print 'start'
    
    #等待所有线程完成
    for t1 in collThreads:
        t1.join()

    for t2 in sendThreads:
        t2.join()
    
    print "Exiting Main Thread"
    
if __name__ == "__main__":
    main()


