#!/usr/bin/env python
#coding=utf-8
import json
import urllib
import inspect
import os,time,socket

userDefine_check_time = 0
userDefine_json = []

class mon:
    def __init__(self):
        self.data = {}

    def getLoadAvg(self):
        with open('/proc/loadavg') as load_open:
            a = load_open.read().split()[:3]
            #return "%s %s %s" % (a[0],a[1],a[2])
            return   float(a[0])
    
    def getMemTotal(self):
        with open('/proc/meminfo') as mem_open:
            a = int(mem_open.readline().split()[1])
            return a / 1024
    
    def getMemUsage(self, noBufferCache=True):
        if noBufferCache:
            with open('/proc/meminfo') as mem_open:
                T = int(mem_open.readline().split()[1]) #Total
                F = int(mem_open.readline().split()[1]) #Free
                B = int(mem_open.readline().split()[1]) #Buffer
                C = int(mem_open.readline().split()[1]) #Cache
                return (T-F-B-C)/1024
        else:
            with open('/proc/meminfo') as mem_open:
                a = int(mem_open.readline().split()[1]) - int(mem_open.readline().split()[1])
                return a / 1024
    
    def getMemFree(self, noBufferCache=True):
        if noBufferCache:
            with open('/proc/meminfo') as mem_open:
                T = int(mem_open.readline().split()[1])
                F = int(mem_open.readline().split()[1])
                B = int(mem_open.readline().split()[1])
                C = int(mem_open.readline().split()[1])
                return (F+B+C)/1024
        else:
            with open('/proc/meminfo') as mem_open:
                mem_open.readline()
                a = int(mem_open.readline().split()[1])
                return a / 1024
     
    def getHost(self):
        return ['host1', 'host2', 'host3', 'host4', 'host5'][int(time.time() * 1000.0) % 5] 
        #return socket.gethostname()
    def getTime(self):
        return int(time.time())
    
    def userDefineMon(self):
        """
        5min -> GET webapi 获取自定义监控项列表
            {"url":"脚本url","md5":"43214321","name":'eth_all'}
        -> check md5
            /home/work/agent/mon/user/$name/xxx.tgz
        -> xxx.tgz -> main -> chmod +x -> ./main
        -> output
            eth1:10
            eth2:20
            eth3:32
        -> return
            {"eth1":10,"eth2":20,"eth3":32}
        
        """
        data = {}
        global userDefine_check_time
        global userDefine_json
        if time.time() - userDefine_check_time > 300 or userDefine_json == []:
            url = 'http://reboot:50004/userdefine_listitem'
            try:
                userDefine_json = json.loads(urllib.urlopen(url).read())
                userDefine_check_time = time.time()
            except:
                userDefine_json = []
                return data
        print userDefine_json 
        for j in userDefine_json:
            data_url,md5,name = j['url'],j['md5'],j['name']
            print data_url,md5, name

            data_dir = '/home/work/agent/mon/user/'+name
            os.system('mkdir -p %s' % data_dir)
            print 'cd %s && md5sum xxx.tgz' % (data_dir)
            if md5 in os.popen('cd %s && md5sum xxx.tgz' % (data_dir)).read():
                pass
            else:
                urllib.urlretrieve(data_url, data_dir+'/'+'xxx.tgz')
            os.system('cd %s && tar zxf xxx.tgz' % data_dir)
            os.system('chmod +x %s/main' % data_dir)
            ret = os.popen('%s/main' % data_dir).read()
            for item in ret.split("\n"):
                if not item:
                    continue
                else:
                    key, val = item.split(":")
                    data["UD_"+key] = val
        return data

    def runAllGet(self):
        for fun in inspect.getmembers(self, predicate=inspect.ismethod):
            if fun[0] == "userDefineMon":
                self.data.update(fun[1]())
            elif fun[0][:3] == 'get':
                self.data[fun[0][3:]] = fun[1]()
        return self.data

if __name__ == "__main__":
    print mon().runAllGet()
