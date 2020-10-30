#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import re
import time
import random
from bs4 import BeautifulSoup
import traceback
from typing import *

from operators import redisOperator as redis
from operators import dBOperator as db
from models import *
from utils import *
from config import *
from goods_operator import *

class JDDetails(object):
  '''商品详情信息抓取，之前抓取的是基础信息，现在抓取详情信息
  商品的信息查询包含两个部分，分别是产品的详情信息页面以及产品的价格信息相关的请求
  两个可以同时放在一起来完成，这样更符合真实的应用请求的效果。'''
  def __init__(self):
    super().__init__()
    self.task_name = 'JD:DETAIL'
    self.page_size = 5
    self.max_faile_count = 50
    self.total_failed_count = 0
    self.group_count = 50 # 将所有的产品分成 30 组，每天爬取 1 组，大概 2000 条
    # self.ua = []

  def crawl(self):
    '''爬取商品的详情信息，设计的逻辑同商品的列表页面'''
    job_no = start_id = item_count = 0
    cursor = redis.get_cursor_of_task(self.task_name, 1)
    type_index = cursor % self.group_count
    while True:
      goods_list = go.next_page_to_handle_prameters(SOURCE_JINGDONG, self.page_size, start_id, type_index, self.group_count)
      if len(goods_list) == 0: # 表示没有需要爬取参数的任务了
        break
      item_count += len(goods_list)
      start_id = goods_list[len(goods_list)-1].id
      job_no += 1
      logging.info(">>>> Crawling Goods Details: job[%d], starter[%d], index[%d], [%d] items done. <<<<" % (job_no, start_id, type_index, item_count))
      succeed = self.__crawl_goods_items(goods_list) # 爬取某个商品的条目
      if not succeed:
        logging.error(">>>> Crawling Goods Details Stopped Due to Fatal Error: job[%d], starter[%d], index[%d], [%d] items done. <<<<" % (job_no, start_id, type_index, item_count))
        send_email('京东详情爬虫【异常】报告', '[%d] jobs [%d] items done, starter [%d], index [%d], ua left [%d]'\
          % (job_no, item_count, start_id, type_index, len(DETAIL_USER_AGENTS)), config.log_filename)
        return
      time.sleep(random.random() * CRAWL_SLEEP_TIME_INTERVAL) # 休眠一定时间
    logging.info(">>>> Crawling Details Job Finished: [%d] jobs, [%d] items done, index [%d]. <<<" % (job_no, item_count, type_index))
    send_email('京东详情爬虫【完成】报告', '[%d] jobs [%d] items done, index [%d]' % (job_no, item_count, type_index))
    redis.mark_task_as_done(self.task_name, cursor)

  def __crawl_goods_items(self, goods_list: List[GoodsItem]):
    '''爬取商品的信息'''
    for goods_item in goods_list:
      try:
        (goods_params, html, headers) = self.__crawl_from_page(goods_item)
        succeed = go.update_goods_prameters(goods_item, goods_params) # 更新到数据库当中
        time.sleep(random.random()*CRAWL_SLEEP_TIME_MIDLLE)
        if not succeed:
          raise Exception('Nothing parsed!')
        # else:
          # self.ua.append(headers.get('User-Agent'))
          # logging.debug("VALID UA: " + str(self.ua)) # 对随机的 ua 做测试
      except BaseException as e:
        self.total_failed_count += 1
        if self.total_failed_count > self.max_faile_count:
          return False
        # 把无效的 ua 从列表中剔除
        ua = headers.get('User-Agent')
        DETAIL_USER_AGENTS.remove(ua)
        logging.debug("UA LEFT %d" % len(DETAIL_USER_AGENTS))
        if len(DETAIL_USER_AGENTS) == 0:
          return False
        logging.error('Error while crawling goods details:\n%s' % traceback.format_exc())
        logging.error("HEADER:%s" % headers)
        logging.debug('HTML:%s' % html)
        time.sleep(random.random()*CRAWL_SLEEP_TIME_MIDLLE) # 小憩一会儿
    return True

  def __crawl_from_page(self, goods_item: GoodsItem):
    '''从商品的详情信息页面中提取商品的详情信息'''
    headers = get_detail_request_headers()
    html = requests.get('https:' + goods_item.link, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    goods_params = GoodsParams()
    # 解析产品参数信息
    params_parents = soup.find_all(class_="p-parameter-list")
    for params_parent in params_parents: # 参数列表
      params_list = params_parent.find_all("li")
      is_brand_ul = False # 品牌参数
      if safeGetAttr(params_parent, 'id', '') == 'parameter-brand':
        is_brand_ul = True
      if params_list != None:
        for params_item in params_list:
          if is_brand_ul: # 解析品牌信息
            goods_params.brand = safeGetAttr(params_item, 'title', '')
            goods_params.brand_url = safeGetAttr(params_item.find('a'), 'href', '')
          else: # 解析其他参数信息
            params_text = safeGetText(params_item, '')
            parts = params_text.split('：')
            if len(parts) > 1:
              name = parts[0].strip()
              value = parts[1].strip()
            goods_params.parameters[name] = value
    # 解析产品包装信息
    package_groups = soup.find_all(class_="Ptable-item")
    for package_group in package_groups:
      group_name = safeGetText(package_group.find('h3'), '')
      group_elements = package_group.find_all(class_="clearfix")
      packages = {}
      for group_element in group_elements:
        item_name = safeGetText(group_element.find('dt'), '').strip()
        item_value = safeGetText(group_element.find('dd'), '').strip()
        packages[item_name] = item_value
      goods_params.packages[group_name] = packages
    # 解析产品的店铺信息
    e_popbox = soup.find(id='popbox')
    if e_popbox != None:
      goods_params.store = safeGetText(e_popbox.find('a'), '')
      goods_params.store_url = safeGetAttr(e_popbox.find('a'), 'href', '')
    else:
      e_contact = soup.select_one('.contact .name a')
      goods_params.store = safeGetText(e_contact, '')
      goods_params.store_url = safeGetAttr(e_contact, 'href', '')
    return (goods_params, html, headers)

  def test(self):
    '''测试入口'''
    # 如果数据库的字段发生了变化这里的参数要相应的改变哦~
    redis.mark_task_as_done(self.task_name, 5)
    redis.mark_task_as_done(self.task_name, 6)
    redis.mark_task_as_done(self.task_name, 7)
    redis.mark_task_as_done(self.task_name, 8)

if __name__ == "__main__":
  '''测试入口'''
  config.logLevel = logging.DEBUG
  config.config_logging()
  config.set_env(ENV_LOCAL)
  dt = JDDetails()
  dt.test()
