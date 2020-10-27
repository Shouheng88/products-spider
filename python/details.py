#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import re
import time
import random
from bs4 import BeautifulSoup
import traceback

from operators import dBOperator as db
from models import *
from utils import *
from config import *

class JDDetails(object):
  '''商品详情信息抓取，之前抓取的是基础信息，现在抓取详情信息
  商品的信息查询包含两个部分，分别是产品的详情信息页面以及产品的价格信息相关的请求
  两个可以同时放在一起来完成，这样更符合真实的应用请求的效果。'''
  def __init__(self):
    super().__init__()
    self.total_failed_count = 0

  def crawl(self):
    '''爬取商品的详情信息，设计的逻辑同商品的列表页面'''
    job_no = start_id = item_count = 0
    while True:
      goods_list = db.next_page_to_handle_prameters(SOURCE_JINGDONG, PARAMETERS_HANDLE_PER_PAGE_SIZE, start_id)
      if len(goods_list) == 0: # 表示没有需要爬取参数的任务了
        break
      item_count = item_count + len(goods_list)
      start_id = goods_list[len(goods_list)-1][GOODS_ID_ROW_INDEX]
      job_no = job_no + 1
      logging.info(">>>> Crawling Goods Details: job[%d], starter[%d], [%d] items done. <<<<" % (job_no, start_id, item_count))
      succeed = self.__crawl_goods_items(goods_list) # 爬取某个商品的条目
      if not succeed:
        logging.error(">>>> Crawling Goods Details Stopped Due to Fatal Error: job[%d], starter[%d], [%d] items done. <<<<" % (job_no, start_id, item_count))
        send_email('京东详情爬虫【异常】报告', '[%d] jobs [%d] items done, starter: [%d]' % (job_no, item_count, start_id), config.log_filename)
        return
      time.sleep(random.random() * CRAWL_SLEEP_TIME_INTERVAL) # 休眠一定时间
    logging.info(">>>> Crawling Details Job Finished: [%d] jobs, [%d] items done. <<<" % (job_no, item_count))
    send_email('京东详情爬虫【完成】报告', '[%d] jobs [%d] items done' % (job_no, item_count))

  def __crawl_goods_items(self, goods_list):
    '''爬取商品的信息'''
    for goods_item in goods_list:
      try:
        (goods_params, html) = self.__crawl_from_page(goods_item)
        succeed = db.update_goods_parames(goods_item, goods_params) # 更新到数据库当中
        if not succeed:
          raise Exception('Nothing parsed!')
      except BaseException as e:
        self.total_failed_count = self.total_failed_count+1
        if self.total_failed_count > JD_DETAIL_MAX_FAILE_COUNT:
          return False
        logging.error('Error while crawling goods details:\n%s' % traceback.format_exc())
        time.sleep(random.random()*CRAWL_SLEEP_TIME_SHORT) # 小憩一会儿
    return True

  def __crawl_from_page(self, goods_item):
    '''从商品的详情信息页面中提取商品的详情信息'''
    goods_link = 'https:' + goods_item[GOODS_LINK_ROW_INDEX]
    html = requests.get(goods_link, headers=get_request_headers()).text
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
    return (goods_params, html)

  def test(self):
    '''测试入口'''
    # 如果数据库的字段发生了变化这里的参数要相应的改变哦~
    self.__crawl_goods_items([(106, 0, 0, '//item.jd.com/56765001552.html', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6)])

if __name__ == "__main__":
  '''测试入口'''
  config.logLevel = logging.DEBUG
  config.config_logging()
  dt = JDDetails()
  dt.test()
