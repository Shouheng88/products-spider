#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from utils import get_current_timestamp

class GoodsItem(object):
  '''产品信息包装类'''
  def __init__(self, name='', promo='', link='', image='', price=0, price_type='', icons='', venid=''):
    super().__init__()
    self.name = name              # 名称
    self.promo = promo            # 提示
    self.link = link              # 链接
    self.image = image            # 图片链接
    self.price = price            # 价格
    self.price_type = price_type  # 价格类型
    self.icons = icons            # 标签
    self.venid= venid             # 商家 id

    self.sku_id = ''
    self.product_id = ''
    self.comment_count = 0
    self.average_score = 0
    self.good_rate = 0    # 数值扩大 100 倍
    self.comment = None

    self.channel_id = 0   # 父级信息：分类 id
    self.channel = ''     # 父级信息：分类 name

  def __str__(self):
    return "Goods: (%s, %s, %s, %s, %s, %s)" % (self.name, self.price, self.icons, self.sku_id, self.product_id, self.comment)

  def get_comment_detail(self):
    '''获取对应的评论的 json 字符串'''
    ret = ''
    if self.comment != None:
      ret = self.comment.to_json()
    return ret

  def get_value_of_filed_name(self, column_name):
    '''根据数据库列的名称取出对应的字段'''
    if column_name == 'name':
      return self.name
    if column_name == 'promo':
      return self.promo
    if column_name == 'link':
      return self.link
    if column_name == 'image':
      return self.image
    if column_name == 'price':
      return self.price
    if column_name == 'price_type':
      return self.price_type
    if column_name == 'icons':
      return self.icons
    if column_name == 'channel_id':
      return self.channel_id
    if column_name == 'channel':
      return self.channel
    if column_name == 'updated_time':
      return get_current_timestamp()
    if column_name == 'sku_id':
      return self.sku_id
    if column_name == 'product_id':
      return self.product_id
    if column_name == 'comment_count':
      return self.comment_count
    if column_name == 'average_score':
      return self.average_score
    if column_name == 'good_rate':
      return self.good_rate
    if column_name == 'comment_detail':
      return self.get_comment_detail()
    if column_name == 'vender_id':
      return self.venid

class GoodsComment(object):
  '''商品的评价封装类'''
  def __init__(self, defaultGood, good, general, poor, video, after, oneYear, show):
    super().__init__()
    self.defaultGoodCount = defaultGood
    self.goodCount = good
    self.generalCount = general
    self.poorCount = poor
    self.videoCount = video
    self.afterCount = after
    self.oneYear = oneYear
    self.showCount = show

  def __str__(self):
    return "Comment: (%d, %d, %d, %d, %d, %d, %d, %d)" % (self.defaultGoodCount, self.goodCount, self.generalCount, self.poorCount, self.videoCount, self.afterCount, self.oneYear, self.showCount)

  def to_json(self):
    '''获取对应的 json 字符串'''
    return json.dumps(self, default=goodsComment2Dict)

def goodsComment2Dict(comment):
  return {
    "defaultGoodCount": comment.defaultGoodCount,
    "goodCount": comment.goodCount,
    "generalCount": comment.generalCount,
    "poorCount": comment.poorCount,
    "videoCount": comment.videoCount,
    "afterCount": comment.afterCount,
    "oneYear": comment.oneYear,
    "showCount": comment.showCount  
  }

class GoodsParams(object):
  '''产品的品牌信息，这个是解析结果的包装对象'''
  def __init__(self):
    super().__init__()
    self.brand = ''
    self.brand_url = ''
    self.store = ''
    self.store_url = ''
    self.parameters = [] # [(), (), ...] 一个列表，每个元素是一个字典
    self.packages = {} # 是一个哈希表 {g1: [(), (), ...], g2:[], ...}

  def __str__(self):
      return 'Brand:' + self.brand + '(' + self.brand_url + ')\nStore:' + self.store + '(' + self.store_url + ')\nParameters:' + str(self.parameters) + '\nPackages:'  + str(self.packages)

class BrandItem(object):
  '''商品的品牌信息'''
  def __init__(self):
    super().__init__()
    self.name = ''          # 品牌名称
    self.data_initial = ''  # 首字母
    self.logo = ''          # 品牌 Logo
    self.link = ''          # 品牌链接
    self.dispaly_order = 0  # 品牌的顺序
    self.channel_id = 0     # 品类信息
    self.channel = ''

  def get_value_of_filed_name(self, column_name):
    '''根据数据库列的名称获取对应的字段信息'''
    if column_name == 'name':
      return self.name
    if column_name == 'data_initial':
      return self.data_initial
    if column_name == 'logo':
      return self.logo
    if column_name == 'link':
      return self.link
    if column_name == 'updated_time':
      return get_current_timestamp()

class Category(object):
  '''分类信息封装'''
  def __init__(self):
    self.name = ''            # 品类名称
    self.link = ''            # 链接地址
    self.treepath = ''        # 搜索路径
    self.parent_id = 0        # 父类品类
    self.jdurl = ''           # 京东链接
    self.tburl = ''           # 淘宝链接
    self.max_page_count = 0   # 最大检索的页数
    self.display_order = 0    # 展示的顺序
    self.children = {}
