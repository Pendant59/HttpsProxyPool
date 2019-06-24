import time
import asyncio
import aiohttp
import json
import random
import requests
from db import RedisClient
from getdata import GetProxiesData
from functions import set_log_zh_bytime
from config import *
from bloomfilter import BloomFilter


class DoCheck():
	""" 检查 """
	def __init__(self):
		self._db = RedisClient()
		self._bf = BloomFilter()
		
	def DoCheck(self, proxyList=''):
		''' 校验代理 '''
		
		waitForCheckList = proxyList
		for proxy in waitForCheckList:
			proxies = eval(proxy.decode('utf-8'))  # dict 格式的str,由eval 转化成dict
			try:
				r = requests.get(TEST_API, proxies=proxies, timeout=3)
				if r.status_code == 200:
					self._db.addProxy(proxy.decode('utf-8'))  # str
					# print('---Userfull : ' + proxy.decode('utf-8'))
			except Exception as e:
				# print(proxies)
				continue

class DoGrab():
	""" 抓取入库 """
	def __init__(self):
		self._db = RedisClient()
		self._get = GetProxiesData()
		self._check = DoCheck()
		self._bf = BloomFilter()

	def DoGrab(self):
		''' 抓取 '''
		for index in range(self._get.funcnum):
			proxyList = eval('self._get.{}()'.format(self._get.funclist[index]))
			if proxyList:
				for proxy in proxyList:
					if USE_BLOOMFILTER:
						if not self._bf.isContains(proxy):
							self._db.addProxy(proxy)
							self._bf.insert(proxy)
					else:
						self._db.addProxy(proxy)
			

class Main():
	""" 主控制器类 """

	# 抓取代理
	_grab = DoGrab()
	# 检查代理
	_check = DoCheck()
	# redis
	_db = RedisClient()

	@staticmethod
	def CheckProxies():
		'''Check whether agents are available'''
		while True:
			Main._db._db.set('Proxy:Check', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
			if Main._db.getProxyLength <= POOL_CRITICAL_NUMBER:
				if USE_BLOOMFILTER:
					Main._check._bf.resetBloomFilter()
					Main._db._db.set('Proxy:ResetBf', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
			waitForCheckList = Main._db.validateProxiesList()
			if waitForCheckList:
				Main._check.DoCheck(waitForCheckList)
			time.sleep(VALID_PROXY_CYCLE)

	@staticmethod
	def GrabProxies():
		'''Grabbing proxies'''
		while True:
			Main._db._db.set('Proxy:Get', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
			Main._grab.DoGrab()
			time.sleep(POOL_MAX_LEN_CHECK_CYCLE)

			
			

if __name__ == '__main__':
	pass
	# Main.GrabProxies()
	# Main.CheckProxies()
