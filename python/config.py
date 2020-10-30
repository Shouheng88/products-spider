#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time, datetime
import random

from utils import *

# 爬虫相关的配置
# 时间配置
CRAWL_SLEEP_TIME_INTERVAL         = 30  # 爬虫的睡眠时间（秒），会使用 random 进行计算，平均时间是一般
CRAWL_SLEEP_TIME_MIDLLE           = 15   # 爬虫的中等长度的睡眠时间（秒）
CRAWL_SLEEP_TIME_SHORT            = 7   # 爬虫的较短长度的睡眠时间（秒）
CRAWL_SLEEP_TIME_LONG             = 10*60
# 时间配置
CHANNEL_HANDLE_TIMEOUT_IN_MINUTE  = 2     # 分类处理的超时时间，超时完不成则认为失败
GOODS_HANDLE_TIMEOUT_IN_MINUTE    = 2     # 产品超时时间，同上
PRICES_HANDLE_TIMEOUT_IN_MINUTE   = 2

# 数据源配置，用来区分不同的来源的数据
SOURCE_JINGDONG                 = 0
SOURCE_TAOBAO                   = 1
SOURCE_TAMLL                    = 2

# 数据库字段的最大长度
MAX_LENGTH_OF_GOODS_PARAMETERS  = 2800
MAX_LENGTH_OF_GOODS_PACKAGES    = 2800

# 命令常量值
# 0 4 * * * sh /home/box_admin_wsh/.tools/mysql_backup.sh
# 0 3 * * * sh ~/.tools/clean.sh
# 0 2 * * * sh /home/box_admin_wsh/.tools/redis_backup.sh
# 0 0 * * 2,4,6 /bin/bash /home/box_admin_wsh/shuma/shell/run_prod.sh start crawl_jd_goods
# 0 12 1,15 * * /bin/bash /home/box_admin_wsh/shuma/shell/run_prod.sh start crawl_jd_prices
# 0 16 * * * /bin/bash /home/box_admin_wsh/shuma/shell/run_prod.sh start crawl_jd_detail
# 0 8 * * 1,3,5 /bin/bash /home/box_admin_wsh/shuma/shell/run_prod.sh start crawl_jd_discount
CMD_WRITE_JD_CATEGORY           = 'write_category'
CMD_CRAWL_JD_CATEGORY           = 'crawl_jd_category'
CMD_CRAWL_JD_GOODS              = 'crawl_jd_goods'    # 每周 2,4,6 爬取商品信息
CMD_CRAWL_JD_DETAIL             = 'crawl_jd_detail'   # 每周周日 0:00 开始爬取商品详情信息
CMD_CRAWL_JD_DISCOUNT           = 'crawl_jd_discount' # 每周周三 16:00 开始爬取折扣信息
CMD_CRAWL_JD_PRICES             = 'crawl_jd_prices'   # 每月 1,15 号 12:00 检查价格信息
CMD_CRAWL_HISTORY               = 'crawl_history'
# 环境值常量
ENV_LOCAL                       = 'local'
ENV_TEST                        = 'test'
ENV_SERVER_LOCAL                = 'server_local'
ENV_SERVER_REMOTE               = 'server_remote'

def get_request_headers():
  return {
    "Accept" : "application/jason, text/javascript, */*; q = 0.01",
    "X-Request-With" : "XMLHttpRequest",
    "User-Agent": random_useragent(),
    "Content-Type" : "application/x-www-form-urlencode:chartset=UTF-8"
  }

def get_detail_request_headers():
  return {
    "Accept" : "application/jason, text/javascript, */*; q = 0.01",
    "X-Request-With" : "XMLHttpRequest",
    "User-Agent": random_jd_detail_ua(),
    "Content-Type" : "application/x-www-form-urlencode:chartset=UTF-8"
  }

class GlobalConfig(object):
  '''全局的配置类，用来区分开发、测试和生产等环境'''
  def __init__(self):
    super().__init__()
    self.logLevel = logging.NOTSET # 默认日志输出级别
    self.logAppendix = ''
    self.db = DBConfig()
    self.redis = RedisConfig()
    self.log_filename = None

  def set_cmd(self, cmd: str):
    if cmd == CMD_WRITE_JD_CATEGORY or cmd == CMD_CRAWL_JD_CATEGORY:
        config.logAppendix = '-category'
    elif cmd == CMD_CRAWL_JD_GOODS:
        config.logAppendix = '-goods'
    elif cmd == CMD_CRAWL_JD_DETAIL:
        config.logAppendix = '-detail'
    elif cmd == CMD_CRAWL_JD_PRICES:
        config.logAppendix = '-prices'
    elif cmd == CMD_CRAWL_JD_DISCOUNT:
        config.logAppendix = '-discount'
    elif cmd == CMD_CRAWL_HISTORY:
        config.logAppendix = '-history'

  def set_env(self, env: str):
    """设置环境信息"""
    self._set_env_log_level(env)
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
      self.db.host = 'localhost'
      self.db.port = ***REMOVED***
      self.db.database = 'shuma'
      self.db.user = '***REMOVED***'
      self.db.password = '***REMOVED***'

      self.redis.host = 'localhost'
      self.redis.db = 0
      self.redis.password = '***REMOVED***'
      self.redis.port = 6379
    elif env == ENV_SERVER_REMOTE:
      self.db.host = '***REMOVED***'
      self.db.port = ***REMOVED***
      self.db.database = 'shuma'
      self.db.user = '***REMOVED***'
      self.db.password = '***REMOVED***'

      self.redis.host = '***REMOVED***'
      self.redis.db = 0
      self.redis.password = '***REMOVED***'
      self.redis.port = 6379
    else:
      logging.warning('Invalid Environment!')

  def _set_env_log_level(self, env):
    '''设置输出日志的级别'''
    if env == ENV_LOCAL or env == ENV_TEST:
      self.logLevel = logging.DEBUG
    elif env == ENV_SERVER_LOCAL or env == ENV_SERVER_REMOTE:
      self.logLevel = logging.INFO

  def config_logging(self):
    """配置应用日志"""
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
    self.log_filename = "log/" + str(datetime.date.today()) + self.logAppendix + '.log' # 指定输出路径，日志归纳到 log 目录下
    logging.basicConfig(filename=self.log_filename, filemode='a', level=self.logLevel, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.FileHandler(filename=self.log_filename, encoding='utf-8')

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
