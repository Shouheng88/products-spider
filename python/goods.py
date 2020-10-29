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

class JDGoods(object):
  '''京东商品信息爬取。这个类主要用来从商品列表中抓取商品的价格等基础信息（不包含商品的具体的参数信息）'''
  def __init__(self):
    super().__init__()
    self.max_page = 100         # 爬取的最大页数
    self.max_retry_count = 3    # 京东爬虫爬取评论的最大重试次数
    self.max_fail_count = 30    # 京东爬取数据的时候最大的失败次数，达到了这个数字之后认定为存在严重的问题，需要停止程序
    self.total_failed_count = 0

  def crawl(self):
    '''
    爬取每个品类的信息，这里每次任务结束之后就会结束程序。
    我们可以在服务器中使用定时脚本来在固定的时间判断爬虫进程是否存在，
    以此来决定是否重新开启程序。也就是说，我们每天的任务最多执行一遍，
    当然也可能存在一遍执行了多天的情形。这种情况，我们也只爬一遍。
    '''
    job_no = 0 # job 编号
    while True:      
      channel = co.next_channel_to_handle()
      if channel == None: # 没有需要爬取的任务了
        break
      job_no = job_no + 1 # 对任务进行解析
      logging.info(">>>> Crawling Channel: job[%d], channel[%s] <<<<" % (job_no, channel.name))
      succeed = self._crawl_jd_channel(channel) # 爬取某个品类的数据
      if not succeed:
        logging.warning(">>>> Crawling Channel Job Stopped Due to Fatal Error! [%d] channels done <<<<" % job_no)
        send_email('京东商品爬虫【异常】报告', '[%d] channels done' % (job_no), config.log_filename)
        return
      co.mark_channel_as_done(channel) # 将指定的品类标记为完成
    logging.info(">>>> Crawling Channel Job Finished: [%d] channels done <<<<" % job_no)
    send_email('京东商品爬虫【完成】报告', '[%d] channels done' % (job_no))

  def _crawl_jd_channel(self, channel: Channel):
    '''爬取指定的品类的所有的信息'''
    # 抓取分类的信息，也就是第一页的信息
    (succeed, max_page) = self.__crawl_jd_page(channel.jdurl, channel, True)
    max_page = min(max_page, self.max_page, channel.max_page_count)
    page_count = 1 # 已经抓取的页数
    for page_num in range(1, max_page):
      page_url = self.__get_page_url_of_page_number(channel.jdurl, page_num)
      (succeed, _max_page) = self.__crawl_jd_page(page_url, channel, False)
      page_count = page_count + 1
      if succeed:
        logging.info(">>>> Crawling Channel [%s] [%d]/[%d] <<<<" % (channel.name, page_count, max_page))
      else:
        self.total_failed_count = self.total_failed_count + 1
        logging.error(">>>> Failed to Scrawl Channel [%s] [%d]/[%d] <<<<" % (channel.name, page_count, max_page))
        if self.total_failed_count > self.max_fail_count:
          # 在这里进行监听，如果达到了最大从失败次数，就返回 False
          return False
      # 休眠一定时间
      time.sleep(random.random() * CRAWL_SLEEP_TIME_INTERVAL)
    return True

  def __get_page_url_of_page_number(self, jdurl, page_num):
    '''获取指定品类的指定的页码，用来统一实现获取指定的页码的地址的逻辑'''
    return jdurl + "&page=" + str(page_num)

  def __crawl_jd_page(self, page_url, channel: Channel, first_page):
    '''京东商品列表信息抓取，最大的页码、产品详情等基础信息'''
    headers = get_request_headers()
    html = requests.get(page_url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    (succeed1, max_page) = self.__crawl_jd_max_page(soup)
    (succeed2, goods_list) = self.__crawl_jd_goods_list(soup, channel)
    (succeed3, brand_list) = self.__crawl_jd_brand_list(soup, channel)
    # 持久化处理爬取结果
    if succeed2:
      # 爬取京东商品的评论信息
      succeed4 = self.__crawl_jd_comment_info(goods_list)
      # 首先将商品列表信息更新数据库当中
      succeed5 = go.batch_insert_or_update_goods(goods_list)
      # 然后将价格历史记录到 Redis 中，Redis 的操作应该放在 DB 之后，因为我们要用到数据库记录的主键
      existed_goods = go.get_existed_goods(goods_list)
      redis.add_goods_price_histories(existed_goods)
    else:
      logging.error("ILLEGAL UA:%s" % headers.get("User-Agent"))
    if succeed3 and first_page:
      # 对于每个品类，只在爬取第一页的时候更新品牌信息，减少服务器压力
      bo.batch_insert_or_update_brands(brand_list)
    return (succeed2 and succeed4 and succeed5, max_page)

  def __crawl_jd_max_page(self, soup: BeautifulSoup):
    '''解析京东的最大页数'''
    # 解析最大页码
    succeed = True
    max_page = self.max_page
    try:
      max_page = int(soup.select_one("#J_topPage > span > i").text)
    except BaseException as e:
      logging.error("Error While Getting Page Count:\n%s" % traceback.format_exc())
      succeed = False
    # 返回结果
    return (succeed, max_page)

  def __crawl_jd_goods_list(self, soup: BeautifulSoup, channel: Channel) -> (bool, List[GoodsItem]):
    '''解析京东的产品列表'''
    succeed = True
    goods_list = []
    try:
      goods_elements = soup.select("#J_goodsList > ul > li")
      for goods_element in goods_elements: # 解析产品信息
        sku_id = safeGetAttr(goods_element, 'data-sku', '')
        # 解析具体的信息：注意防范异常，提高程序鲁棒性
        url = safeGetAttr(goods_element.select_one(".p-img a"), "href", "")
        if len(url) > 200: # 个别商品的链接存在问题
          url = '//item.jd.com/%s.html' % sku_id
        img = safeGetAttr(goods_element.select_one(".p-img img"), "data-lazy-img", "")
        if img == None:
          img = safeGetAttr(goods_element.select_one(".p-img img"), "src", "")
        vid = safeGetAttr(goods_element.select_one(".p-img div"), "data-venid", "")
        prince_type = safeGetText(goods_element.select_one(".p-price em"), "")
        price = safeGetText(goods_element.select_one(".p-price i"), "-1")
        promo = safeGetAttr(goods_element.select_one(".p-name a"), "title", "")
        name = safeGetText(goods_element.select_one(".p-name a em"), "")
        commit_link = safeGetAttr(goods_element.select_one(".p-commit a"), "href", "")
        icons = safeGetText(goods_element.select_one(".p-icons i"), "")
        # logging.debug('url:%s\nimg:%s\nvid:%s\npt:%s\np:%s\npromo:%s\nname:%s\ncl:%s\nicons:%sskuid:%s\n'\
          # % (url, img, vid, prince_type, price, promo, name, commit_link, icons, sku_id))
        # 组装产品信息，价格要扩大 100 倍
        goods_item = GoodsItem(name, promo, url, img, int(float(price)*100), prince_type, icons, vid)
        goods_item.sku_id = sku_id
        goods_item.channel = channel.name
        goods_item.channel_id = channel.id
        goods_list.append(goods_item)
    except BaseException as e:
      succeed = False
      logging.error("Error While Getting Goods List:\n%s" % traceback.format_exc())
    # 返回结果
    return (succeed, goods_list)

  def __crawl_jd_brand_list(self, soup: BeautifulSoup, channel: Channel) -> (bool, List[Brand]):
    '''从页面中解析产品的品牌数据'''
    succeed = True
    brand_list = []
    try:
      display_order = 0
      brand_list_tags = soup.find_all(id=re.compile("brand")) # 所有的包含 id 包含 brand 的标签，即品牌
      for brand_list_tag in brand_list_tags:
        display_order = display_order + 1
        # 组装品牌信息
        brand = Brand(safeGetAttr(brand_list_tag.find("a"), "title", ""),
          safeGetAttr(brand_list_tag, "data-initial", ""),
          safeGetAttr(brand_list_tag.find("img"), "src", ""),
          safeGetAttr(brand_list_tag.find("a"), "href", ""), display_order)
        brand.channel = channel.name
        brand.channel_id = channel.id
        brand_list.append(brand)
    except BaseException as e:
      succeed = False
      logging.error("Error While Getting Brand List:\n%s" % traceback.format_exc())
    # 返回结果
    return (succeed, brand_list)

  def __crawl_jd_comment_info(self, goods_list: List[GoodsItem]):
    '''爬取京东商品的评论信息'''
    # 组装数据
    sku_id_map = {}
    for goods_item in goods_list:
      sku_id_map[goods_item.sku_id] = goods_item
    sku_ids = ",".join([str(goods_item.sku_id) for goods_item in goods_list])
    tried_count = 0 # 重试的次数
    if len(sku_ids) != 0:
      # 请求评论信息
      json_comments = None
      while tried_count < self.max_retry_count and json_comments == None:
        tried_count = tried_count + 1
        url = "https://club.jd.com/comment/productCommentSummaries.action?referenceIds=" + sku_ids
        try:
          # 进行请求，多次重试之后失败了就睡眠一会儿，然后进行重试
          json_comments = requests.get(url, headers=get_request_headers()).text
        except BaseException as e:
          logging.error("Error while requesting comments:\n%s" % traceback.format_exc())
          logging.error("Error while requesting comments:\n%s" % url)
          # 小小的睡眠一段时间
          time.sleep(random.random()*CRAWL_SLEEP_TIME_SHORT)
      # 最终还是失败了，输出日志并退出程序
      if json_comments == None:
        logging.error("Failed to Get goods Comments.")
        return False
      comments = json.loads(json_comments).get("CommentsCount")
      for comment in comments:
        sku_id = comment.get("SkuId")
        # 获取商品条目
        goods_item = sku_id_map.get(str(sku_id))
        if goods_item != None:
          goods_item.sku_id = sku_id
          goods_item.product_id = comment.get("ProductId")
          goods_item.comment_count = comment.get("CommentCount")
          goods_item.average_score = comment.get("AverageScore")
          goods_item.good_rate = int(comment.get("GoodRate")*100)
          goods_comment = GoodsComment(comment.get("DefaultGoodCount"), comment.get("GoodCount"), \
            comment.get("GeneralCount"), comment.get("PoorCount"), comment.get("VideoCount"), \
              comment.get("AfterCount"), comment.get("OneYear"), comment.get("ShowCount"))
          goods_item.comment_detail = goods_comment.to_json()
    return True

  def test(self):
    '''测试入口'''
    self.__crawl_jd_page("https://list.jd.com/list.html?cat=670%2C686%2C689&page=100", (328, ""), True)

class TBGoods(object):
  def __init__(self):
    super().__init__()

  def crawl(self):
    # 淘宝的都是以搜索的形式的
    html = requests.get("https://s.taobao.com/search?q=%E6%89%8B%E6%9C%BA", headers ={
      "Accept" : "application/jason, text/javascript, */*; q = 0.01",
      "X-Request-With" : "XMLHttpRequest",
      "User-Agent":"Mozilla/5.0 (Windows NT 10.0; ...) Gecko/20100101 Firefox/60.0",
      "Content-Type" : "application/x-www-form-urlencode:chartset=UTF-8",
      'cookie': 't=fc09ad46bdaacf77d576575754ce164a; enc=25WIP7P0FSKmvPciLcPfsEuT1JIuDE3HMHToPzzfx8%2B%2FVubIg77xDFrEFkSiaQ9myqlsh4JJI8Y2cLTvAEBo%2FA%3D%3D; hng=CN%7Czh-CN%7CCNY%7C156; thw=cn; _fbp=fb.1.1600140188248.332468417; tracknick=; cna=rTvJFyaJOV0CAWj752MYVDKZ; mt=ci=-1_0; xlly_s=1; _samesite_flag_=true; cookie2=1e454d5c02d1bd9981b3288ff41810ca; _tb_token_=efe37eeeeeeee; v=0; _m_h5_tk=038bceed31696698007415e8cb61a72c_1602844578531; _m_h5_tk_enc=75099bdc3351f64c971ed1885d8ec377; alitrackid=www.taobao.com; lastalitrackid=www.taobao.com; JSESSIONID=0F03B40EEC8F060650BEA25C784E0541; tfstk=cVdPBR0-Kbhy0QfIB_1UFMvZxdfRZQdHaSSPEpRoXfb7naXliEZdo0URuiStiTf..; l=eBrntNgeOYR5fegSBOfZourza779SIRAguPzaNbMiOCPOV1p5qENWZ56n2L9CnGVh6q9R3-wPvUJBeYBqIv4n5U62j-laskmn; isg=BMbGrG7l5VhWarFrP-uXSX05F7xIJwrhS3TFJrDvt-nEs2bNGLM18ZxBj-9_GwL5'
    })
    html.encoding = 'gbk'
    html = requests.get('https://detail.tmall.com/item.htm?id=608801385005', headers = {
      "Accept" : "application/jason, text/javascript, */*; q = 0.01",
      "X-Request-With" : "XMLHttpRequest",
      "User-Agent":"Mozilla/5.0 (Windows NT 10.0; ...) Gecko/20100101 Firefox/60.0",
      "Content-Type" : "application/x-www-form-urlencode:chartset=UTF-8",
      'cookie': 't=fc09ad46bdaacf77d576575754ce164a; enc=25WIP7P0FSKmvPciLcPfsEuT1JIuDE3HMHToPzzfx8%2B%2FVubIg77xDFrEFkSiaQ9myqlsh4JJI8Y2cLTvAEBo%2FA%3D%3D; hng=CN%7Czh-CN%7CCNY%7C156; thw=cn; _fbp=fb.1.1600140188248.332468417; tracknick=; cna=rTvJFyaJOV0CAWj752MYVDKZ; mt=ci=-1_0; xlly_s=1; _samesite_flag_=true; cookie2=1e454d5c02d1bd9981b3288ff41810ca; _tb_token_=efe37eeeeeeee; v=0; _m_h5_tk=038bceed31696698007415e8cb61a72c_1602844578531; _m_h5_tk_enc=75099bdc3351f64c971ed1885d8ec377; alitrackid=www.taobao.com; lastalitrackid=www.taobao.com; JSESSIONID=0F03B40EEC8F060650BEA25C784E0541; tfstk=cVdPBR0-Kbhy0QfIB_1UFMvZxdfRZQdHaSSPEpRoXfb7naXliEZdo0URuiStiTf..; l=eBrntNgeOYR5fegSBOfZourza779SIRAguPzaNbMiOCPOV1p5qENWZ56n2L9CnGVh6q9R3-wPvUJBeYBqIv4n5U62j-laskmn; isg=BMbGrG7l5VhWarFrP-uXSX05F7xIJwrhS3TFJrDvt-nEs2bNGLM18ZxBj-9_GwL5'
    })
    # logging.debug(html.text)

  def login(self):
    '''淘宝登录'''
    
    pass

  def test(self):
    cookies = [{'name': '_samesite_flag_', 'value': 'true', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 19, 'httpOnly': True, 'secure': True, 'session': True}, {'name': 'cookie2', 'value': '198cc95167581b3358dfe883041baba3', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 39, 'httpOnly': True, 'secure': False, 'session': True}, {'name': 'cna', 'value': '1AQUGJsekWsCATpkbQ3DyinP', 'domain': '.taobao.com', 'path': '/', 'expires': 2233801940, 'size': 27, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'tracknick', 'value': 'shouheng0808', 'domain': '.taobao.com', 'path': '/', 'expires': 1634623692.664334, 'size': 21, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 't', 'value': '62787c4b9687b3c6133ebb6bebfee91e', 'domain': '.taobao.com', 'path': '/', 'expires': 1610863692.664177, 'size': 33, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'l', 'value': 'eBICktVPOmJOVs92BOfanurza77OSIRYYuPzaNbMiOCP_9CB5MBkXZ5CDIY6C3GVh6mvR3-1IUIkBeYBq7Vonxv9w8VMULkmn', 'domain': '.taobao.com', 'path': '/', 'expires': 1618639694, 
            'size': 98, 'httpOnly': False, 'secure': False, 'session': False}, {'name': '_tb_token_', 'value': 'e5e37be395783', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 23, 'httpOnly': False, 'secure': False, 'session': True}, {'name': 'xlly_s', 'value': '1', 'domain': '.taobao.com', 'path': '/', 'expires': 1603168341, 'size': 7, 'httpOnly': False, 'secure': True, 'session': False}, {'name': 'lgc', 'value': 'shouheng0808', 'domain': '.taobao.com', 'path': '/', 'expires': 1605679692.664155, 'size': 15, 'httpOnly': False, 'secure': 
            False, 'session': False}, {'name': 'mt', 'value': 'ci=1_1', 'domain': '.taobao.com', 'path': '/', 'expires': 1603692494.035305, 'size': 8, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'dnk', 'value': 'shouheng0808', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 15, 'httpOnly': False, 'secure': False, 'session': True}, {'name': '_l_g_', 'value': 'Ug%3D%3D', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 13, 'httpOnly': False, 'secure': False, 'session': True}, {'name': 'sgcookie', 'value': 'E100diulm2bKRsdOqf2B2z87HguXYjQrpP%2B1vQZjAgwzkWR3AB1fi70%2FuIAQslssVd1KmyNHH4u0tg2IKXJRIvcVgg%3D%3D', 'domain': '.taobao.com', 'path': '/', 'expires': 1634623692.664214, 'size': 108, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'uc1', 'value': 'pas=0&cookie15=VT5L2FSpMGV7TQ%3D%3D&cookie16=VT5L2FSpNgq6fDudInPRgavC%2BQ%3D%3D&cookie14=Uoe0bkmAUrAjsg%3D%3D&existShop=false&cookie21=Vq8l%2BKCLjhS4UhJVbhgU', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 160, 'httpOnly': False, 'secure': False, 'session': True}, 
            {'name': 'unb', 'value': '1680333832', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 13, 'httpOnly': True, 'secure': False, 'session': True}, {'name': 'uc3', 'value': 'lg2=UtASsssmOIJ0bQ%3D%3D&vt3=F8dCufHHfcyyC36Ovtg%3D&id2=Uoe8iqifvGVHWw%3D%3D&nk2=EFY783GxR4G%2FiWeX', 'domain': '.taobao.com', 'path': '/', 'expires': 1605679692.664114, 'size': 102, 'httpOnly': True, 'secure': False, 'session': False}, {'name': 'csg', 'value': 'ae082d45', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 11, 'httpOnly': False, 'secure': False, 'session': True}, {'name': 'uc4', 'value': 'nk4=0%40Eo9FomkH1pRlXqJlEKbr%2F71QgmRda0Q%3D&id4=0%40UO%2B6bNEDF%2FPQTFVtgrZD26zSE34T', 'domain': '.taobao.com', 'path': '/', 'expires': 1605679692.664298, 'size': 88, 'httpOnly': True, 'secure': False, 'session': 
            False}, {'name': 'cookie17', 'value': 'Uoe8iqifvGVHWw%3D%3D', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 28, 'httpOnly': True, 'secure': False, 'session': True}, {'name': 'skt', 'value': 'ede997ffd99e0c7c', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 19, 'httpOnly': True, 'secure': False, 'session': True}, {'name': 'existShop', 'value': 'MTYwMzA4NzY5Mg%3D%3D', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 29, 'httpOnly': False, 'secure': False, 'session': True}, {'name': '_cc_', 'value': 'UIHiLt3xSw%3D%3D', 'domain': '.taobao.com', 'path': '/', 'expires': 1634623692.664376, 'size': 20, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'sg', 'value': '82e', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 5, 'httpOnly': False, 'secure': False, 'session': True}, {'name': '_nk_', 'value': 'shouheng0808', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 16, 'httpOnly': False, 'secure': False, 'session': True}, {'name': 'cookie1', 'value': 'AVZ%2FtpR0qlrLZMdfvi6yi4Fv71L%2FXcDv84O98Z6uBCE%3D', 'domain': '.taobao.com', 'path': '/', 'expires': -1, 'size': 57, 'httpOnly': True, 'secure': False, 'session': True}, {'name': 'thw', 'value': 'cn', 'domain': '.taobao.com', 'path': '/', 'expires': 1634623694.035356, 'size': 5, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'isg', 'value': 'BOrqQR4dQSi9Ac3Essdn-T8GO1CMW2619K0BzXSj9T3Jp4thSugKxBNFNdO7TOZN', 'domain': '.taobao.com', 'path': '/', 'expires': 1618639694, 'size': 67, 'httpOnly': False, 'secure': False, 'session': False}, {'name': 'tfstk', 'value': 'cQ8OB9VyuvDgs8Cpahn3lpOastDlwzoOp51LkbODk--WM91mRUYPNco1Lxzt9', 'domain': '.taobao.com', 'path': '/', 'expires': 1618639694, 'size': 66, 'httpOnly': False, 'secure': False, 'session': False}]
    # self.crawl()
    try:
      chrome_opt = Options()      # 创建参数设置对象.
      chrome_opt.add_argument('--headless')   # 无界面化.
      chrome_opt.add_argument('--disable-gpu')    # 配合上面的无界面化.
      chrome_opt.add_argument('--window-size=1366,768')   # 设置窗口大小, 窗口大小会有影响.
      driver = webdriver.Chrome(chrome_options=chrome_opt)     # 创建Chrome对象.
      wait = WebDriverWait(driver, 10)
      driver.get('https://s.taobao.com/search?q=华为手机')     # get方式访问百度.
      wait.until(EC.presence_of_element_located((By.ID, 'mainsrp-itemlist')))
      print(driver.page_source)
      driver.quit()
    except BaseException as e:
      logging.error("Error Diver:\n %s" % traceback.format_exc())

def tag_has_venid_attr(tag):
  return tag.has_attr('data-venid')

if __name__ == "__main__":
  '''调试入口'''
  config.config_logging()
  config.set_env(ENV_LOCAL)
  # gd = TBGoods()
  # gd.test()
  ret = co.next_channel_to_handle()
  print(ret.name)
