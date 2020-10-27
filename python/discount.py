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
  
  def crawl(self, start_id_ = None):
    '''查询产品的折扣信息'''
    job_no = start_id = item_count = 0
    if start_id_ != None:
      try:
        start_id = int(start_id_)
      except BaseException as e:
        logging.error("Faile to get number from param: %s" % start_id_)
    while True:
      goods_list = db.next_goods_page_for_icons(SOURCE_JINGDONG, DISCOUNT_FILTER_LIKES, DISCOUNT_HANDLE_PER_PAGE_SIZE, start_id) # 拉取一页数据
      if len(goods_list) == 0: # 表示可能是数据加锁的时候失败了
        break
      item_count = item_count + len(goods_list)
      start_id = goods_list[len(goods_list)-1][GOODS_ID_ROW_INDEX]
      job_no = job_no + 1
      self.__crawl_goods_discount(goods_list)
      logging.info('>>>> Crawling Discount: job[%d], starter[%d], [%d] items done. <<<<' % (job_no, start_id, item_count))
      if self.total_failed_count > JD_DISCOUNT_MAX_FAILE_COUNT: # 每批次的任务结束之后就检测一下
        # 同时输出 start_id 便于下次从失败中恢复
        logging.error(">>>> Crawling Prices Job Stopped Due to Fatal Error: job[%d], starter[%d], [%d] items done. <<<<" % (job_no, start_id, item_count))
        send_email('京东折扣爬虫【异常】报告', '[%d] jobs [%d] items done, starter: [%d]' % (job_no, item_count, start_id), config.log_filename)
        break
      # 休眠一定时间，其实爬数据的时候是一批分别 http 请求的，所以大休一下拉
      time.sleep(random.random() * CRAWL_SLEEP_TIME_INTERVAL)
    logging.info(">>>> Crawling Discount Job Finished: [%d] jobs [%d] items done <<<<" % (job_no, item_count))
    send_email('京东折扣爬虫【完成】报告', '[%d] jobs [%d] items done' % (job_no, item_count))

  def __crawl_goods_discount(self, goods_list):
    '''查询商品的折扣信息'''
    # 获取 channel 和 cat 信息
    channel_id_list = []
    for goods_item in goods_list:
      channel_id_list.append(goods_item[GOODS_CHANNEL_ID_ROW_INDEX])
    channels = db.get_channels_of_channel_ids(channel_id_list)
    cat_map = {}
    for channel in channels:
      cat_map[channel[CHANNEL_ID_ROW_INDEX]] = channel[CHANNEL_CAT_ROW_INDEX]
    # 循环抓取每个商品条目
    discount_map = {}
    for goods_item in goods_list:
      cat = cat_map.get(goods_item[GOODS_CHANNEL_ID_ROW_INDEX])
      if cat != None:
        req = "http://cd.jd.com/promotion/v2?skuId=%s&area=%s&venderId=%s&cat=%s" % (
          goods_item[GOODS_SKU_ID_ROW_INDEX], DISCOUNT_AREA, goods_item[GOODS_VEN_ID_ROW_INDEX], cat)
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
    rows = db.get_discounts_of_batch_ids(batch_id_list)
    for row in rows:
      batch_id = int(row[DISCOUNT_BATCH_ID_ROW_INDEX])
      if batch_id in discount_map:
        discount_map.pop(batch_id)
    if len(discount_map) != 0:
      db.batch_insert_discounts(discount_map.values())

  def test(self):
    '''测试入口'''
    self.crawl_discount()

if __name__ == "__main__":
  '''测试入口'''
  config.config_logging()
  dt = JDDiscount()
  dt.test()
