#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, datetime

class TimeHelper(object):
  def __init__(self):
    super().__init__()

def get_timestamp_of_today_start(self):
  """
  获取今天的开始时间的时间戳，就是当前的 0 时 0 分 0 秒的时间，返回的时间戳单位为毫秒
  """
  str_today = str(datetime.date.today())
  str_today_start = str_today + " 0:0:0"
  return int(time.mktime(time.strptime(str_today_start, "%Y-%m-%d %H:%M:%S")))

def get_current_timestamp(self):
  """获取当前的时间戳"""
  return int(time.time())

def get_seconds_of_minutes(self, minutes):
    """获取指定的分钟的描述"""
    return minutes * 60

def safeGetAttr(node, attr, value):
  '''安全的方式来获取属性，用于 BeautifulSoup，防止程序运行中出现空指针异常'''
  if node == None:
    return value
  else:
    ret = node.get(attr)
    if ret == None:
      return value
    else:
      return ret

def safeGetText(node, value):
  '''安全的方式来获取节点的 text 信息，用于 BeautifulSoup，防止程序运行中出现空指针异常'''
  if node == None:
    return value
  else:
    ret = node.text
    if ret == None:
      return value
    else:
      return ret
