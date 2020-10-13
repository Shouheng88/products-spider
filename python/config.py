#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

CRAWL_SLEEP_TIME_INTERVAL = 1500      # 爬虫的睡眠时间

JD_MAX_SEARCH_PAGE = 30

# 分类的列信息，对应的数据库字段的索引
CHANNEL_ID_ROW_INDEX = 0
CHANNEL_TREEPATH_ROW_INDEX = 3
CHANNEL_JD_URL_ROW_INDEX = 4
CHANNEL_LOCK_VERSION_ROW_INDEX = 10

JD_CATEGORY_STORE = "../data/京东分类.xlsx"
TB_CATEGORY_STORE = "../data/淘宝分类.xlsx"
JD_HANDLED_CATEGORY_STORE = "../data/京东分类-处理.xlsx"

class GlobalConfig(object):
  def __init__(self):
    super().__init__()

  # 配置日志
  def config_logging(self):
      """配置应用日志"""
      LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
      DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
      logging.basicConfig(filename='app.log', filemode='a', level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)
      logging.FileHandler(filename='app.log', encoding='utf-8')
