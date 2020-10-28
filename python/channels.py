#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import os
import codecs
import pymysql
import pymysql.cursors
import traceback
from typing import List

from models import *
from utils import *
from config import *
from operators import dBOperator as db
from channels import *

class ChannelOperator(object):
  def __init__(self):
    super().__init__()

  def write_channel(self, category: Category):
    '''将各个分类数据写入到数据库种'''
    con = self.connect_db()
    cur = con.cursor()
    row_id = -1
    try:
      # 先插入到数据库中，获取到记录的 id 之后再更新记录的 treepath 字段
      sql = "INSERT INTO gt_channel (\
        name, treepath, parent_id, cat, jdurl, tburl, max_page_count, \
        handling_time, display_order, lock_version, updated_time, created_time\
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, 0, 0, unix_timestamp(now()))"
      # 将处理时间默和最后更新 (完成时间) 默认设置为 0
      val = (category.name, category.treepath, category.parent_id, category.cat,
        category.jdurl, category.tburl, category.max_page_count, category.display_order)
      cur.execute(sql, val)
      row_id = cur.lastrowid
      # 再更新数据的 treepath 字段
      if len(category.treepath) == 0:
        category.treepath = str(row_id)
      else:
        category.treepath = category.treepath + "|" + str(row_id)
      cur.execute("UPDATE gt_channel SET treepath = %s WHERE id = %s", (category.treepath, row_id))
      con.commit()
    except Exception as e:
      con.rollback()
      logging.exception('Insert Operation Error :\n %s' % traceback.format_exc())
    finally:
      cur.close()
      con.close()
    return row_id

  def next_channel_to_handle(self) -> Channel:
    '''
    获取下一个需要处理的品类，如果返回的结果是 None 就表示这个品类的数据已经爬取完了。要求：
    1. updated_time 在今天之前，也就是每天最多爬取一次数据
    2. handling_time 在现在 2 分钟之前, 如果 2 分钟还没有完成，说明任务失败了
    3. 按照 updated_time 低到高排序，也就是上次完成时间
    '''
    f = None
    today_starter = get_timestamp_of_today_start()
    handling_before = get_current_timestamp() - get_seconds_of_minutes(CHANNEL_HANDLE_TIMEOUT_IN_MINUTE)
    sql = ("SELECT * FROM gt_channel WHERE updated_time < %s AND handling_time < %s ORDER BY updated_time") % (today_starter, handling_before)
    rows = db.fetchall(sql)
    if rows == None or len(rows) == 0:
      logging.info('Empty channel to handle.')
      return f
    for row in rows:
      channel = self._row_2_channel(row)
      if len(channel.treepath.split("|")) == 3: # 只处理三级品类
        sql = "UPDATE gt_channel SET handling_time = %s, lock_version = %s WHERE id = %s AND lock_version = %s"\
          % (get_current_timestamp(), channel.lock_version+1, row.get('id'), channel.lock_version)
        ret = db.execute(sql)
        if ret == 1: # 表示已经取到任务
          f = channel
          break
    return f

  def get_channels_of_ids(self, channel_id_list) -> List[Channel]:
    '''通过 channel id 列表获取 channel 数据'''
    id_list = []
    for id in channel_id_list:
      id_list.append(str(id))
    ids = ','.join(id_list)
    if len(ids.strip()) == 0:
      logging.info("Empty Channel Id List!")
      return None
    sql = 'SELECT * FROM gt_channel WHERE id IN ( %s )' % ids
    rows = db.fetchall(sql)
    return self._rows_2_channels(rows)

  def mark_channel_as_done(self, channel: Channel):
    '''
    将指定的品类标记为完成状态：
    1. 将 updated_time 设置为当前的时间
    2. 将 lock_version + 1
    3. 通过 lock_version 来做判断，防止因为任务超时，导致任务数据被其他人修改掉
    '''
    sql = "UPDATE gt_channel SET updated_time = %s, lock_version = %s WHERE id = %s AND lock_version = %s"\
      % (get_current_timestamp(), channel.lock_version+2, channel.id, channel.lock_version+1)
    ret = db.execute(sql)
    if ret != 1:
      logging.error("Failed to marking channel as done: %s\n" % traceback.format_exc())

  def _row_2_channel(self, row) -> Channel:
    '''将数据库中读取到的字典转换为 Channel 对象'''
    if row == None:
      return None
    channel = Channel()
    for name, value in row.items():
      setattr(channel, name, value)
    return channel

  def _rows_2_channels(self, rows) -> List[Channel]:
    channels = []
    if rows == None or len(rows) == 0:
      return channels
    for row in rows:
      channel = self._row_2_channel(row)
      channels.append(channel)
    return channels

co = ChannelOperator()
