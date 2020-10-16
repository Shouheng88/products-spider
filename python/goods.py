#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
import re
from bs4 import BeautifulSoup
import traceback
import json

from utils import *
from models import *
from config import *
from operators import redisOperator as redis
from operators import dBOperator as db

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
    while True:      
      channel = db.next_channel_to_handle()
      # 没有需要爬取的任务了
      if channel == None:
        break
      # 对任务进行解析
      job_no = job_no + 1
      logging.info("Crawling Channel (%d)：%s" % (job_no, str(channel)))
      # 爬取某个品类的数据
      self.__crawl_jd_channel(channel)
      # 将指定的品类标记为完成
      db.mark_channel_as_done(channel)
    # 任务完成！！！！！撒花！！！！!
    # *★,°*:.☆(￣▽￣)/$:*.°★* 
    logging.info("Channel Scrawl Job Finished!!!")

  def __crawl_jd_channel(self, channel):
    '''爬取指定的品类的所有的信息'''
    channel_url = channel[CHANNEL_JD_URL_ROW_INDEX]
    channel_id = channel[CHANNEL_ID_ROW_INDEX]
    channel_name = channel[CHANNEL_NAME_ROW_INDEX]
    # TODO 要爬取的最大的页数，数据库中也有一个对应的记录，输出完整的任务信息 
    # 抓取分类的信息，也就是第一页的信息
    (succeed, max_page) = self.__crawl_jd_page(channel_url, channel, True)
    page_count = 1 # 已经抓取的页数
    for page_num in range(1, min(max_page, JD_MAX_SEARCH_PAGE)):
      page_url = self.__get_page_url_of_page_number(channel_url, page_num)
      # step 1: 从页面上解析最大的页数数据，并且根据该页数的限制进行只爬指定的页数
      (succeed, _max_page) = self.__crawl_jd_page(page_url, channel, False)
      page_count = page_count + 1
      if succeed:
        logging.info("Succeed To Scrawl Channel %s [%d]," % (channel_name, page_count))
      else:
        logging.error("Failed To Scrawl Channel %s [%d]," % (channel_name, page_count))

  def __get_page_url_of_page_number(self, jdurl, page_num):
    '''获取指定品类的指定的页码，用来统一实现获取指定的页码的地址的逻辑'''
    return jdurl + "&page=" + str(page_num)

  def __crawl_jd_page(self, page_url, channel, first_page):
    '''京东商品列表信息抓取，最大的页码、产品详情等基础信息'''
    channel_id = channel[CHANNEL_ID_ROW_INDEX]
    channel_name = channel[CHANNEL_NAME_ROW_INDEX]
    html = requests.get(page_url, headers=REQUEST_HEADERS).text
    soup = BeautifulSoup(html, "html.parser")
    (succeed1, max_page) = self.__crawl_jd_max_page(soup)
    (succeed2, goods_list) = self.__crawl_jd_goods_list(soup)
    (succeed3, brand_list) = self.__crawl_jd_brand_list(soup)
    # 为爬取到的结果添加分类信息
    for goods_item in goods_list:
      goods_item.channel_id = channel_id
      goods_item.channel = channel_name
    for brand_item in brand_list:
      brand_item.channel_id = channel_id
      brand_item.channel = channel_name
    # 持久化处理爬取结果
    if succeed2:
      # 爬取京东商品的评论信息
      self.__crawl_jd_comment_info(goods_list)
      # 首先将商品列表信息更新数据库当中
      db.batch_insert_or_update_goods(goods_list)
      # 然后将价格历史记录到 Redis 中，Redis 的操作应该放在 DB 之后，因为我们要用到数据库记录的主键
      redis.add_goods_price_histories(goods_list)
    if succeed3 and first_page:
      # 对于每个品类，只在爬取第一页的时候更新品牌信息，减少服务器压力
      db.batch_insert_or_update_brands(brand_list)
    return (succeed1 and succeed2, max_page)

  def __crawl_jd_max_page(self, soup):
    '''解析京东的最大页数'''
    # 解析最大页码
    succeed = True
    max_page = JD_MAX_SEARCH_PAGE
    try:
      pageText = soup.find(id="J_topPage").find("span").text
      index = pageText.find("/")
      max_page = int(pageText[(index+1):])
    except BaseException as e:
      logging.error("Error While Getting Page Count : %s " % traceback.format_exc())
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
        vid = safeGetAttr(p_img.find(tag_has_venid_attr), "data-venid", "")
        prince_type = safeGetText(p_price.find("em"), "")
        price = safeGetText(p_price.find("i"), "-1")
        promo = safeGetAttr(p_name.find("a"), "title", "")
        name = safeGetText(p_name.find("a").find("em"), "")
        commit_link = safeGetAttr(p_commit.find("a"), "href", "")
        icons = safeGetText(p_icons.find("i"), "")
        # 组装产品信息，价格要扩大 100 倍
        goods_item = GoodsItem(name, promo, url, img, int(float(price)*100), prince_type, icons, vid)
        goods_list.append(goods_item)
    except BaseException as e:
      succeed = False
      logging.error("Error While Getting Goods List : %s" % traceback.format_exc())
    # 返回结果
    return (succeed, goods_list)

  def __crawl_jd_brand_list(self, soup):
    '''从页面中解析产品的品牌数据'''
    succeed = True
    brand_list = []
    try:
      display_order = 0
      brand_list_tags = soup.find_all(id=re.compile("brand")) # 所有的包含 id 包含 brand 的标签，即品牌
      for brand_list_tag in brand_list_tags:
        display_order = display_order + 1
        data_initial = safeGetAttr(brand_list_tag, "data-initial", "")
        name = safeGetAttr(brand_list_tag.find("a"), "title", "")
        link = safeGetAttr(brand_list_tag.find("a"), "href", "")
        logo = safeGetAttr(brand_list_tag.find("img"), "src", "")
        # 组装品牌信息
        brand_item = BrandItem()
        brand_item.name = name
        brand_item.data_initial = data_initial
        brand_item.logo = logo
        brand_item.link = link
        brand_item.dispaly_order = display_order
        brand_list.append(brand_item)
    except BaseException as e:
      succeed = False
      logging.error("Error While Getting Brand List : %s " % traceback.format_exc())
    # 返回结果
    return (succeed, brand_list)

  def __crawl_jd_comment_info(self, goods_list):
    '''爬取京东商品的评论信息'''
    # 组装数据
    sku_ids = ''
    sku_id_map = {}
    for idx in range(0, len(goods_list)):
      goods_item = goods_list[idx]
      last_split = goods_item.link.rfind("/")
      last_point = goods_item.link.rfind(".")
      if last_point != None and last_split != None:
        sku_id = goods_item.link[(last_split+1):last_point]
        sku_id_map[sku_id] = goods_item
      sku_ids = sku_ids + sku_id
      if idx != len(goods_list)-1:
        sku_ids = sku_ids + ","
    if len(sku_ids) != 0:
      # 请求评论信息
      json_comments = requests.get("https://club.jd.com/comment/productCommentSummaries.action?referenceIds=" + sku_ids, headers=REQUEST_HEADERS).text
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
          goods_item.comment = goods_comment

  def test(self):
    '''测试入口'''
    self.__crawl_jd_page("https://list.jd.com/list.html?cat=670%2C686%2C689&page=100", (328, ""), True)

def tag_has_venid_attr(tag):
  return tag.has_attr('data-venid')

if __name__ == "__main__":
  '''调试入口'''
  config = GlobalConfig()
  config.config_logging()
  gd = JDGoods()
  gd.test()
