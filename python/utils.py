#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, datetime

# 时间相关的工具类
class TimeHelper(object):
  def __init__(self):
    super().__init__()

  # 获取今天的开始时间的时间戳
  def get_timestamp_of_today_start(self):
    """
    获取今天的开始时间的时间戳，就是当前的 0 时 0 分 0 秒的时间，返回的时间戳单位为毫秒
    """
    str_today = str(datetime.date.today())
    str_today_start = str_today + " 0:0:0"
    return int(time.mktime(time.strptime(str_today_start, "%Y-%m-%d %H:%M:%S")))

  # 获取当前的时间戳
  def get_current_timestamp(self):
    """获取当前的时间戳"""
    return int(time.time())

  # 获取 15 分钟的时间长度，单位秒
  def get_quartern_seconds(self):
    """获取一刻，也就是 15 分钟的时间长度，单位秒"""
    return 15 * 60

