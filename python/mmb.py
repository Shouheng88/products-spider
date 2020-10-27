#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, datetime
import traceback
import logging
import requests
import json
from config import *
from utils import *
from operators import dBOperator as db
from operators import redisOperator as redis

class ManmanBuy(object):
  def __init__(self):
    super().__init__()
    self.token = 'm9if2229dad9f89afe1cfaf6213e63029540uqbcaeopxr'
    self.total_failed_count = 0

  def crawl(self, start_id_=None):
    '''爬取任务信息'''
    job_no = start_id = item_count = 0
    if start_id_ != None:
      try:
        start_id = int(start_id_)
      except BaseException as e:
        logging.error("Faile to get number from param: %s" % start_id_)
    while True:
      goods_list = db.next_goods_page_of_channels(PRICE_HISTORY_HANDLE_CHANNELS, PRICE_HISTORY_HANDLE_PER_PAGE_SIZE, start_id) # 拉取一页数据
      if len(goods_list) == 0: # 表示可能是数据加锁的时候失败了
        break
      item_count = item_count + len(goods_list)
      start_id = goods_list[len(goods_list)-1][GOODS_ID_ROW_INDEX]
      job_no = job_no + 1
      self._crawl_goods(goods_list)
      logging.info('>>>> Crawling Price History: job[%d], starter[%d], [%d] items done. <<<<' % (job_no, start_id, item_count))
      if self.total_failed_count > HISTORY_MAX_FAILE_COUNT: # 每批次的任务结束之后就检测一下
        # 同时输出 start_id 便于下次从失败中恢复
        logging.error(">>>> Crawling Price History Job Stopped Due to Fatal Error: job[%d], starter[%d], [%d] items done. <<<<" % (job_no, start_id, item_count))
        send_email('历史价格爬虫【异常】报告', '[%d] jobs [%d] items done, starter: [%d]' % (job_no, item_count, start_id), config.log_filename)
        break
      # 休眠一定时间，其实爬数据的时候是一批分别 http 请求的，所以大休一下拉
      time.sleep(random.random() * CRAWL_SLEEP_TIME_INTERVAL)
    logging.info(">>>> Crawling Price History Job Finished: [%d] jobs [%d] items done <<<<" % (job_no, item_count))
    send_email('价格历史爬虫【完成】报告', '[%d] jobs [%d] items done' % (job_no, item_count))

  def _crawl_goods(self, goods_list):
    '''爬取商品列表'''
    try:
      req_map = {}
      for goods_item in goods_list:
        link = 'http:' + goods_item[GOODS_LINK_ROW_INDEX]
        ret = self._request_api(link, req_map)
        date_prices = json.loads(("[%s]" % ret.get('datePrice')).replace(',]', ']'))
        pcice_map = {}
        for data_price in date_prices:
          date = int(data_price[0]/1000) # 保留到秒
          price = int(data_price[1]*100) # 扩大 100 倍
          pcice_map[date] = price
        redis.add_prices(goods_item, pcice_map)
        time.sleep(random.random()*CRAWL_SLEEP_TIME_SHORT)
    except BaseException as e:
      logging.error("Error while crawling price hisotry:\n%s" % traceback.format_exc())
      logging.error("REQ: %s" % req_map.get('REQ')) 
      self.total_failed_count = self.total_failed_count+1
      time.sleep(random.random()*CRAWL_SLEEP_TIME_MIDLLE)

  def _request_api(self, link, req_map):
    '''请求 api'''
    url = 'http://tool.manmanbuy.com/history.aspx?DA=1&action=gethistory&url=%s&bjid=&spbh=&cxid=&zkid=&w=350&token=%s' % (link, self.token)
    req_map['REQ'] = url
    ret = requests.get(url, headers=get_request_headers()).text
    return json.loads(ret)

  def test(self):
    self.request_api('https//:item.jd.com/100009082466.html')

if __name__ == "__main__":
  config.config_logging()
  ManmanBuy().test()
