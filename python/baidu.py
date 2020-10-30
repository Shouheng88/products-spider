#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
import re
from bs4 import BeautifulSoup
import traceback
import json
import time
import random
from typing import List
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import *
from models import *
from config import *
from operators import redisOperator as redis
from operators import dBOperator as db
from channels import *
from brands import *
from goods_operator import *

class BaiduBaike(object):
  def __init__(self):
    super().__init__()
    self.page_size = 20

  def crawl(self):
    starter = 0
    brands = bo.next_page_of_brands(self.page_size, starter)
    for brand in brands:
      self.get_from_baike(brand.name)

  def get_from_baike(self, name: str):
    search_name = self.handle_brand_name(name)
    headers = get_request_headers()
    html = requests.get("https://baike.baidu.com/item/%s" % search_name, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    summary = safeGetText(soup.select_one('.lemma-summary'), '').replace('\xa0', '')
    logo = safeGetAttr(soup.select_one(".summary-pic img"), 'src', '')
    logging.debug("%s _ %s SUMMARY: %s" % (name, search_name, summary))
    logging.debug("%s _ %s LOGO: %s" % (name, search_name, logo))

  def handle_brand_name(self, name: str):
    l = name.find('（')
    r = name.find('）')
    if l != -1 and r != -1:
      return name.replace(name[l:r+1], '', -1)
    else:
      return name

if __name__ == "__main__":
  config.config_logging()
  config.set_env(ENV_LOCAL)
  BaiduBaike().crawl()
