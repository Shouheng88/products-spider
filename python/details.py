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

  def crawl(self):
    '''爬取商品的详情信息，设计的逻辑同商品的列表页面'''
    job_no = 0 # 编号
    while True:
      goods_item = db.next_goods_to_handle_prameters(SOURCE_JINGDONG)
      if goods_item == None:
        break
      job_no = job_no + 1
      goods_id = goods_item[GOODS_ID_ROW_INDEX]
      logging.info(">>>> Crawling Goods Details: job[%d] goods[%d] <<<<" % (job_no, goods_id))
      self.__crawl_goods_item(goods_item) # 爬取某个商品的条目
      time.sleep(random.random() * CRAWL_SLEEP_TIME_MIDLLE) # 休眠一定时间
    logging.info(">>>> Crawling Goods Details Job Finished: [%d] channels done <<<" % job_no)

  def __crawl_goods_item(self, goods_item):
    '''爬取商品的信息'''
    try:
      goods_params = self.__crawl_from_page(goods_item)
      # 更新到数据库当中
      db.update_goods_parames_and_mark_done(goods_item, goods_params)
    except BaseException as e:
      logging.error('Error while crawling goods details:\n%s' % traceback.format_exc())

  def __crawl_from_page(self, goods_item):
    '''从商品的详情信息页面中提取商品的详情信息'''
    goods_link = 'https:' + goods_item[GOODS_LINK_ROW_INDEX]
    html = requests.get(goods_link, headers=REQUEST_HEADERS).text
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
    goods_params.store = safeGetText(soup.find(id='popbox').find('a'), '')
    goods_params.store_url = safeGetAttr(soup.find(id='popbox').find('a'), 'href', '')
    return goods_params

  def test(self):
    '''测试入口'''
    # 如果数据库的字段发生了变化这里的参数要相应的改变哦~
    self.__crawl_goods_item((106, 0, 0, 'https://item.jd.com/100000695409.html', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6))

if __name__ == "__main__":
  '''测试入口'''
  config.config_logging()
  dt = JDDetails()
  dt.test()
