#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time, datetime

# 爬虫相关的配置
CRAWL_SLEEP_TIME_INTERVAL         = 10  # 爬虫的睡眠时间（秒）
CRAWL_SLEEP_TIME_MIDLLE           = 6   # 爬虫的中等长度的睡眠时间（秒）
CRAWL_SLEEP_TIME_SHORT            = 2   # 爬虫的较短长度的睡眠时间（秒）
JD_COMMENT_MAX_TRAY_COUNT         = 3   # 京东爬虫爬取评论的最大重试次数
JD_PAGE_MAX_FAIL_COUNT            = 15  # 京东爬取数据的时候最大的失败次数，达到了这个数字之后认定为存在严重的问题，需要停止程序
JD_MAX_SEARCH_PAGE                = 100    # 爬虫默认最大爬取的页数
CHANNEL_HANDLE_TIMEOUT_IN_MINUTE  = 2     # 分类处理的超时时间，超时完不成则认为失败
GOODS_HANDLE_TIMEOUT_IN_MINUTE    = 2     # 产品超时时间，同上
PRICES_HANDLE_TIMEOUT_IN_MINUTE   = 2
PRICES_HANDLE_PER_PAGE_SIZE       = 30
DISCOUNT_HANDLE_PER_PAGE_SIZE     = 10

# 分类的列索引
CHANNEL_ID_ROW_INDEX            = 0
CHANNEL_NAME_ROW_INDEX          = 1
CHANNEL_CAT_ROW_INDEX           = 3
CHANNEL_TREEPATH_ROW_INDEX      = 4
CHANNEL_JD_URL_ROW_INDEX        = 5
CHANNEL_MAXPAGE_ROW_INDEX       = 7
CHANNEL_LOCK_VERSION_ROW_INDEX  = 11
# 商品的列索引
GOODS_ID_ROW_INDEX              = 0
GOODS_LINK_ROW_INDEX            = 3
GOODS_PRICE_ROW_INDEX           = 5
GOODS_SKU_ID_ROW_INDEX          = 11
GOODS_VEN_ID_ROW_INDEX          = 13
GOODS_CHANNEL_ID_ROW_INDEX      = 22
GOODS_LOCK_VERSION_ROW_INDEX    = 25     # lock version
# 品牌的列索引
BRAND_ID_ROW_INDEX              = 0
BRAND_LINK_ROW_INDEX            = 4
# 折扣的列索引
DISCOUNT_BATCH_ID_ROW_INDEX     = 2

# 数据源配置，用来区分不同的来源的数据
SOURCE_JINGDONG                 = 0
SOURCE_TAOBAO                   = 1
SOURCE_TAMLL                    = 2

# 数据库字段的最大长度
MAX_LENGTH_OF_GOODS_PARAMETERS  = 2800
MAX_LENGTH_OF_GOODS_PACKAGES    = 2800

# Redis 相关的键信息
GOODS_PRICE_HISTORY_REDIS_KEY_PATTERN = "GOODS:PRICE:HISTORY:%d"  # 商品历史价格的 Redis 键的格式

# 处理的分类的文件位置
JD_CATEGORY_STORE = "../data/京东分类.xlsx"
TB_CATEGORY_STORE = "../data/淘宝分类.xlsx"
JD_HANDLED_CATEGORY_STORE = "../data/京东分类-处理.xlsx"

# 命令常量值
CMD_WRITE_JD_CATEGORY           = 'write_category'
CMD_CRAWL_JD_CATEGORY           = 'crawl_jd_category'
CMD_CRAWL_JD_GOODS              = 'crawl_jd_goods'
CMD_CRAWL_JD_DETAIL             = 'crawl_jd_detail'
CMD_CRAWL_JD_DISCOUNT           = 'crawl_jd_discount'
CMD_CRAWL_JD_PRICES             = 'crawl_jd_price_batch'

# 环境值常量
ENV_LOCAL                       = 'local'
ENV_TEST                        = 'test'
ENV_SERVER_LOCAL                = 'server_local'
ENV_SERVER_REMOTE               = 'server_remote'

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
    self.logLevel = logging.WARNING
    self.logAppendix = ''
    self.db = DBConfig()
    self.redis = RedisConfig()

  def config_logging(self):
    """配置应用日志"""
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
    filename = str(datetime.date.today()) + self.logAppendix + '.log'
    logging.basicConfig(filename=filename, filemode='a', level=self.logLevel, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.FileHandler(filename=filename, encoding='utf-8')

  def set_env(self, env: str):
    """设置环境信息"""
    if env == ENV_LOCAL:
      self.db.host = 'localhost'
      self.db.port = ***REMOVED***
      self.db.database = '***REMOVED***'
      self.db.user = 'root'
      self.db.password = '***REMOVED***'

      self.redis.host = 'localhost'
      self.redis.db = 0
      self.redis.password = ''
      self.redis.port = 6379
    elif env == ENV_TEST:
      self.db.host = 'localhost'
      self.db.port = ***REMOVED***
      self.db.database = 'shuma'
      self.db.user = 'root'
      self.db.password = '***REMOVED***'

      self.redis.host = 'localhost'
      self.redis.db = 0
      self.redis.password = '12345'
      self.redis.port = 6379
    elif env == ENV_SERVER_LOCAL:
      pass
    elif env == ENV_SERVER_REMOTE:
      pass
    else:
      logging.warning('Invalid Environment!')

class DBConfig(object):
  """数据库配置类"""
  def __init__(self):
    super().__init__()
    self.host = ''
    self.port = ***REMOVED***
    self.user = ''
    self.password = ''
    self.database = ''

class RedisConfig(object):
  """Redis 配置类"""
  def __init__(self):
    super().__init__()
    self.host = ''
    self.port = 6379
    self.db = 0
    self.password = ''

config = GlobalConfig()
