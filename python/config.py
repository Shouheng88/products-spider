#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

# 爬虫相关的配置
CRAWL_SLEEP_TIME_INTERVAL         = 1500  # 爬虫的睡眠时间（毫秒）
JD_MAX_SEARCH_PAGE                = 100    # 爬虫默认最大爬取的页数
CHANNEL_HANDLE_TIMEOUT_IN_MINUTE  = 2     # 分类处理的超时时间，超时完不成则认为失败
GOODS_HANDLE_TIMEOUT_IN_MINUTE    = 2     # 产品超时时间，同上
PRICES_HANDLE_TIMEOUT_IN_MINUTE   = 2
PRICES_HANDLE_PER_PAGE_SIZE       = 30

# 分类的列索引
CHANNEL_ID_ROW_INDEX            = 0
CHANNEL_NAME_ROW_INDEX          = 1
CHANNEL_TREEPATH_ROW_INDEX      = 3
CHANNEL_JD_URL_ROW_INDEX        = 4
CHANNEL_LOCK_VERSION_ROW_INDEX  = 10
# 商品的列索引
GOODS_ID_ROW_INDEX              = 0
GOODS_PRICE_ROW_INDEX           = 5
GOODS_LINK_ROW_INDEX            = 3
GOODS_SKU_ID_ROW_INDEX          = 10
GOODS_LOCK_VERSION_ROW_INDEX    = 24     # lock version
# 品牌的列索引
BRAND_ID_ROW_INDEX              = 0
BRAND_LINK_ROW_INDEX            = 4 

# Redis 相关的键信息
GOODS_PRICE_HISTORY_REDIS_KEY_PATTERN = "GOODS:PRICE:HISTORY:%d"  # 商品历史价格的 Redis 键的格式

# 处理的分类的文件位置
JD_CATEGORY_STORE = "../data/京东分类.xlsx"
TB_CATEGORY_STORE = "../data/淘宝分类.xlsx"
JD_HANDLED_CATEGORY_STORE = "../data/京东分类-处理.xlsx"

# 请求头
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
