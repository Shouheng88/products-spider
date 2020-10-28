#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import re
import time
import random
import traceback
from typing import List

from operators import redisOperator as redis
from operators import dBOperator as db
from models import *
from utils import *
from config import *
from channels import *

class JDDiscount(object):
  def __init__(self):
    super().__init__()
    self.max_faile_count = 30
    self.total_failed_count = 0
    self.per_page_size = 5
    self.group_count = 4 # 要将全部的折扣数据分成多少组，生产约 1w 折扣商品需要爬取，每批次约 2500 条数据需要爬取
  
  def crawl(self, start_id_ = None):
    '''查询产品的折扣信息'''
    job_no = start_id = item_count = 0
    type_index = int(redis.get_jd_type_index('discount')) % self.group_count # 折扣的自增 index
    if start_id_ != None:
      try:
        start_id = int(start_id_)
      except BaseException as e:
        logging.error("Faile to get number from param: %s" % start_id_)
    while True:
      goods_list = db.next_goods_page_for_icons(SOURCE_JINGDONG, ('-', '减', '券'), self.per_page_size, start_id, type_index, self.group_count) # 拉取一页数据
      if len(goods_list) == 0: # 表示可能是数据加锁的时候失败了
        break
      item_count = item_count + len(goods_list)
      start_id = goods_list[len(goods_list)-1][GOODS_ID_ROW_INDEX]
      job_no = job_no + 1
      self.__crawl_goods_discount(goods_list)
      logging.info('>>>> Crawling Discount: job[%d], starter[%d], index[%d], [%d] items done. <<<<' % (job_no, start_id, type_index, item_count))
      if self.total_failed_count > self.max_faile_count: # 每批次的任务结束之后就检测一下
        # 同时输出 start_id 便于下次从失败中恢复
        logging.error(">>>> Crawling Prices Job Stopped Due to Fatal Error: job[%d], starter[%d], index[%d], [%d] items done. <<<<" % (job_no, start_id, type_index, item_count))
        send_email('京东折扣爬虫【异常】报告', '[%d] jobs [%d] items done, starter: [%d], index[%d]' % (job_no, item_count, start_id, type_index), config.log_filename)
        break
      # 休眠一定时间，其实爬数据的时候是一批分别 http 请求的，所以大休一下拉
      time.sleep(random.random() * CRAWL_SLEEP_TIME_INTERVAL)
    logging.info(">>>> Crawling Discount Job Finished: [%d] jobs [%d] items done, index[%d] <<<<" % (job_no, item_count, type_index))
    send_email('京东折扣爬虫【完成】报告', '[%d] jobs [%d] items done, index[%d]' % (job_no, item_count, type_index))
    redis.increase_jd_type_index('discount')

  def __crawl_goods_discount(self, goods_list):
    '''查询商品的折扣信息'''
    # 获取 channel 和 cat 信息
    channel_id_list = []
    for goods_item in goods_list:
      channel_id_list.append(goods_item[GOODS_CHANNEL_ID_ROW_INDEX])
    channels = co.get_channels_of_ids(channel_id_list)
    cat_map = {}
    for channel in channels:
      cat_map[channel.id] = channel.cat
    # 循环抓取每个商品条目
    discount_map = {}
    for goods_item in goods_list:
      cat = cat_map.get(goods_item[GOODS_CHANNEL_ID_ROW_INDEX])
      if cat != None:
        req = "http://cd.jd.com/promotion/v2?skuId=%s&area=%s&venderId=%s&cat=%s" % (
          goods_item[GOODS_SKU_ID_ROW_INDEX], self._random_discount_area(), goods_item[GOODS_VEN_ID_ROW_INDEX], cat)
        try:
          headers = get_request_headers()
          resp_text = requests.get(req, headers=headers).text
          discount_obj = json.loads(resp_text)
          coupons = discount_obj.get('skuCoupon')
          antiSpider = discount_obj.get('antiSpider')
          if coupons == None:
            if antiSpider == True:
              logging.error("Errir while request discount, invoked anit-spider. \nREQ:%s\nHEADERS:%s\nRESP:%s" % (req, headers, resp_text))
              self.total_failed_count = self.total_failed_count + 1 # 错误次数+1，触发了爬虫的时候次数也加 1
              time.sleep(CRAWL_SLEEP_TIME_LONG) # 触发了反爬虫，睡眠一定时间
            continue # 跳过
          for coupon in coupons:
            start_time = get_starter_timestamp_of_day(coupon.get('beginTime'))
            end_time = get_starter_timestamp_of_day(coupon.get('endTime'))
            batch_id = coupon.get('batchId')
            discount = Discount(goods_item[GOODS_ID_ROW_INDEX], batch_id, coupon.get('quota')*100, coupon.get('trueDiscount')*100, start_time, end_time)
            discount_map[batch_id] = discount
        except BaseException as e:
          self.total_failed_count = self.total_failed_count + 1 # 错误次数+1
          logging.error("Error while request discount info:\n%s" % traceback.format_exc())
          logging.error("REQ:\n%s" % req)
          time.sleep(random.random()*CRAWL_SLEEP_TIME_MIDLLE) # 小憩一会儿
      else:
        logging.warning("Failed To Get Discount Due: the cat not found.")
    # 过滤已经存在的折扣
    batch_id_list = list(discount_map.keys())
    discounts = do.get_discounts_of_batch_ids(batch_id_list)
    for discount in discounts:
      if int(discount.batch_id) in discount_map:
        discount_map.pop(int(discount.batch_id))
    if len(discount_map) != 0:
      do.batch_insert_discounts(discount_map.values())

  def _random_discount_area(self):
    '''随机返回一个地址信息'''
    return random.choice(['12_904_3373_0', '15_1213_1214_52674', '15_1273_1275_22204', '15_1262_1267_56327',
      '15_1158_1224_46479', '15_1250_1251_44548', '15_1255_15944_44627', '15_1255_15944_59428'])

  def test(self):
    '''测试入口'''
    self.crawl()

class DiscountOperator(object):
  def __init__(self):
    super().__init__()

  def get_discounts_of_batch_ids(self, batch_id_list):
    '''根据传入的折扣的 id 列表查出数据库中存储的折扣记录'''
    id_list = []
    for id in batch_id_list:
      id_list.append(str(id))
    batch_ids = ','.join(id_list)
    if len(batch_ids.strip()) == 0:
      logging.info("Empty Batch Id List!") # 出现这个信息属于正常现象，即商品没有折扣信息
      return []
    sql = "SELECT * FROM gt_discount WHERE batch_id IN ( %s )" % batch_ids
    rows = db.fetchall(sql)
    return self._rows_2_discounts(rows)

  def batch_insert_discounts(self, discounts: List[Discount]):
    '''批量向数据库中插入折扣信息'''
    sql = "INSERT INTO gt_discount (goods_id, batch_id, quota, discount, start_time, end_time,\
      lock_version, updated_time, created_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = []
    for discount in discounts:
      values.append((discount.goods_id, discount.batch_id, discount.quota, discount.discount, 
        discount.start_time, discount.end_time, 0, get_current_timestamp(), get_current_timestamp()))
    return db.executemany(sql, tuple(values))

  def _row_2_discount(self, row) -> Discount:
    if row == None:
      return None
    discount = Discount(None, None, None, None, None, None)
    for name, value in row.items():
      setattr(discount, name, value)
    return discount

  def _rows_2_discounts(self, rows) -> List[Discount]:
    discounts = []
    if rows == None or len(rows) == 0:
      return discounts
    for row in rows:
      discount = self._row_2_discount(row)
      discounts.append(discount)
    return discounts

do = DiscountOperator()

if __name__ == "__main__":
  '''测试入口'''
  config.set_env(ENV_LOCAL)
  config.config_logging()
  # dt = JDDiscount()
  # dt.test()
  channels = co.get_channels_of_ids([498,499,500])
  for c in channels:
    print(c.name)
