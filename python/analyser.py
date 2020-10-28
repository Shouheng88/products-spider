#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import jieba
import json

from operators import dBOperator as db
from config import *

class Analyser(object):
  def __init__(self):
    super().__init__()
    self.counts = {}
    self.p_map = {}
    self.page_size = 200

  def analyze_name(self):
    '''对产品的名称进行分词统计分析，似乎名称里面并没有特别有值得分析的词汇'''
    job_no = start_id = item_count = 0
    start_id = 30000
    while True:
      # 不对各个品类的频率进行细化统计
      goods_list = db.next_goods_page_without_source(self.page_size, start_id)
      if len(goods_list) == 0:
        break
      item_count = item_count+len(goods_list)
      job_no = job_no+1
      logging.info(">>>> Analysing Goods: job[%d], starter[%d], [%d] itemd done <<<<" % (job_no, start_id, item_count))
      for goods_item in goods_list:
        name = goods_item[GOODS_NAME_ROW_INDEX]
        # 将特殊的字符替换为空格
        for ch in '!"#$%&()*+,-./:;<=>?@[\\]^_‘{|}~':
          name = name.replace(ch, " ")
        for word in jieba.lcut(name):
          if len(word) == 1:
            continue
          else:
            self.counts[word] = self.counts.get(word, 0) + 1   
      # TODO remove the break
      if job_no == 10:
        break
    items = list(self.counts.items())
    items.sort(key=lambda x: x[1], reverse=True)
    for item in items:
      word, count = item
      logging.debug("{0:<5}->{1:>5}".format(word, count))
  
  def analyse_parameters(self):
    '''对商品的参数进行分词分析'''
    job_no = start_id = item_count = 0
    while True:
      # 不对各个品类的频率进行细化统计
      goods_list = db.next_goods_page_without_source(self.page_size, start_id)
      if len(goods_list) == 0:
        break
      item_count = item_count+len(goods_list)
      job_no = job_no+1
      logging.info(">>>> Analysing Goods: job[%d], starter[%d], [%d] itemd done <<<<" % (job_no, start_id, item_count))
      for goods_item in goods_list:
        if goods_item[GOODS_PARAMETER_ROW_INDEX] != None:
          params = eval(goods_item[GOODS_PARAMETER_ROW_INDEX])
          for name, value in params.items():
            if self.p_map.get(name) == None:
              self.p_map[name] = []
            if value not in self.p_map[name]:
              self.p_map[name].append(value)
      # TODO remove the break
      # if job_no == 10:
      break
    logging.debug(self.p_map)

  def test(self):
    '''测试函数'''
    self.analyse_parameters()

if __name__ == "__main__":
  '''测试入口'''
  config.set_env(ENV_LOCAL)
  config.config_logging()
  an = Analyser()
  an.test()
