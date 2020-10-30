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
from typing import *

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

    def execute(self, sql):
        ret = con = cur = None
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
            self._safe_closs(cur)
            self._safe_closs(con)
        return ret

    def executemany(self, sql, values: tuple):
        succeed = True
        if len(values) == 0:
            logging.info("executemany(): Empty values")
            return succeed
        con = cur = None
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
            self._safe_closs(cur)
            self._safe_closs(con)
        return succeed

    def fetchall(self, sql):
        rows = con = cur = None
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
            self._safe_closs(cur)
            self._safe_closs(con)
        return rows

    def _safe_closs(self, target):
        if target != None:
            target.close()

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

    def add_goods_price_histories(self, goods_list: List[GoodsItem]):
        '''添加商品的历史价格信息'''
        self._connect_redis()
        today = str(get_timestamp_of_today_start())
        for goods_item in goods_list:
            name = 'GOODS:PRICE:HISTORY:%d' % goods_item.id
            self.r.hset(name, today, goods_item.price)

    def add_prices(self, goods_item: GoodsItem, price_map: Dict[int, int]):
        '''
        添加历史价格
        添加历史价格，不过有个问题，这里价格是统计了折扣之后的结果，所以可能有问题，
        这里计算出来的价格也就当作一个补充吧，即项目正式开启爬虫之前进行的数据抓取
        '''
        self._connect_redis()
        name = 'GOODS:PRICE:HISTORY:%d' % goods_item.id
        for d, p in price_map.items():
            price = self.r.hget(name, str(d))
            if price == None:
                self.r.hset(name, str(d), p)

    def get_cursor_of_task(self, task_name: str, days_span: int = 2):
        '''获取任务的 id '''
        self._connect_redis()
        cursor = self.r.get('TASK:CRAWL:CURSOR:%s' % task_name) # 获取当前的游标
        if cursor == None:
            current_cursor = 0
        else:
            cursor = int(cursor)
            # 如果之前有没有完成的任务，先完成那些任务
            for c in range(max(0, cursor-20), cursor): 
                is_done = bool(self.r.getbit('TASK:CRAWL:DONE:%s' % task_name, c))
                if not is_done:
                    handling_time = int(self.r.hget('TASK:CRAWL:TIME:%s' % task_name, str(c)))
                    if (get_current_timestamp()-handling_time)//(24*60*60*days_span) > 0: # 处理了两天没有完成
                        self.r.hset('TASK:CRAWL:TIME:%s' % task_name, str(c), str(get_current_timestamp()))
                        return c
            current_cursor = cursor+1
        # 没有未完成的任务
        self.r.set('TASK:CRAWL:CURSOR:%s' % task_name, str(current_cursor))
        self.r.hset('TASK:CRAWL:TIME:%s' % task_name, str(current_cursor), str(get_current_timestamp()))
        return current_cursor

    def mark_task_as_done(self, task_name: str, cursor: int):
        '''标记指定的任务为完成状态'''
        self._connect_redis()
        self.r.setbit('TASK:CRAWL:DONE:%s' % task_name, cursor, True)

    def get_jd_type_index(self, type_name: str):
        '''获取京东的参数的索引'''
        self._connect_redis()
        index = self.r.get('jd_type_index_%s' % type_name)
        if index == None:
            index = 0
        return index

    def increase_jd_type_index(self, type_name: str):
        '''京东的参数索引+1'''
        self._connect_redis()
        index = self.r.get('jd_type_index_%s' % type_name)
        if index == None:
            index = 0
        self.r.set('jd_type_index_%s' % type_name, (index+1))

    def _connect_redis(self):
        '''连接 Redis'''
        if not self.connected:
            self.connected = True
        pool = ConnectionPool(host=config.redis.host, port=config.redis.port,\
            db=config.redis.db, password=config.redis.password)
        self.r = StrictRedis(connection_pool=pool)

redisOperator = RedisOperator()

dBOperator = DBOperator()
