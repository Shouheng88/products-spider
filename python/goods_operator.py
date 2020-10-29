#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
import re
import time
import random
import traceback
from typing import *

from operators import redisOperator as redis
from operators import dBOperator as db
from models import *
from utils import *
from config import *
from channels import *

class GoodsOperator(object):
  def __init__(self):
    super().__init__()

  def batch_insert_or_update_goods(self, goods_list: List[GoodsItem]):
    '''批量向数据库当中插入数据或者更新数据当中的记录'''
    succeed = True
    if goods_list == None or len(goods_list) == 0:
      logging.warning("Empty Goods List.")
      return succeed
    new_goods_map = {}
    for goods_item in goods_list:
      new_goods_map[goods_item.link] = goods_item
    existed_goods_list = self._get_existed_goods(goods_list)
    map_2_update = {} # 已经存在于数据库中的记录 => 用于更新
    for existed_goods in existed_goods_list:
      if existed_goods.link in new_goods_map:
        new_goods = new_goods_map.pop(existed_goods.link) # 移除指定的 key
        map_2_update[existed_goods.id] = new_goods
    # 批量更新
    if len(map_2_update) != 0:
      self._batch_update_goods(map_2_update)
    # 批量插入
    if len(new_goods_map) != 0:
      self._batch_insert_goods(new_goods_map)
    return succeed

  def next_goods_page(self, source: int, page_size: int, start_id: int) -> List[GoodsItem]:
    """从商品列表中读取一页数据来查询商品的价格信息，"""
    sql = ("SELECT * FROM gt_item WHERE price != -1 AND source = %s AND id > %s ORDER BY id LIMIT %s") % (source, start_id, page_size)
    rows = db.fetchall(sql)
    return self._rows_2_models(rows)

  def update_goods_list_as_sold_out(self, goods_list: List[GoodsItem]):
    '''将指定的产品列表标记为下架状态'''
    ids = ','.join([str(goods_item.id) for goods_item in goods_list])
    if len(ids.strip()) == 0:
        logging.info("Empty Goods Id List.")
        return False
    sql = "UPDATE gt_item SET price = -1, updated_time = %s WHERE id IN ( %s )" % (str(get_current_timestamp()), ids)
    ret = db.execute(sql)
    return ret != None

  def _batch_insert_goods(self, new_goods_map: Dict[str, GoodsItem]):
    '''向数据库中批量插入记录'''
    sql = "INSERT INTO gt_item (\
      name, promo, link, image, price, price_type, icons, channel_id,\
      channel, lock_version, updated_time, created_time, handling_time,source,\
      sku_id, product_id, comment_count, average_score, good_rate, comment_detail, vender_id\
      ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = []
    for goods_item in new_goods_map.values():
      values.append((goods_item.name.replace("'", "\'"), goods_item.promo.replace("'", "\'"), goods_item.link, 
          goods_item.image, goods_item.price, goods_item.price_type,
          goods_item.icons.replace("'", "\'"), goods_item.channel_id, goods_item.channel,
          0, int(get_current_timestamp()), int(get_current_timestamp()), 0, SOURCE_JINGDONG, # 将 handling_time 置为 0, souce 置为 0
          goods_item.sku_id, goods_item.product_id, goods_item.comment_count, 
          goods_item.average_score, goods_item.good_rate, goods_item.comment_detail, goods_item.vender_id))
    db.executemany(sql, tuple(values))
    sql_map = {}
    sql_map['sql'] = sql
    sql_map['val'] = tuple(values)
    return sql_map

  def _batch_update_goods(self, map_2_update: Dict[int, GoodsItem]):
    '''向数据库中批量更新记录'''
    val_ids = ",".join(map(str, map_2_update.keys()))
    # 拼接 when then 语句
    when_then_map = {} 
    for id, goods_item in map_2_update.items():
      goods_item.updated_time = get_current_timestamp()
      for column_name in ('name', 'promo', 'link', 'image', 'price', 'price_type', 'icons', 'updated_time', \
        'sku_id', 'product_id', 'comment_count', 'average_score', 'good_rate', 'comment_detail', 'vender_id'):
        when_then = when_then_map.get(column_name)
        if when_then == None:
          when_then = ''
        val = getattr(goods_item, column_name)
        if isinstance(val, str): # 如果是字符串类型的话，再包一层引号，还要处理 sql 中字符串的 ' 符号
          val = "'" + val.replace("'", "\\'") + "'"
        when_then = when_then + '\n' + ' WHEN ' + str(id) + ' THEN ' + str(val)
        when_then_map[column_name] = when_then
    sql_when_then = ",\n".join([ column_name + " = CASE id " + when_then + "\n END" for column_name, when_then in when_then_map.items() ]) + " \n"
    sql = "UPDATE gt_item SET \n %s WHERE id IN ( %s ) " % (sql_when_then, val_ids)
    db.execute(sql)
    sql_map = {}
    sql_map['sql'] = sql
    return sql_map

  def _get_existed_goods(self, goods_list: List[GoodsItem]) -> List[GoodsItem]:
    '''从数据库中查询指定的商品列表的商品信息'''
    val = ','.join(["'%s'" % goods.link for goods in goods_list])
    sql = "SELECT * FROM gt_item WHERE link IN (%s)" % val
    rows = db.fetchall(sql)
    return self._rows_2_models(rows)

  def _row_2_model(self, row) -> GoodsItem:
    if row == None:
      return None
    model = GoodsItem('', '', '', '', 0, '', '', '')
    for name, value in row.items():
      setattr(model, name, value)
    return model

  def _rows_2_models(self, rows) -> List[GoodsItem]:
    models = []
    if rows == None or len(rows) == 0:
      return models
    for row in rows:
      model = self._row_2_model(row)
      models.append(model)
    return models

go = GoodsOperator()
