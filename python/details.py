#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import re
from bs4 import BeautifulSoup
import traceback

from operators import dBOperator as db
from models import GoodsParams
from utils import safeGetAttr
from utils import safeGetText
from config import GlobalConfig as Config
from config import REQUEST_HEADERS
from config import GOODS_LINK_ROW_INDEX
from config import GOODS_ID_ROW_INDEX

class JDDetails(object):
  '''商品详情信息抓取，之前抓取的是基础信息，现在抓取详情信息
  商品的信息查询包含两个部分，分别是产品的详情信息页面以及产品的价格信息相关的请求
  两个可以同时放在一起来完成，这样更符合真实的应用请求的效果。'''
  def __init__(self):
    super().__init__()

  def crawl(self):
    '''爬取商品的详情信息，设计的逻辑同商品的列表页面'''
    job_no = 0
    while True:
      goods_item = db.next_item_to_handle()
      if goods_item == None:
        break
      job_no = job_no + 1
      logging.info("Crawling Goods (%d): %s" % (job_no, str(goods_item)))
      # 爬取一条数据
      self.__crawl_goods_item(goods_item)
    # 任务完成！！！*★,°*:.☆(￣▽￣)/$:*.°★* 。4
    logging.info("Goods Scrawl Job Finished!!!")

  def __crawl_goods_item(self, goods_item):
    '''爬取商品的信息'''
    goods_params = self.__crawl_from_page(goods_item)
    self.__crawl_from_request(goods_item)
    # 更新到数据库当中
    db.update_goods_parames_and_mark_done(goods_item, goods_params)

  def __crawl_from_request(self, goods_item):
    '''使用请求的链接来获取商品的详情信息'''
    pass

  def __crawl_from_page(self, goods_item):
    '''从商品的详情信息页面中提取商品的详情信息'''
    goods_link = goods_item[GOODS_LINK_ROW_INDEX]
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
              name = parts[0]
              value = parts[1]
            goods_params.parameters.append((name, value))
    # 解析产品包装信息
    package_groups = soup.find_all(class_="Ptable-item")
    for package_group in package_groups:
      group_name = safeGetText(package_group.find('h3'), '')
      group_elements = package_group.find_all(class_="clearfix")
      packages = []
      for group_element in group_elements:
        item_name = safeGetText(group_element.find('dt'), '')
        item_value = safeGetText(group_element.find('dd'), '')
        packages.append((item_name, item_value))
      goods_params.packages[group_name] = packages
    # 解析产品的店铺信息
    goods_params.store = safeGetText(soup.find(id='popbox').find('a'), '')
    goods_params.store_url = safeGetAttr(soup.find(id='popbox').find('a'), 'href', '')
    return goods_params

  def test(self):
    '''测试入口'''
    self.__crawl_goods_item((66, 0, 0, 'https://item.jd.com/55690316532.html', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

if __name__ == "__main__":
  '''测试入口'''
  config = Config()
  config.config_logging()
  dt = JDDetails()
  dt.test()
