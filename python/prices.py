#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import re
import time
import random
import traceback
from typing import *

from operators import dBOperator as db
from models import *
from utils import *
from config import *
from goods_operator import *

class JDPrices(object):
  '''京东的商品价格查询，价格查询分为独立的任务进行'''
  def __init__(self):
    super().__init__()
    self.page_size = 30
    self.max_fail_count = 50
    self.total_failed_count = 0

  def crawl(self, start_id_ = None):
    '''
    获取商品的价格信息，这个任务的作用是用来清理已经下架的商品，爬取的时间周期可以长一些
    接受参数 start_id_ 用来手动指定开始的 id，这样就可以从上次失败中进行恢复
    '''
    job_no = start_id = item_count = 0
    start_id = parse_number(start_id_, start_id)
    while True:
      goods_list = go.next_goods_page(SOURCE_JINGDONG, self.page_size, start_id)
      if len(goods_list) == 0: # 表示可能是数据加锁的时候失败了
        break
      item_count += len(goods_list)
      start_id = goods_list[len(goods_list)-1].id
      job_no += 1
      logging.info('>>>> Crawling Prices: job[%d], starter[%d], [%d] items done. <<<<' % (job_no, start_id, item_count))
      succeed = self._crawl_prices(goods_list)
      if not succeed:
        self.total_failed_count += 1
        if self.total_failed_count > self.max_fail_count:
          # 同时输出 start_id 便于下次从失败中恢复
          logging.error(">>>> Crawling Prices Job Stopped Due to Fatal Error: job[%d], starter[%d], [%d] items done. <<<<" % (job_no, start_id, item_count))
          send_email('京东价格爬虫【异常】报告', '[%d] jobs [%d] items done, starter: [%d]' % (job_no, item_count, start_id), config.log_filename)
          break
      # 休眠一定时间
      time.sleep(random.random() * CRAWL_SLEEP_TIME_INTERVAL)
    logging.info(">>>> Crawling Prices Job Finished: [%d] jobs [%d] items done. <<<<" % (job_no, item_count))
    send_email('京东价格爬虫【完成】报告', '[%d] jobs [%d] items done' % (job_no, item_count))

  def _crawl_prices(self, goods_list: List[GoodsItem]):
    '''批量爬取商品的价格信息，主要用来查找商品的下架状态，如果下架了，就将其标记为下架'''
    succeed = True
    try:
      soldout_list = self._crawl_basic_prices(goods_list)
      if len(soldout_list) != 0:
        succeed = go.update_goods_list_as_sold_out(soldout_list) # 更新到数据库
    except BaseException as e:
      logging.error("Eror while crawl prices:\n%s" % traceback.format_exc())
      succeed = False
    return succeed

  def _crawl_basic_prices(self, goods_list: List[GoodsItem]):
    '''查询商品的基础价格信息，批量请求，用来检查商品是否已经被下架了'''
    sku_ids = ','.join([str(goods_item.sku_id) for goods_item in goods_list])  
    prices_json = requests.get("http://p.3.cn/prices/mgets?skuIds=" + sku_ids, headers=get_request_headers()).text
    prices = json.loads(prices_json)
    soldout_list = [] # 已下架的商品列表
    for idx in range(0, len(prices)):
      price_value = prices[idx].get('p')
      if float(price_value) == -1.00:
        soldout_list.append(goods_list[idx])
    return soldout_list

  def test(self):
    '''测试入口'''
    self.crawl()

if __name__ == "__main__":
  '''测试入口'''
  config.config_logging()
  dt = JDPrices()
  dt.test()
