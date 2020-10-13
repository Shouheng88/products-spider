#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
from bs4 import BeautifulSoup
from operators import DBOperator as DB
from config import CHANNEL_JD_URL_ROW_INDEX as jdurl_idx
from config import JD_MAX_SEARCH_PAGE as jd_max_page
from config import GlobalConfig as Config

# 京东商品爬取
class JDGoods(object):
  '''
  京东商品信息爬取
  这个类主要用来从商品列表中抓取商品的价格等基础信息（不包含商品的具体的参数信息）
  '''
  def __init__(self):
    super().__init__()

  # 爬取商品信息
  def crawl(self):
    '''
    爬取每个品类的信息，这里每次任务结束之后就会结束程序。
    我们可以在服务器中使用定时脚本来在固定的时间判断爬虫进程是否存在，
    以此来决定是否重新开启程序。也就是说，我们每天的任务最多执行一遍，
    当然也可能存在一遍执行了多天的情形。这种情况，我们也只爬一遍。
    '''
    job_no = 0 # job 编号
    db = DB()
    while True:      
      channel = db.next_channel_to_handle()
      # 没有需要爬取的任务了
      if channel == None:
        break
      # 对任务进行解析
      job_no = job_no + 1
      logging.info("正在爬取品类 (%d)：%s" % (job_no, str(channel)))
      jdurl = channel[jdurl_idx]
      # 爬取某个品类的数据
      self.__crawl_jd_channel(jdurl)
      # 将指定的品类标记为完成
      db.mark_channel_as_done(channel)
    # 任务完成！！！！！撒花！！！！!
    # *★,°*:.☆(￣▽￣)/$:*.°★* 
    logging.info("商品信息爬取任务结束！")

  # 爬取某个 url 的数据
  def __crawl_jd_channel(self, jdurl):
    '''爬取指定的品类的所有的信息'''
    (totoal_count) = self.__crawl_jd_page(jdurl)
    page_count = 1
    for page_num in len(0):
      page_url = self.__get_page_url_of_page_number(jdurl, page_num)
      # step 1: 从页面上解析最大的页数数据，并且根据该页数的限制进行只爬指定的页数
      self.__crawl_jd_page(self)
  
  # 获取指定的页码的网页的 url
  def __get_page_url_of_page_number(self, jdurl, page_num):
    '''获取指定品类的指定的页码，用来统一实现获取指定的页码的地址的逻辑'''
    return jdurl + "&page=" + str(page_num)

  # 获取产品的一页的信息
  def __crawl_jd_page(self, page_url):
    '''获取京东商品列表'''
    headers = {
      "Accept" : "application/jason, text/javascript, */*; q = 0.01",
      "X-Request-With" : "XMLHttpRequest",
      "User-Agent":"Mozilla/5.0 (Windows NT 10.0; ...) Gecko/20100101 Firefox/60.0",
      "Content-Type" : "application/x-www-form-urlencode:chartset=UTF-8"
    }
    html = requests.get(page_url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    # 解析最大页码
    max_page = jd_max_page
    try:
      pageText = soup.find(id="J_topPage").find("span").text
      index = pageText.find("/")
      max_page = int(pageText[(index+1):])
    except BaseException as e:
      logging.error("Error While Getting Page Count : " + str(e))
    logging.debug("Getting JD Max Page : %d " % max_page)
    # 解析产品列表
    result_goods = []
    try:
      goods_list_parent = soup.find(id="J_goodsList")
      goods_list_items = goods_list_parent.find_all(class_="gl-item")
      for goods_list_item in goods_list_items: # 解析产品信息
        # 几个大块
        p_img = goods_list_item.find(class_="p-img")
        p_price = goods_list_item.find(class_="p-price")
        p_name = goods_list_item.find(class_="p-name")
        p_commit = goods_list_item.find(class_="p-commit")
        p_shop = goods_list_item.find(class_="p-shop")
        p_icons = goods_list_item.find(class_="p-icons")
        # 解析具体的信息：注意防范异常，提高程序鲁棒性
        url = p_img.find("a").get("href")
        img = p_img.find("img").get("data-lazy-img")
        if img == None:
          img = p_img.find("img").get("src")
        prince_type = p_price.find("em").text
        price = p_price.find("i").text
        promo = p_name.find("a").get("title")
        name = p_name.find("a").find("em").text
        commit_link = p_commit.find("a").get("href")
        icons = p_icons.find("i").text
        # 
        logging.debug(str(url) + "\n"
          + str(img) + "\n" 
          + str(prince_type) + "\n" 
          + str(price) + "\n" 
          + str(promo) + "\n" 
          + str(name) + "\n" 
          + str(commit_link) + "\n" 
          + str(icons))
    except BaseException as e:
      logging.error("Error While Getting Goods List : " + str(e))

  # 将产品插入到数据库中
  def insert_into_db(self):
    '''
    应该根据产品的链接作为唯一的标志，每次将产品的信息更新到该链接上面
    产品的信息写入到数据库表中，产品的价格数据写入到 Redis 中
    '''
    pass

  # 测试入口
  def test(self):
    '''测试入口'''
    self.__crawl_jd_page("https://list.jd.com/list.html?cat=670%2C686%2C689&page=100")

# 产品信息
class Goods(object):
  def __init__(self):
    super().__init__()

# 调试入口
if __name__ == "__main__":
  config = Config()
  config.config_logging()
  gd = JDGoods()
  gd.test()
