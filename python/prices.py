#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import re

from operators import dBOperator as db
from models import *
from utils import *
from config import *

class JDPrices(object):
  '''京东的商品价格查询，价格查询分为独立的任务进行'''
  def __init__(self):
    super().__init__()

  def crawl(self):
    '''获取商品的价格信息'''
    job_no = 0
    while True:
      goods_list = db
      job_no = job_no + 1
      (task_done, goods_list) = db.next_goods_page_to_handle_prices()
      if task_done:
        # 表示任务完成了
        break
      if len(goods_list) == 0:
        # 表示可能是数据加锁的时候失败了
        continue
      self.__crawl_basic_prices(goods_list)
    # 任务完成！！！*★,°*:.☆(￣▽￣)/$:*.°★* 。4
    logging.info("Goods Scrawl Job Finished!!!")

  def __crawl_prices(self, goods_list):
    '''批量爬取商品的价格信息'''
    self.__crawl_basic_prices(goods_list)
    for goods_item in goods_list:
      if goods_item[GOODS_PRICE_ROW_INDEX] != -1:
        # 过滤掉下架的商品
        self.__crawl_goods_discount(goods_item)

  def __crawl_basic_prices(self, goods_list):
    '''查询商品的基础价格信息，批量请求，用来检查商品是否已经被下架了'''
    ids = ''
    for idx in range(0, len(goods_list)):
      goods_item = goods_list[idx]
      skuid = goods_item[GOODS_SKU_ID_ROW_INDEX]
      ids = ids + skuid
      if len(goods_list)-1 != idx:
        ids = ids + ','
    prices_json = requests.get("https://p.3.cn/prices/mgets?skuIds=" + ids)
    prices = json.loads(prices_json)
    logging.debug(prices)
    for idx in range(0, len(prices)):
      price = prices[idx]
      price_value = price.get('p')
      if float(price) == -1.00:
        # 当价格为 -1 的时候，表示商品被下架了
        goods_list[idx][GOODS_PRICE_ROW_INDEX] = -1

  def __crawl_goods_discount(self):
    '''查询商品的折扣信息'''
    pass

  def test(self):
    '''测试入口'''
    self.crawl()

if __name__ == "__main__":
  '''测试入口'''
  config = GlobalConfig()
  config.config_logging()
  dt = JDPrices()
  dt.test()