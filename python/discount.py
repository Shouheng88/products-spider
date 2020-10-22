#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import re
import time
import random
import traceback

from operators import dBOperator as db
from models import *
from utils import *
from config import *

class JDDiscount(object):
  def __init__(self):
    super().__init__()
    self.total_failed_count = 0
  
  def crawl(self):
    '''查询产品的折扣信息'''
    job_no = 0
    start_id = 0
    item_count = 0
    while True:
      (task_done, goods_list) = db.next_goods_page_to_handle(SOURCE_JINGDONG, DISCOUNT_HANDLE_PER_PAGE_SIZE, start_id) # 拉取一页数据
      if task_done: # 表示任务完成了
        break
      if len(goods_list) == 0: # 表示可能是数据加锁的时候失败了
        continue
      item_count = item_count + len(goods_list)
      start_id = goods_list[len(goods_list)-1][GOODS_ID_ROW_INDEX]
      job_no = job_no + 1
      logging.info('>>>> Crawling Discount: job[%d] <<<<' % (job_no))
      self.__crawl_goods_discount(goods_list)
      # 休眠一定时间，其实爬数据的时候是一批分别 http 请求的，所以大休一下拉
      time.sleep(random.random() * CRAWL_SLEEP_TIME_INTERVAL)
    logging.info(">>>> Crawling Discount Job Finished: [%d] jobs [%d] items done <<<<" % (job_no, item_count))

  def __crawl_goods_discount(self, goods_list):
    '''查询商品的折扣信息'''
    # 获取 channel 和 cat 信息
    channel_ids = []
    for goods_item in goods_list:
      channel_id = goods_item[GOODS_CHANNEL_ID_ROW_INDEX]
      channel_ids.append(channel_id)
    channels = db.get_channels_of_channel_ids(channel_ids)
    cat_map = {}
    if channels != None:
      for channel in channels:
        channel_id = channel[CHANNEL_ID_ROW_INDEX]
        channel_cat = channel[CHANNEL_CAT_ROW_INDEX]
        cat_map[channel_id] = channel_cat
    # 循环抓取每个商品条目
    discount_map = {}
    for goods_item in goods_list:
      goods_id = goods_item[GOODS_ID_ROW_INDEX]
      sku_id = goods_item[GOODS_SKU_ID_ROW_INDEX]
      ven_id = goods_item[GOODS_VEN_ID_ROW_INDEX]
      channel_id = goods_item[GOODS_CHANNEL_ID_ROW_INDEX]
      cat = cat_map.get(channel_id)
      if cat != None:
        discount_json = requests.get("https://cd.jd.com/promotion/v2?skuId=%s&area=12_904_3373_0&venderId=%s&cat=%s" % (sku_id, ven_id, cat), headers=REQUEST_HEADERS).text
        # logging.debug(discount_json)
        discount_obj = json.loads(discount_json)
        coupons = discount_obj.get('skuCoupon')
        for coupon in coupons:
          start_time = get_starter_timestamp_of_day(coupon.get('beginTime'))
          end_time = get_starter_timestamp_of_day(coupon.get('endTime'))
          batch_id = coupon.get('batchId')
          discount = Discount(goods_id, batch_id, coupon.get('quota')*100, coupon.get('trueDiscount')*100, start_time, end_time)
          discount_map[batch_id] = discount
      else:
        logging.warning("Failed To Get Discount Due: the cat not found.")
    # 过滤已经存在的折扣
    if len(discount_map) != 0:
      batch_id_list = []
      for batch_id, discount in discount_map.items():
        batch_id_list.append(batch_id)
      rows = db.get_discounts_of_batch_ids(batch_id_list)
      if rows != None:
        for row in rows:
          batch_id = int(row[DISCOUNT_BATCH_ID_ROW_INDEX])
          if batch_id in discount_map:
            discount_map.pop(batch_id)
      discounts = []
      for batch_id, discount in discount_map.items():
        discounts.append(discount)
      db.batch_insert_discounts(discounts)
    else:
      logging.warning("Empty Discount Map!")

  def test(self):
    '''测试入口'''
    self.crawl_discount()

if __name__ == "__main__":
  '''测试入口'''
  config.config_logging()
  dt = JDDiscount()
  dt.test()
