#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

CRAWL_SLEEP_TIME_INTERVAL = 1500      # 爬虫的睡眠时间

JD_MAX_SEARCH_PAGE = 30

CHANNEL_ID_ROW_INDEX = 0              # 分类的列信息，对应的数据库字段的索引
CHANNEL_NAME_ROW_INDEX = 1
CHANNEL_TREEPATH_ROW_INDEX = 3
CHANNEL_JD_URL_ROW_INDEX = 4
CHANNEL_LOCK_VERSION_ROW_INDEX = 10

GOODS_ID_ROW_INDEX = 0                # 商品的列信息，对应的数据库字段的索引
GOODS_LINK_ROW_INDEX = 3

JD_CATEGORY_STORE = "../data/京东分类.xlsx"
TB_CATEGORY_STORE = "../data/淘宝分类.xlsx"
JD_HANDLED_CATEGORY_STORE = "../data/京东分类-处理.xlsx"

REQUEST_HEADERS = {
      "Accept" : "application/jason, text/javascript, */*; q = 0.01",
      "X-Request-With" : "XMLHttpRequest",
      "User-Agent":"Mozilla/5.0 (Windows NT 10.0; ...) Gecko/20100101 Firefox/60.0",
      "Content-Type" : "application/x-www-form-urlencode:chartset=UTF-8"
    }

class GlobalConfig(object):
  '''全局的配置类，用来区分开发、测试和生产等环境'''
  def __init__(self):
    super().__init__()

  def config_logging(self):
      """配置应用日志"""
      LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
      DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
      logging.basicConfig(filename='app.log', filemode='a', level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)
      logging.FileHandler(filename='app.log', encoding='utf-8')
