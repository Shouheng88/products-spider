#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from utils import *

class GoodsItem(object):
  '''产品信息包装类'''
  def __init__(self, name='', promo='', link='', image='', price=0, price_type='', icons='', vender_id=''):
    super().__init__()
    self.id = None
    self.name = name              # 名称
    self.promo = promo            # 提示
    self.link = link              # 链接
    self.image = image            # 图片链接
    self.price = price            # 价格
    self.price_type = price_type  # 价格类型
    self.icons = icons            # 标签
    self.source = None            # 来源，0 京东，1 淘宝，2 天猫
    self.parameters = None
    self.packages = None

    self.sku_id = ''
    self.product_id = ''          # prodcut id *
    self.vender_id = vender_id    # 商家 id
    self.comment_count = 0        # 评论数量 *
    self.average_score = 0        # 平均得分 *
    self.good_rate = 0            # 好评百分比，诸如 0.98，综合评价 *
    self.comment_detail = None
    self.store = None
    self.store_link = None
    self.brand = None
    self.brand_link = None
    self.channel_id = None        # 父级信息：分类 id
    self.channel = None           # 父级信息：分类 name

    self.handling_time = None
    self.updated_time = None
    self.created_time = None

  def __str__(self):
    return "Goods: (%s, %s, %s, %s, %s, %s, %s, %s,\
      %s, %s, %s, %s, %s, %s,\
      %s, %s, %s)" % (self.name, self.promo, self.link, self.image, self.price, \
        self.price_type, self.icons, self.venid, self.sku_id, self.product_id, \
        self.comment_count, self.average_score, self.good_rate, self.comment_detail, \
        self.channel_id, self.channel, self.source)

class GoodsComment(object):
  '''商品的评价封装类'''
  def __init__(self, defaultGood, good, general, poor, video, after, oneYear, show):
    super().__init__()
    self.defaultGoodCount = defaultGood # 默认好评
    self.goodCount = good       # 好评数量
    self.generalCount = general # 中评数量
    self.poorCount = poor       # 差评数量
    self.videoCount = video     # 视频晒单数量
    self.afterCount = after     # 追评
    self.oneYear = oneYear      # 一年之后评论
    self.showCount = show       # show count
                
  def __str__(self):
    return "Comment: (%d, %d, %d, %d, %d, %d, %d, %d)" % (self.defaultGoodCount, \
      self.goodCount, self.generalCount, self.poorCount, self.videoCount, \
      self.afterCount, self.oneYear, self.showCount)

  def to_json(self):
    '''获取对应的 json 字符串'''
    return json.dumps(self, default=goodsComment2Dict)

class GoodsParams(object):
  '''产品的品牌信息，这个是解析结果的包装对象'''
  def __init__(self):
    super().__init__()
    self.brand = ''
    self.brand_url = ''
    self.store = ''
    self.store_url = ''
    self.parameters = {} # [(), (), ...] 一个列表，每个元素是一个字典
    self.packages = {} # 是一个哈希表 {g1: [(), (), ...], g2:[], ...}

  def __str__(self):
      return 'Brand:' + self.brand + '(' + self.brand_url + ')\nStore:' + self.store + \
        '(' + self.store_url + ')\nParameters:' + str(self.parameters) \
        + '\nPackages:'  + str(self.packages)

class Brand(object):
  '''商品的品牌信息'''
  def __init__(self, name, data_initial, logo, link, dispaly_order):
    super().__init__()
    self.id = None
    self.name = name                    # 品牌名称
    self.data_initial = data_initial    # 首字母
    self.logo = logo                    # 品牌 Logo
    self.link = link                    # 品牌链接
    self.dispaly_order = dispaly_order  # 品牌的顺序
    self.channel_id = 0                 # 品类信息
    self.channel = ''
    self.remark = None
    self.lock_version = None
    self.updated_time = None
    self.created_time = None

class Category(object):
  '''分类信息封装'''
  def __init__(self, name='', link='', treepath='', parent_id=0, \
    jdurl='', tburl='', max_page_count=0, display_order=0, cat=''):
    self.name = name                      # 品类名称
    self.link = link                      # 链接地址
    self.treepath = treepath              # 搜索路径
    self.parent_id = parent_id            # 父类品类
    self.jdurl = jdurl                    # 京东链接
    self.tburl = tburl                    # 淘宝链接
    self.max_page_count = max_page_count  # 最大检索的页数
    self.display_order = display_order    # 展示的顺序
    self.cat = cat                        # 品类信息
    self.children = {}

  def __str__(self):
      return ' ' + self.name + ' ' + self.cat + ' ' + str(self.children)

class Channel(object):
  def __init__(self):
    super().__init__()
    self.id = None
    self.name = None
    self.parent_id = None 
    self.cat = None
    self.treepath = None
    self.jdurl = None
    self.tburl = None
    self.max_page_count = None
    self.handling_time = None
    self.display_order= None
    self.remark = None
    self.lock_version = None
    self.updated_time = None
    self.created_time = None

class Discount(object):
  '''商品的折扣信息'''
  def __init__(self, goods_id, batch_id, quota, discount, start_time, end_time):
    super().__init__()
    self.id = None
    self.goods_id = goods_id
    self.batch_id = batch_id
    self.quota = quota            # 满足多少金额的时候可以使用
    self.discount = discount      # 真实的折扣信息
    self.start_time = start_time
    self.end_time = end_time
    self.remark = None
    self.lock_version = None
    self.updated_time = None
    self.created_time = None

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
