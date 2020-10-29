#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from xml.dom.minidom import parse
import xml.dom.minidom
import logging
import json
import xlwt
import os
import codecs
import xlrd
import pymysql
import pymysql.cursors
import traceback
from redis import StrictRedis, ConnectionPool

from models import GoodsItem
from utils import *
from config import *

class JsonOperator(object):
    # 初始化
    def __init__(self):
        pass

    # 写入 json 到文件
    def write_json(self, fname, json_obj):
        json_str = json.dumps(json_obj)
        with open(fname, "w") as f:
            f.write(json_str)

    # 从文件读取 json 字符串
    def read_json(self, fname):
        with open(fname, "r") as f:
            return json.load(f)

class ExcelOperator(object):
    # 初始化
    def __init__(self):
        pass

    # 写 Excel
    def write_excel(self, sheet_name, dist, file):
        # 创建 Excel 的工作簿
        book = xlwt.Workbook(encoding='utf-8', style_compression=0)
        sheet = book.add_sheet(sheet_name, cell_overwrite_ok=True)
        # dist : {"a":[], "b":[], "c": []}
        row_count = 0
        col_count = 0
        for k, v in dist.items():
            sheet.write(row_count, col_count, k)
            for item in v:
                row_count = row_count + 1
                sheet.write(row_count, col_count, item)
            col_count = col_count + 1
            row_count = 0
        book.save(file)

    # 读取 Excel，{sheet_name:[[col 1], [col 2], []]}
    def read_excel(self, xlsfile):
        dists = {}
        book = xlrd.open_workbook(xlsfile)
        size = len(book.sheet_names())
        for i in range(size):
            sheet = book.sheet_by_index(i)
            dists[sheet.name] = self.__read_sheet(sheet)
        return dists

    # 读取 Excel Sheet
    def __read_sheet(self, sheet):
        col_list = []
        # 按列遍历
        for col in range(0, sheet.ncols):
            col_list.append([])
            # 按行遍历
            for row in range(0, sheet.nrows):
                value = sheet.cell_value(row, col)
                col_list[col].append(value)
        return col_list

class DBOperator(object):
    def __init__(self):
        super().__init__()

    def update_goods_parames(self, goods_item, goods_params):
        '''更新产品的参数信息'''
        goods_id = goods_item[GOODS_ID_ROW_INDEX]
        lock_version = goods_item[GOODS_LOCK_VERSION_ROW_INDEX]
        # 判断需要更新的字段，防止因为没有抓取到数据覆盖了之前爬取的结果
        fileds_to_update = {}
        if goods_params.brand != '':
            fileds_to_update['brand'] = goods_params.brand.replace("'", "\\'")
        if goods_params.brand_url != '':
            fileds_to_update['brand_link'] = goods_params.brand_url
        if goods_params.store != '':
            fileds_to_update['store'] = goods_params.store.replace("'", "\\'")
        if goods_params.store_url != '':
            fileds_to_update['store_link'] = goods_params.store_url
        if len(goods_params.parameters) != 0:
            text = str(goods_params.parameters).replace("'", '"')
            if len(text) < MAX_LENGTH_OF_GOODS_PARAMETERS: # 当文字长度高于 3000 的时候就不赋值了，以保证 sql 执行不会出错
                fileds_to_update['parameters'] = text
        if len(goods_params.packages) != 0:
            text = str(goods_params.packages).replace("'", '"')
            if len(text) < MAX_LENGTH_OF_GOODS_PACKAGES: # 同上
                fileds_to_update['packages'] = text
        if len(fileds_to_update) == 0:
            logging.warning("Trying to Update But Nothing Need to Update.")
            return False
        # 拼接 sql
        sql_parts = []
        for name, value in fileds_to_update.items():
            sql_parts.append("%s = '%s'," % (name, value))
        sql_part = ''.join(sql_parts) + ' updated_time = ' + str(get_current_timestamp())
        sql = "UPDATE gt_item SET %s WHERE id = %s" % (sql_part, goods_id)
        succeed = True
        try:
            con = self.connect_db()
            cur = con.cursor()
            ret = cur.execute(sql)
            if ret == 0:
                succeed = False
                logging.error("Failed To Update Goods Item.")
            else:
                con.commit()
        except BaseException as e:
            succeed = False
            logging.error("Failed While Insert:\n%s" % traceback.format_exc())
            logging.error("SQL:\n%s" % sql)
            con.rollback()
        finally:
            cur.close()
            con.close()
        return succeed

    def next_page_to_handle_prameters(self, source: int, page_size: int, start_id: int, type_index, group_count):
        '''从商品列表中取出下一个需要解析的商品，设计的逻辑参考品类爬取相关的逻辑'''
        # 查询的时候增加 parameters 条件，也即只有当参数为空的时候才爬取，每个产品只爬取一次
        sql = ("SELECT * FROM gt_item WHERE \
            parameters is null and \
            store is null and \
            brand is null and \
            price != -1 and \
            id > %s and \
            id %% %s = %s and \
            source = %s \
            ORDER BY id LIMIt %s") % (start_id, group_count, type_index, source, page_size) # 每次取出来 5 个数据吧
        con = self.connect_db()
        cur = con.cursor()
        rows = None
        try:
            cur.execute(sql)
            rows = cur.fetchall()
        except BaseException as e:
            logging.error('Error while getting next goods to handle:\n%s' % traceback.format_exc())
            logging.error('SQL:\n%s' % sql)
        finally:
            cur.close()
            con.close()
        return rows

    def next_goods_page_without_source(self, page_size: int, start_id: int):
        '''按页取商品数据'''
        sql = ("SELECT * FROM gt_item WHERE \
            price != -1 \
            AND id > %s \
            ORDER BY id LIMIT %s") % (start_id, page_size)
        con = self.connect_db()
        cur = con.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows

    def next_goods_page_for_icons(self, source: int, icons, page_size: int, start_id: int, type_index: int, group_count:int):
        """
        从商品列表中读取一页数据来查询商品的价格信息，这里查询到了数据之后就直接返回了，
        处理数据的时候也不会进行加锁和标记.
        """
        sql_like_parts = []
        for filter in icons: # 增加 icons 条件进行过滤，只对折扣商品进行检索
            sql_like_parts.append("icons LIKE '%" + filter +  "%'")
        sql_like = ' OR '.join(sql_like_parts)
        sql = ("SELECT * FROM gt_item WHERE \
            price != -1 \
            AND source = %s \
            AND id > %s \
            AND id %% %s = %s \
            AND (%s) \
            ORDER BY id LIMIT %s") % (source, start_id, group_count, type_index, sql_like, page_size)
        logging.debug(sql)
        con = self.connect_db()
        cur = con.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows

    def next_goods_page_of_channels(self, channel_id_list, page_size: int, start_id: int):
        """
        从商品列表中读取一页数据来查询商品的价格信息，这里查询到了数据之后就直接返回了，
        处理数据的时候也不会进行加锁和标记.
        """
        channel_ids_str = []
        for channel_id in channel_id_list:
            channel_ids_str.append(str(channel_id))
        channel_ids = ','.join(channel_ids_str)
        # TODO 不同的服务器上面 channel id 不同，所以不应该使用 channel id 作为标志
        sql = ("SELECT * FROM gt_item WHERE \
            price != -1 \
            AND channel_id in (%s) \
            AND id > %s \
            ORDER BY id LIMIT %s") % (channel_ids, start_id, page_size)
        con = self.connect_db()
        cur = con.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows

    def execute(self, sql):
        ret = None
        try:
            # logging.debug("execute(): %s\n" % sql)
            con = self.connect_db()
            cur = con.cursor()
            ret = cur.execute(sql)
            con.commit()
        except BaseException as e:
            con.rollback()
            logging.error('Failed fetchall(): %s\n' % traceback.format_exc())
            logging.error('SQL:%s' % sql)
        finally:
            cur.close()
            con.close()
        return ret

    def executemany(self, sql, values: tuple):
        succeed = True
        if len(values) == 0:
            logging.info("executemany(): Empty values")
            return succeed
        try:
            # logging.debug("executemany(): %s\n" % sql)
            con = self.connect_db()
            cur = con.cursor()
            cur.executemany(sql, tuple(values))
            con.commit()
        except BaseException as e:
            succeed = False
            con.rollback()
            logging.error("Failed While executemany():\n%s" % traceback.format_exc())
            logging.error("SQL:\n%s" % sql)
        finally:
            cur.close()
            con.close()
        return succeed

    def fetchall(self, sql):
        rows = None
        try:
            # logging.debug("fetchall(): %s\n" % sql)
            con = self.connect_db()
            cur = con.cursor(cursor=pymysql.cursors.DictCursor)
            cur.execute(sql)
            rows = cur.fetchall()
        except BaseException as e:
            logging.error('Failed fetchall(): %s\n' % traceback.format_exc())
            logging.error('SQL:%s' % sql)
        finally:
            cur.close()
            con.close()
        return rows

    def connect_db(self):
        '''链接数据库'''
        return pymysql.connect(host=config.db.host, port=config.db.port, \
            user=config.db.user, password=config.db.password, database=config.db.database)

class RedisOperator(object):
    '''Redis 操作的封装类'''
    def __init__(self):
        super().__init__()
        self.connected = False
        self.r: StrictRedis = None

    def add_goods_price_histories(self, goods_list):
        '''添加商品的历史价格信息'''
        self._connect_redis()
        today = get_timestamp_of_today_start()
        rows = dBOperator.get_goods_list_from_database(goods_list)
        for row in rows:
            goods_id = row[GOODS_ID_ROW_INDEX]
            price = row[GOODS_PRICE_ROW_INDEX]
            name = 'GOODS:PRICE:HISTORY:%d' % goods_id
            self.r.hset(name, str(today), price)

    def add_prices(self, goods_item, price_map):
        '''
        添加历史价格
        添加历史价格，不过有个问题，这里价格是统计了折扣之后的结果，所以可能有问题，
        这里计算出来的价格也就当作一个补充吧，即项目正式开启爬虫之前进行的数据抓取
        '''
        goods_id = goods_item[GOODS_ID_ROW_INDEX]
        name = 'GOODS:PRICE:HISTORY:%d' % goods_id
        self._connect_redis()
        for d,p in price_map.items():
            price = self.r.hget(name, str(d))
            if price == None:
                self.r.hset(name, str(d), p)

    def get_jd_type_index(self, type_name):
        '''获取京东的参数的索引'''
        self._connect_redis()
        index = self.r.get('jd_type_index_%s' % type_name)
        if index == None:
            index = 0
        return index

    def increase_jd_type_index(self, type_name):
        '''京东的参数索引+1'''
        self._connect_redis()
        index = self.r.get('jd_type_index_%s' % type_name)
        if index == None:
            index = 0
        self.r.set('jd_type_index_%s' % type_name, index+1)

    def _connect_redis(self):
        '''连接 Redis'''
        if not self.connected:
            self.connected = True
        pool = ConnectionPool(host=config.redis.host, port=config.redis.port,\
            db=config.redis.db, password=config.redis.password)
        self.r = StrictRedis(connection_pool=pool)

redisOperator = RedisOperator()

dBOperator = DBOperator()
