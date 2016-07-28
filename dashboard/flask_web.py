#!/usr/bin/env python
#encoding:utf8
import json
import time,random
import datetime
import MySQLdb
from flask import Flask, request
from flask import render_template
import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
#from controller.client import *
#from nbNet.nbNet import sendData
from dbutil.dbutil import DB


db = DB(host="localhost", mysql_user="fable", mysql_pass="fableAdmin", \
                mysql_db="fable")

app = Flask(__name__)

monTables = [
    'stat_0',
    'stat_1',
    'stat_2',
    'stat_3',
]

def fnvhash(string):
    ret = 97
    for i in string:
        ret = ret ^ ord(i) * 13
    return ret 


@app.route("/userdefine_listitem", methods=["GET"])
def listitem():
    j = [{"url":"http://fable:50004/static/testUserDefine/xxx.tgz","md5":"3483e6bbab5fa7f56f76caa531ae265a","name":'eth_all'}]
    return json.dumps(j)

@app.route("/listhost", methods=["GET"])
def listhost():
    hostl = set()
    for t in monTables:
        sql = "SELECT distinct(`host`) FROM `%s`;" % (t)
        c = db.execute(sql)
        ones = c.fetchall()
        for one in ones:
            hostl.add(one[0])
    return json.dumps(list(set(hostl)))

@app.route("/", methods=["GET"])
def index():
    hostname = request.args.get("host")
    item = request.args.get("item")
  #  mIteml = []
    sql = "show columns from stat_2;"
    print sql
    c = db.execute(sql)
    columns = c.fetchall()
    columns = list(columns)
    columns = [i[0] for i in columns]
    columns.remove('id')
    columns.remove('host')
    columns.remove('time')
    columns.remove('user_define')
    try:
        c = db.execute("SELECT `user_define` FROM falcon.stat_2 order by `time` desc limit 1")
        columns.extend(json.loads(c.fetchall()[0][0]).keys())
    except:
        pass

    print columns 
    hostl = set()
    for t in monTables:
        sql = "SELECT distinct(`host`) FROM `%s`;" % (t)
        c = db.execute(sql)
        ones = c.fetchall()
        for one in ones:
            hostl.add(one[0])
    return render_template("index.html", hosts = hostl, selected_host = hostname,items = columns,selected_item = item)

@app.route("/getdata", methods=["GET", "POST"])
def getdata():
    """
    http://fable:50004/getdata?host=host1&item=UD_eth11&from=2015-07-19%2015:47:32&to=&callback=jQuery18303697302439250052_1437291543987&_=1437292056435

    return:
    jQuery183045716429501771927_1435477247087(
    [
        [1147651200000,67.79],
        [1147737600000,64.98],
        [1147824000000,65.26],
        [1147910400000,63.18]
    ]);
    """
    host = request.args.get('host')
    item = request.args.get('item')
    t = int(time.time())
    f = t - 3600
    timetemplate = "%Y-%m-%d %H:%M:%S"
    try:
        t = time.mktime(datetime.datetime.strptime(request.args.get('to'), timetemplate).timetuple())
        f = time.mktime(datetime.datetime.strptime(request.args.get('from'), timetemplate).timetuple())
    except:
        pass
    print t, f 
    start_time = f
    end_time   = t
    callback   = request.args.get('callback')

    print start_time, end_time, callback
    mTable = monTables[fnvhash(host) % len(monTables)]
    if item[:3] == "UD_":
        sql = "SELECT `time`*1000,`user_define` FROM `%s` WHERE host = '%s' AND `time` BETWEEN '%d' AND '%d';" % (mTable,host,int(start_time),int(end_time))
    else:
        sql = "SELECT `time`*1000,`%s` FROM `%s` WHERE host = '%s' AND `time` BETWEEN '%d' AND '%d';" % (item,mTable,host,int(start_time),int(end_time))
    print sql 
    c = db.execute(sql)
    data = c.fetchall()
    if item[:3] == "UD_":
        data = [[d[0], float(json.loads(d[1])[item])] for d in data]
    else:
        data = [[d[0], float(d[1])] for d in data]
    data = json.dumps(data)
    return_data = '%s(%s);' % (callback,data)
    return return_data 


@app.route("/show", methods=["GET", "POST"])
def show():
    host = request.args.get("host")
    item = request.args.get("item")
    t = int(time.time())
    f = t - 3600
    timetemplate = "%Y-%m-%d %H:%M:%S"
    try:
        t = time.mktime(datetime.datetime.strptime(request.args.get('to'), timetemplate).timetuple())
        f = time.mktime(datetime.datetime.strptime(request.args.get('from'), timetemplate).timetuple())
    except:
        pass
    print t, f 
    
    #mTable = monTables[fnvhash(host) % len(monTables)]
    #sql = "SELECT `%s` FROM `%s` WHERE host = '%s' AND `time` BETWEEN '%d' AND '%d';" % (item,mTable,host,f,t)
    #print sql
    #c = db.execute(sql)
    #ones = c.fetchall()

    return render_template("sysstatus.html", host = host, item = item, f = int(f), t = int(t) )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=50004, debug=True)


