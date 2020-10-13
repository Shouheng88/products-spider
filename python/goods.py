#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
from bs4 import BeautifulSoup
from utils import safeGetAttr
from utils import safeGetText
from operators import DBOperator as DB
from operators import RedisOperator as Redis
from config import CHANNEL_NAME_ROW_INDEX as channel_name_idx
from config import CHANNEL_JD_URL_ROW_INDEX as jdurl_idx
from config import JD_MAX_SEARCH_PAGE as jd_max_page
from config import GlobalConfig as Config
from config import REQUEST_HEADERS

class JDGoods(object):
  '''京东商品信息爬取。这个类主要用来从商品列表中抓取商品的价格等基础信息（不包含商品的具体的参数信息）'''
  def __init__(self):
    super().__init__()

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
      # 爬取某个品类的数据
      self.__crawl_jd_channel(channel)
      # 将指定的品类标记为完成
      db.mark_channel_as_done(channel)
    # 任务完成！！！！！撒花！！！！!
    # *★,°*:.☆(￣▽￣)/$:*.°★* 
    logging.info("商品信息爬取任务结束！")

  def __crawl_jd_channel(self, channel):
    '''爬取指定的品类的所有的信息'''
    channel_url = channel[jdurl_idx]
    channel_name = channel[channel_name_idx]
    # 抓取分类的信息，也就是第一页的信息
    (succeed, max_page) = self.__crawl_jd_page(channel_url)
    page_count = 1 # 已经抓取的页数
    for page_num in range(1, min(max_page, jd_max_page)):
      page_url = self.__get_page_url_of_page_number(channel_url, page_num)
      # step 1: 从页面上解析最大的页数数据，并且根据该页数的限制进行只爬指定的页数
      (succeed, _max_page) = self.__crawl_jd_page(self, page_url)
      page_count = page_count + 1
      if succeed:
        logging.info("Succeed To Scrawl Channel %s [%d]," % (channel_name, page_count))
      else:
        logging.error("Failed To Scrawl Channel %s [%d]," % (channel_name, page_count))
  
  def __get_page_url_of_page_number(self, jdurl, page_num):
    '''获取指定品类的指定的页码，用来统一实现获取指定的页码的地址的逻辑'''
    return jdurl + "&page=" + str(page_num)

  def __crawl_jd_page(self, page_url):
    '''京东商品列表信息抓取，最大的页码、产品详情等基础信息'''
    headers = REQUEST_HEADERS
    html = requests.get(page_url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    (succeed1, max_page) = self.__crawl_jd_max_page(soup)
    (succeed2, goods_list) = self.__crawl_jd_goods_list(soup)
    if succeed2:
      self.__handle_goods_result(goods_list)
    return (succeed1 and succeed2, max_page)

  def __crawl_jd_max_page(self, soup):
    '''解析京东的最大页数'''
    # 解析最大页码
    succeed = True
    max_page = jd_max_page
    try:
      pageText = soup.find(id="J_topPage").find("span").text
      index = pageText.find("/")
      max_page = int(pageText[(index+1):])
    except BaseException as e:
      logging.error("Error While Getting Page Count : " + str(e))
      succeed = False
    # 返回结果
    return (succeed, max_page)

  def __crawl_jd_goods_list(self, soup):
    '''解析京东的产品列表'''
    succeed = True
    goods_list = []
    try:
      goods_list_parent = soup.find(id="J_goodsList")
      goods_list_items = goods_list_parent.find_all(class_="gl-item")
      for goods_list_item in goods_list_items: # 解析产品信息
        # 几个信息组成部分
        p_img = goods_list_item.find(class_="p-img")
        p_price = goods_list_item.find(class_="p-price")
        p_name = goods_list_item.find(class_="p-name")
        p_commit = goods_list_item.find(class_="p-commit")
        p_shop = goods_list_item.find(class_="p-shop")
        p_icons = goods_list_item.find(class_="p-icons")
        # 通过判断名称是否存在来决定程序是否出现问题
        if p_name == None:
          succeed = False
          logging.error("FATAL ERROR!!! FAILED TO GET ATTRIBUTE!!!!")
          break
        # 解析具体的信息：注意防范异常，提高程序鲁棒性
        url = safeGetAttr(p_img.find("a"), "href", "")
        img = safeGetAttr(p_img.find("img"), "data-lazy-img", "")
        if img == None:
          img = safeGetAttr(p_img.find("img"), "src", "")
        prince_type = safeGetText(p_price.find("em"), "")
        price = safeGetText(p_price.find("i"), "")
        promo = safeGetAttr(p_name.find("a"), "title", "")
        name = safeGetText(p_name.find("a").find("em"), "")
        commit_link = safeGetAttr(p_commit.find("a"), "href", "")
        icons = safeGetText(p_icons.find("i"), "")
        # 组装产品信息
        goods_item = Goods_Item()
        goods_item.name = name
        goods_item.promo = promo
        goods_item.link = url
        goods_item.image = img
        goods_item.price = price
        goods_item.price_type = prince_type
        goods_item.icons = icons
        goods_item.commit_link = commit_link
        goods_list.append(goods_item)
    except BaseException as e:
      succeed = False
      logging.error("Error While Getting Goods List : " + str(e))
    # 返回结果
    return (succeed, goods_list)

  def __handle_goods_result(self, goods_list):
    '''处理商品信息爬取结果'''
    # 首先将商品列表信息更新数据库当中
    db = DB()
    db.batch_insert_or_update_goods(goods_list)
    # 然后将价格历史记录到 Redis 中
    redis = Redis()
    redis.add_goods_price_histories(goods_list)

  def test(self):
    '''测试入口'''
    self.__crawl_jd_page("https://list.jd.com/list.html?cat=670%2C686%2C689&page=100")

class Goods_Item(object):
  '''产品信息包装类'''
  def __init__(self):
    super().__init__()
    self.name = ''        # 名称
    self.promo = ''       # 提示
    self.link = ''        # 链接
    self.image = ''       # 图片链接
    self.price = 0        # 价格
    self.price_type = ''  # 价格类型
    self.icons = ''       # 标签
    self.commit_link = '' # 评论链接
    
    self.channel_id = 0   # 父级信息：分类 id
    self.channel = ''     # 父级信息：分类 name

  def __str__(self):
    return self.name + " " + self.price + " " + self.icons

if __name__ == "__main__":
  '''调试入口'''
  config = Config()
  config.config_logging()
  gd = JDGoods()
  gd.test()
