#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import os
import codecs
import pymysql
import pymysql.cursors
import traceback
from typing import *

from models import *
from utils import *
from config import *
from operators import dBOperator as db
from channels import *

class BrandOperator(object):
  def __init__(self):
    super().__init__()

  def next_page_of_brands(self, page_size: int, start_id: int) -> List[Brand]:
    '''按页取一页品牌信息'''
    sql = ("SELECT * FROM gt_brand WHERE id > %s ORDER BY id LIMIT %s") % (start_id, page_size)
    rows = db.fetchall(sql)
    return self._rows_2_brands(rows)

  def batch_insert_or_update_brands(self, brands: List[Brand]):
    '''批量插入或者更新品牌列表'''
    succeed = True
    if brands == None or len(brands) == 0:
      logging.warning("Empty Brands List.")
      return succeed
    new_brands = {}
    for brand in brands:
      new_brands[brand.link] = brand
    existed_brands = self._get_existed_brands(brands)
    list_2_update = {} # 已经存在于数据库中的记录 => 用于更新
    for existed_brand in existed_brands:
      if existed_brand.link in new_brands:
        new_brand = new_brands.pop(existed_brand.link) # 移除指定的 key
        list_2_update[existed_brand.id] = new_brand
    # 批量更新
    if len(list_2_update) != 0:
      self._batch_update_brands(list_2_update)
    # 批量插入
    if len(new_brands) != 0:
      self._batch_insert_brands(new_brands)
    return succeed

  def _get_existed_brands(self, brands: List[Brand]) -> List[Brand]:
    val = ','.join(["'" + brand.link + "'" for brand in brands])
    sql = "SELECT * FROM gt_brand WHERE link IN (%s)" % val
    rows = db.fetchall(sql)
    return self._rows_2_brands(rows)

  def _batch_update_brands(self, list_2_update: Dict[int, Brand]):
    '''批量向数据库中插入品牌信息'''
    val_ids = ",".join(map(str, list_2_update.keys()))
    # 拼接 when then 语句
    when_then_map = {} 
    for id, brand in list_2_update.items():
      brand.updated_time = get_current_timestamp()
      for column_name in ('name', 'data_initial', 'logo', 'link', 'updated_time'):
        when_then = when_then_map.get(column_name)
        if when_then == None:
          when_then = ''
        val = getattr(brand, column_name)
        if isinstance(val, str): # 如果是字符串类型的话，再包一层引号
          val = "'" + val.replace("'", "\\'") + "'"
        when_then = when_then + '\n' + ' WHEN ' + str(id) + ' THEN ' + str(val)
        when_then_map[column_name] = when_then
    sql_when_then = ',\n'.join([ column_name + ' = CASE id ' + when_then + '\n END' for column_name, when_then in when_then_map.items() ]) + '\n'
    sql = "UPDATE gt_brand SET \n %s WHERE id IN ( %s ) " % (sql_when_then, val_ids)
    db.execute(sql)

  def _batch_insert_brands(self, link_map: Dict[str, Brand]):
    '''向数据库中批量插入品牌记录'''
    sql = "INSERT INTO gt_brand (\
      name,\
      data_initial,\
      logo,\
      link,\
      display_order,\
      channel_id,\
      channel,\
      remark,\
      lock_version,\
      updated_time,\
      created_time\
      ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = []
    for brand in link_map.values():
      values.append((
        brand.name.replace("'", "\'"),
        brand.data_initial,
        brand.logo,
        brand.link,
        brand.dispaly_order,
        brand.channel_id,
        brand.channel,
        '',                     # remark
        0,                      # lock_version
        int(get_current_timestamp()),
        int(get_current_timestamp())
      ))
    db.executemany(sql, tuple(values))

  def _row_2_brand(self, row) -> Brand:
    if row == None:
      return None
    brand = Brand(None, None, None, None, None)
    for name, value in row.items():
      setattr(brand, name, value)
    return brand

  def _rows_2_brands(self, rows) -> List[Brand]:
    brands = []
    if rows == None or len(rows) == 0:
      return brands
    for row in rows:
      brand = self._row_2_brand(row)
      brands.append(brand)
    return brands

bo = BrandOperator()
