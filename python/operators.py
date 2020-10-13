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

from utils import TimeHelper as TH
from config import CHANNEL_ID_ROW_INDEX as id_idx
from config import CHANNEL_TREEPATH_ROW_INDEX as treepath_idx
from config import CHANNEL_LOCK_VERSION_ROW_INDEX as lock_version_idx

class XmlOperator:
    # 初始化
    def __init__(self):
        pass

class JsonOperator:
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

class ExcelOperator:
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
    '''
    目前这个数据库的设计方案是按照多进程来设计，如果多线程的话，除非你在应用内部切换 ip
    否则还是运行在同一个 ip 地址内。容易因为访问量过大被 block. 而如果按照多进程的方案
    进行设计，那么我们可以自由地进行横向的拓展。甚至，我们可以通过服务器暴露任务给客户端
    来在客户端上面实现爬虫之后将获取的数据提交到服务器上面。也就是，使用多进程的设计方案
    拓展起来会容易得多。
    '''
    def __init__(self):
        super().__init__()

    def next_channel_to_handle(self):
        '''获取下一个需要处理的品类，如果返回的结果是 None 就表示这个品类的数据已经爬取完了'''
        # 要求：
        # 1. updated_time 在今天之前，也就是每天最多爬取一次数据
        # 2. handling_time 在现在 30 分钟之前, 如果 30 分钟还没有完成，说明任务失败了
        # 3. 按照 updated_time 低到高排序，也就是上次完成时间
        th = TH()
        today_starter = th.get_timestamp_of_today_start()
        handling_before = th.get_current_timestamp() - th.get_quartern_seconds()
        sql = ("SELECT * FROM gt_channel WHERE updated_time < %s and handling_time < %s ORDER BY updated_time")
        val = (today_starter, handling_before)
        con = self.connect_db()
        cur = con.cursor()
        cur.execute(sql, val)
        rows = cur.fetchall()
        # 拿到了所有的分类之后进行处理
        channel = None
        for row in rows:
            # 1. 对品来进行过滤，只需要对三级品类进行过滤，包含 两个 | 的时候代表三级品类
            if len(row[treepath_idx].split("|")) == 3:
                row_id = row[treepath_idx] # 记录 id
                lock_version = row[lock_version_idx] # 乐观锁
                # 2. 对数据库进行修改，标记完成时间，同时乐观锁 +1
                ret = cur.execute("UPDATE gt_channel SET handling_time = %s, lock_version = %s WHERE id = %s and lock_version = %s", 
                    (th.get_current_timestamp(), lock_version+1, row_id, lock_version))
                # 3. 更新成功，表示已经取到任务
                if ret == 1:
                    channel = row
                    break
        con.commit() # 提交事务
        cur.close()
        con.close()
        return channel

    def mark_channel_as_done(self, channel):
        '''
        将指定的品类标记为完成状态：
        1. 将 updated_time 设置为当前的时间
        2. 将 lock_version + 1
        3. 通过 lock_version 来做判断，防止因为任务超时，导致任务数据被其他人修改掉
        '''
        pass

    def batch_insert_or_update_goods(self, goods_list):
        '''批量向数据库当中插入数据或者更新数据当中的记录'''
        pass

    def write_channel(self, category):
        '''将各个分类数据写入到数据库种'''
        con = self.connect_db()
        cur = con.cursor()
        row_id = -1
        try:
            # 先插入到数据库中，获取到记录的 id 之后再更新记录的 treepath 字段
            sql = "INSERT INTO gt_channel (\
                name, \
                treepath, \
                parent_id, \
                jdurl, \
                tburl, \
                max_page_count, \
                handling_time, \
                display_order, \
                lock_version, \
                updated_time, \
                created_time) VALUES (%s, %s, %s, %s, %s, %s, 0, %s, 0, 0, unix_timestamp(now()))"
            # 将处理时间默和最后更新 (完成时间) 默认设置为 0
            val = (category.name, category.treepath, category.parent_id, 
                category.jdurl, category.tburl, category.max_page_count, category.display_order)
            cur.execute(sql, val)
            row_id = cur.lastrowid
            # 再更新数据的 treepath 字段
            if len(category.treepath) == 0:
                category.treepath = str(row_id)
            else:
                category.treepath = category.treepath + "|" + str(row_id)
            cur.execute("UPDATE gt_channel SET treepath = %s WHERE id = %s", (category.treepath, row_id))
            con.commit()
        except Exception as e:
            con.rollback()
            logging.exception('Insert operation error')
        finally:
            cur.close()
            con.close()
        return row_id

    def connect_db(self):
        '''链接数据库'''
        return pymysql.connect(host='localhost', port=***REMOVED***, user='root',password='***REMOVED***', database='***REMOVED***')

class RedisOperator(object):
    '''Redis 操作的封装类'''
    def __init__(self):
        super().__init__()

    def add_goods_price_histories(self, goods_list):
        '''添加商品的历史价格信息'''
        pass