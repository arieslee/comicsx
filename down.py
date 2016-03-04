#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2016/3/4 10:23
# @Author  : Aries (i@iw3c.com)
# @Site    : http://iw3c.com
# @File    : download.py
# @Software: PyCharm

import os,json,sys,getopt
import time
import Queue,threading
from bs4 import BeautifulSoup
import requests
try:
	opts, args = getopt.getopt(sys.argv[1:], 'd:')
except getopt.GetoptError, err:
	print str(err)
	exit()
BASE_DIR = 'xieemanhua'
for k,v in opts:
    if k == '-d':
        BASE_DIR = v

BASE_URL = 'http://m.wujiecao.cn'
SAVE_DIR = 'datas/'+BASE_DIR
THREAD_COUNT = 5
#获取HTML内容
def getHtml(url,timeout=20):
    try:
        headers = {
            'Accept-Language': 'zh-cn',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/4.0 (compatible MSIE 6.00 Windows NT 5.1 SV1)',
        }
        r = requests.get(url,headers=headers,timeout=timeout)
        r.encoding='utf-8'
        html = r.text
        return html
    except Exception,ex:
        return False
#采集列表页
def getAllPageLists():
    print "=====start get all page lists====== %s" % time.ctime()
    soup = BeautifulSoup(getHtml(BASE_URL+'/'+BASE_DIR))
    select = soup.find('select', class_='paging-select')
    option = select.find_all('option')
    lists = []
    for o in option:
        lists.append(BASE_URL+'/'+BASE_DIR+'/'+o['value'])
    return lists
#采集每一页的列表
def getSingePageUrlLists(url):
    print "=====start getSingePageUrlLists("+os.path.basename(url)+") ====== %s" % time.ctime()
    soup = BeautifulSoup(getHtml(url))
    ul=soup.find("ul", class_="pic")
    all_a=ul.find_all('a')
    datas = []
    for a in all_a:
        img = a.find('img')
        span=a.find('span',class_="bt")
        title = span.contents[0]
        data = {'url':BASE_URL+a['href'],'title':title,'pic':BASE_URL+img['lazysrc']}
        datas.append(data)
    return datas
#采集详细页
def getDetailPage(url,title):
    print "=====start getDetailPage("+os.path.basename(url)+") ====== %s" % time.ctime()
    soup = BeautifulSoup(getHtml(url))
    div = soup.find('div',id="imgString")
    img = div.find('img')
    imgUrl = img['src']
    if imgUrl == '':
        return False
    response = requests.get(imgUrl, stream=True)
    if response.status_code != 200:
        return False
    image = response.content
    dir = SAVE_DIR
    if not os.path.exists(dir):
        os.mkdir(dir)
    baseName = os.path.basename(img['src']);
    fileName = dir+'/'+title+'.'+baseName.split('.')[1]
    try:
        open(fileName ,"wb").write(image)
        print "=====write end====== %s" % time.ctime()
    except IOError:
        print("IO Error\n")
        return

class getLists(threading.Thread):
    def __init__(self ,que,detailQue):
        threading.Thread.__init__(self)
        self.pageQue = que
        self.detailQue = detailQue
    def run(self):
        while True:
            url = self.pageQue.get()
            singePageLists = getSingePageUrlLists(url)
            for sl in singePageLists:
                self.detailQue.put(json.dumps(sl))
            self.pageQue.task_done()

class getDetailLists(threading.Thread):
    def __init__(self ,detailQue):
        threading.Thread.__init__(self)
        self.detailQue = detailQue
    def run(self):
        while True:
            data = self.detailQue.get()
            decodeData = json.loads(data)
            getDetailPage(decodeData['url'],decodeData['title'])
            self.detailQue.task_done()

pageQue = Queue.Queue()
detailQue = Queue.Queue()
if __name__ == '__main__':
    print "====start request====%s" % time.ctime()
    allLists = getAllPageLists()
    for u in allLists:
        pageQue.put(u)
    for t in range(THREAD_COUNT):
        t = getLists(pageQue,detailQue)
        t.setDaemon(True)
        t.start()

    for t in range(THREAD_COUNT):
        t = getDetailLists(detailQue)
        t.setDaemon(True)
        t.start()

    pageQue.join()
    detailQue.join()
    print 'all DONE at:', time.ctime()