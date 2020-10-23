#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time, datetime
import random

from utils import *

# 爬虫相关的配置
# 时间配置
CRAWL_SLEEP_TIME_INTERVAL         = 20  # 爬虫的睡眠时间（秒），会使用 random 进行计算，平均时间是一般
CRAWL_SLEEP_TIME_MIDLLE           = 14   # 爬虫的中等长度的睡眠时间（秒）
CRAWL_SLEEP_TIME_SHORT            = 7   # 爬虫的较短长度的睡眠时间（秒）
CRAWL_SLEEP_TIME_LONG             = 30*60
# 重试配置
JD_COMMENT_MAX_TRAY_COUNT         = 3   # 京东爬虫爬取评论的最大重试次数
# 最大失败次数
JD_PAGE_MAX_FAIL_COUNT            = 15  # 京东爬取数据的时候最大的失败次数，达到了这个数字之后认定为存在严重的问题，需要停止程序
JD_DETAIL_MAX_FAILE_COUNT         = 50  # 抓取京东详情页面的最大失败次数
JD_PRICE_MAX_FAILE_COUNT          = 50  # 爬取价格的时候允许的最大的失败次数
JD_DISCOUNT_MAX_FAILE_COUNT       = 50  # 爬取折扣的时候允许的最大的失败次数
JD_MAX_SEARCH_PAGE                = 100    # 爬虫默认最大爬取的页数
# 时间配置
CHANNEL_HANDLE_TIMEOUT_IN_MINUTE  = 2     # 分类处理的超时时间，超时完不成则认为失败
GOODS_HANDLE_TIMEOUT_IN_MINUTE    = 2     # 产品超时时间，同上
PRICES_HANDLE_TIMEOUT_IN_MINUTE   = 2
# 页数配置
PRICES_HANDLE_PER_PAGE_SIZE       = 30
DISCOUNT_HANDLE_PER_PAGE_SIZE     = 5
PARAMETERS_HANDLE_PER_PAGE_SIZE   = 5

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
CMD_CRAWL_JD_PRICES             = 'crawl_jd_prices'

# 环境值常量
ENV_LOCAL                       = 'local'
ENV_TEST                        = 'test'
ENV_SERVER_LOCAL                = 'server_local'
ENV_SERVER_REMOTE               = 'server_remote'

# 请求头
ALL_REQUEST_HEADERS = [
  # "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    # "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
    # "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; InfoPath.3; rv:11.0) like Gecko",
    # "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    # "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
    # "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
    # "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
    # "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
    # "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    # "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)",
    # "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
    # "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
    # "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
    # "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)",
    # "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
    # "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
    # "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
    "MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
    "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
    "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13",
    "Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+",
    "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
    "Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)",
    "UCWEB7.0.2.37/28/999",
    "NOKIA5700/ UCWEB7.0.2.37/28/999",
    "Openwave/ UCWEB7.0.2.37/28/999",
    "Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999",
    # iPhone 6：
    "Mozilla/6.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/8.0 Mobile/10A5376e Safari/8536.25",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36",
    "ozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51",
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
  ]

REQUEST_HEADERS = {
      "Accept" : "application/jason, text/javascript, */*; q = 0.01",
      "X-Request-With" : "XMLHttpRequest",
      "User-Agent": random_useragent(),
      "Content-Type" : "application/x-www-form-urlencode:chartset=UTF-8"
    }

DISCOUNT_FILTER_LIKES = ('-', '减', '券')

DISCOUNT_AREAS = ['12_904_3373_0', '15_1213_1214_52674', '15_1273_1275_22204', '15_1262_1267_56327',
  '15_1158_1224_46479', '15_1250_1251_44548', '15_1255_15944_44627', '15_1255_15944_59428']

DISCOUNT_AREA = random.choice(DISCOUNT_AREAS)

class GlobalConfig(object):
  '''全局的配置类，用来区分开发、测试和生产等环境'''
  def __init__(self):
    super().__init__()
    self.logLevel = logging.WARNING
    self.logAppendix = ''
    self.db = DBConfig()
    self.redis = RedisConfig()
    self.log_filename = None

  def config_logging(self):
    """配置应用日志"""
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
    self.log_filename = str(datetime.date.today()) + self.logAppendix + '.log'
    logging.basicConfig(filename=self.log_filename, filemode='a', level=self.logLevel, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.FileHandler(filename=self.log_filename, encoding='utf-8')

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
