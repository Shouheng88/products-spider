#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, datetime
import smtplib
from email.header import Header
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
import traceback
import logging
import random
from fake_useragent import UserAgent

from useragent import *

def parse_number(num: str, def_val: int):
  '''从字符串中解析出数字'''
  if num != None:
    try:
      return int(num)
    except BaseException as e:
      logging.error("Faile to parse number : %s" % num)
  return def_val

def parse_number_or_none(num: str):
  try:
    return int(num)
  except BaseException as e:
    logging.error("Faile to parse number : %s" % num)

def to_str(obj: object) -> str:
  str_list = []
  fields = dir(obj)
  for field in fields:
    if not field.startswith('_'):
      str_list.append('%s:%s' % (field, getattr(obj, field)))
  return str(str_list)

def get_timestamp_of_today_start():
  """获取今天的开始时间的时间戳，就是当前的 0 时 0 分 0 秒的时间，返回的时间戳单位为毫秒"""
  str_today = str(datetime.date.today())
  str_today_start = str_today + " 0:0:0"
  return int(time.mktime(time.strptime(str_today_start, "%Y-%m-%d %H:%M:%S")))

def get_starter_timestamp_of_day(dat_str):
  '''从时间字符串中获取指定日期的开始时间戳'''
  if dat_str.find(' ') != -1:
    return int(time.mktime(time.strptime(dat_str, "%Y-%m-%d %H:%M")))
  else:
    return int(time.mktime(time.strptime(dat_str + " 0:0:0", "%Y-%m-%d %H:%M:%S")))

def get_current_timestamp():
  """获取当前的时间戳"""
  return int(time.time())

def get_seconds_of_minutes(minutes):
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

def send_email(subject: str, message: str, filename = None):
  '''向开发者邮箱发送邮件'''
  email_ = 'shouheng2015@gmail.com'
  from_ = "每日数据报告<***REMOVED***@qq.com>"
  to_ = '亲爱的开发者<%s>' % email_
  receivers = [email_]
  msg = MIMEMultipart()
  msg['From'] = _format_addr(from_) # 发送者
  msg['To'] =  _format_addr(to_) # 接收者
  msg['Subject'] = Header(subject, 'utf-8').encode()
  msg.attach(MIMEText(message, 'plain', 'utf-8'))
  if filename is not None:
    with open(filename, 'rb') as f:
      # 设置附件的MIME和文件名，这里是png类型:
      mime = MIMEBase('text', 'txt', filename='error.log')
      # 加上必要的头信息:
      mime.add_header('Content-Disposition', 'attachment', filename='error.log')
      mime.add_header('Content-ID', '<0>')
      mime.add_header('X-Attachment-Id', '0')
      # 把附件的内容读进来:
      mime.set_payload(f.read())
      # 用Base64编码:
      encoders.encode_base64(mime)
      # 添加到MIMEMultipart:
      msg.attach(mime)
  try:
    smtpObj = smtplib.SMTP_SSL('smtp.qq.com')
    #smtpObj.connect('smtp.qq.com')
    #smtpObj.ehlo()
    #smtpObj.starttls()
    smtpObj.login('***REMOVED***@qq.com', 'ffknbklvxzvncajd')
    smtpObj.sendmail('***REMOVED***@qq.com', receivers, msg.as_string())
    logging.info("Succeed to send email.")
  except BaseException as e:
    print("Failed to send email:\n%s" % traceback.format_exc())
    logging.error("Failed to send email:\n%s" % traceback.format_exc())

def _format_addr(s):
  name, addr = parseaddr(s)
  return formataddr((Header(name, 'utf-8').encode(), addr))

ua = UserAgent()

def random_fake_useragent():
  '''基于 fake-useragent 来获取一个随机的 ua，但是这个随机的 ua 有一定的可能是非法的，
  所以这个方法的返回结果是不可以直接使用的，可以多次请求来从该方法的返回结果中筛选出合法
  的 ua，然后再从合法的 ua 中随机选择 ua 作为请求的最终 ua'''
  return ua.random

def random_useragent():
  '''从自己维护的 useragent 列表中返回可用的 useragent'''
  return random.choice(USER_AGENTS)

def random_jd_detail_ua():
  return random.choice(DETAIL_USER_AGENTS)

# import socket
# import socks
# import requests

# def test_socks():
#   socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9150) # Tor 端口 9150
#   socket.socket = socks.socksocket
#   a = requests.get("http://checkip.amazonaws.com").text
#   print(a)

if __name__ == "__main__":
  # test_socks()
  send_email('京东价格爬虫【完成】报告', '[%d] jobs [%d] items done' % (0, 0))
