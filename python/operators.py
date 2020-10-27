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
        # 2. handling_time 在现在 2 分钟之前, 如果 2 分钟还没有完成，说明任务失败了
        # 3. 按照 updated_time 低到高排序，也就是上次完成时间
        today_starter = get_timestamp_of_today_start()
        handling_before = get_current_timestamp() - get_seconds_of_minutes(CHANNEL_HANDLE_TIMEOUT_IN_MINUTE)
        sql = ("SELECT * FROM gt_channel WHERE updated_time < %s AND handling_time < %s ORDER BY updated_time")
        val = (today_starter, handling_before)
        con = self.connect_db()
        cur = con.cursor()
        channel = None
        try:
            cur.execute(sql, val)
            rows = cur.fetchall()
            if len(rows) == 0:
                logging.info('Empty channel to handle.')
            # 拿到了所有的分类之后进行处理
            for row in rows:
                # 1. 对品来进行过滤，只需要对三级品类进行过滤，包含 两个 | 的时候代表三级品类
                if len(row[CHANNEL_TREEPATH_ROW_INDEX].split("|")) == 3:
                    row_id = row[CHANNEL_ID_ROW_INDEX] # 记录 id
                    lock_version = row[CHANNEL_LOCK_VERSION_ROW_INDEX] # 乐观锁
                    # 2. 对数据库进行修改，标记完成时间，同时乐观锁 +1
                    ret = cur.execute("UPDATE gt_channel SET handling_time = %s, lock_version = %s WHERE id = %s AND lock_version = %s", 
                        (get_current_timestamp(), lock_version+1, row_id, lock_version))
                    # 3. 更新成功，表示已经取到任务
                    if ret == 1:
                        channel = row
                        con.commit() # 提交事务
                        break
                    else:
                        logging.error('Failed to get next channel to handle.')
        except BaseException as e:
            logging.error('Failed to get next channel to handle: %s\n' % traceback.format_exc())
            con.rollback()
        finally:
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
        con = self.connect_db()
        cur = con.cursor()
        try:
            row_id = channel[CHANNEL_ID_ROW_INDEX] # 记录 id
            lock_version = channel[CHANNEL_LOCK_VERSION_ROW_INDEX] # 乐观锁
            ret = cur.execute("UPDATE gt_channel SET updated_time = %s, lock_version = %s WHERE id = %s AND lock_version = %s", 
                (get_current_timestamp(), lock_version+2, row_id, lock_version+1))
            if ret == 1:
                con.commit()
            else:
                logging.error("Failed to marking channel as done: %s\n" % traceback.format_exc())
        except BaseException as e:
            logging.error("Error while making channel as done: %s\n" % traceback.format_exc())
            con.rollback()
        finally:
            cur.close()
            con.close()

    def get_goods_list_from_database(self, goods_list):
        '''从数据库中查询指定的商品列表的商品信息'''
        rows = ()
        if len(goods_list) == 0:
            return rows
        link_list = []
        for idx in range(0, len(goods_list)):
            link = goods_list[idx].link
            link_list.append("'%s'" % link)
        val = ",".join(link_list)
        sql = "SELECT * FROM gt_item WHERE link IN (%s)" % val
        try:
            con = self.connect_db()
            cur = con.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
        except:
            logging.error("Failed When Fetching Goods From Database.")
            logging.error("SQL:\n%s" % sql)
        finally:
            cur.close()
            con.close()
        return rows

    def batch_insert_or_update_goods(self, goods_list):
        '''批量向数据库当中插入数据或者更新数据当中的记录'''
        links = {}
        for idx in range(0, len(goods_list)):
            link = goods_list[idx].link
            links[link] = goods_list[idx]
        succeed = True
        # 从数据库中按照连接查询商品列表
        rows = self.get_goods_list_from_database(goods_list)
        sql_map = {}
        try:
            con = self.connect_db()
            cur = con.cursor()
            # 检索到了数据 => 执行批量更新
            if len(rows) != 0:
                list_2_update = {} # 已经存在于数据库中的记录 => 用于更新
                for row in rows:
                    id = row[GOODS_ID_ROW_INDEX]
                    link = row[GOODS_LINK_ROW_INDEX]
                    if link in links:
                        existed_goods = links.pop(link) # 移除指定的 key
                        list_2_update[id] = existed_goods
                # 执行批量更新操作
                if len(list_2_update) != 0:
                    self.__batch_update_goods(list_2_update, cur, sql_map)
                    # 如果没有需要插入的记录，就提交事务，下面的逻辑走不到了
                    if len(links) == 0:
                        con.commit()
            # 没有检索到数据 => 执行插入操作
            if len(links) != 0:
                self.__batch_insert_goods(links, cur, sql_map)
                con.commit()
        except BaseException as e:
            succeed = False
            logging.error("Failed While Batch Insert: \n%s" % traceback.format_exc())
            logging.error("SQL:\n%s" % sql_map.get('sql'))
            # logging.error("VAL:\n%s" % sql_map.get('val'))
            con.rollback()
        finally:
            cur.close()
            con.close()
        return succeed

    def __batch_insert_goods(self, link_map, cur, sql_map):
        '''向数据库中批量插入记录'''
        values = []
        sql = "INSERT INTO gt_item (\
            name, promo, link, image, price, price_type, icons, channel_id,\
            channel, lock_version, updated_time, created_time, handling_time,source,\
            sku_id, product_id, comment_count, average_score, good_rate, comment_detail, vender_id\
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        for goods_item in link_map.values():
            values.append((goods_item.name.replace("'", "\'"), goods_item.promo.replace("'", "\'"), goods_item.link, 
                goods_item.image, goods_item.price, goods_item.price_type,
                goods_item.icons.replace("'", "\'"), goods_item.channel_id, goods_item.channel,
                0, int(get_current_timestamp()), int(get_current_timestamp()), 0, SOURCE_JINGDONG, # 将 handling_time 置为 0, souce 置为 0
                goods_item.sku_id, goods_item.product_id, goods_item.comment_count, 
                goods_item.average_score, goods_item.good_rate, goods_item.get_comment_detail(), goods_item.venid))
        val = tuple(values)
        sql_map['sql'] = sql
        sql_map['val'] = val
        cur.executemany(sql, val)

    def __batch_update_goods(self, list_2_update, cur, sql_map):
        '''向数据库中批量更新记录'''
        # 拼接 id
        id_list = []
        for id in list_2_update.keys():
            id_list.append(str(id))
        val_ids = ",".join(id_list)
        # 拼接 when then 语句
        when_then_map = {} 
        for id, goods_item in list_2_update.items():
            for column_name in ('name', 'promo', 'link', 'image', 'price', 'price_type', 'icons', 'updated_time', \
                'sku_id', 'product_id', 'comment_count', 'average_score', 'good_rate', 'comment_detail', 'vender_id'):
                when_then = when_then_map.get(column_name)
                if when_then == None:
                    when_then = ''
                val = goods_item.get_value_of_filed_name(column_name)
                if isinstance(val, str): # 如果是字符串类型的话，再包一层引号，还要处理 sql 中字符串的 ' 符号
                    val = "'" + val.replace("'", "\\'") + "'"
                when_then = when_then + '\n' + ' WHEN ' + str(id) + ' THEN ' + str(val)
                when_then_map[column_name] = when_then
        sql_when_then_list = []
        for column_name, when_then in when_then_map.items():
            sql_when_then_list.append(column_name + " = CASE id " + when_then + "\n END")
        sql_when_then = ", \n".join(sql_when_then_list) + " \n"
        # 拼接最终 sql
        sql = "UPDATE gt_item SET \n %s WHERE id IN ( %s ) " % (sql_when_then, val_ids)
        sql_map['sql'] = sql
        cur.execute(sql)

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

    def batch_insert_or_update_brands(self, brand_list):
        '''批量插入或者更新品牌列表'''
        if len(brand_list) == 0:
            logging.warning("Empty Brands List.")
            return False
        val = ''
        links = {}
        for idx in range(0, len(brand_list)):
            link = brand_list[idx].link
            links[link] = brand_list[idx]
            val = val + "'" + link + "'"
            if idx != len(brand_list)-1:
                val = val + ","
        sql = "SELECT * FROM gt_brand WHERE link IN (%s)" % val
        succeed = True
        try:
            con = self.connect_db()
            cur = con.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            # 检索到了数据 => 执行批量更新
            if len(rows) != 0:
                list_2_update = {} # 已经存在于数据库中的记录 => 用于更新
                for row in rows:
                    id = row[BRAND_ID_ROW_INDEX]
                    link = row[BRAND_LINK_ROW_INDEX]
                    if link in links:
                        existed_brand = links.pop(link) # 移除指定的 key
                        list_2_update[id] = existed_brand
                # 执行批量更新操作
                if len(list_2_update) != 0:
                    self.__batch_update_brands(list_2_update, cur)
                    # 如果没有需要插入的记录，就提交事务，下面的逻辑走不到了
                    if len(links) == 0:
                        con.commit()
            # 没有检索到数据 => 执行插入操作
            if len(links) != 0:
                self.__batch_insert_brands(links, cur)
                con.commit()
        except BaseException as e:
            succeed = False
            logging.error("Failed While Batch Insert: %s." % traceback.format_exc())
            con.rollback()
        finally:
            cur.close()
            con.close()
        return succeed

    def __batch_update_brands(self, list_2_update, cur):
        '''批量向数据库中插入品牌信息'''
        # 拼接 id
        val_ids = ""
        idx_ids = 0
        for id in list_2_update.keys():
            if idx_ids == len(list_2_update)-1:
                val_ids = val_ids + str(id)
            else:
                val_ids = val_ids + str(id) + ','
            idx_ids = idx_ids+1
        # 拼接 when then 语句
        when_then_map = {} 
        for id, brand_item in list_2_update.items():
            for column_name in ('name', 'data_initial', 'logo', 'link', 'updated_time'):
                when_then = when_then_map.get(column_name)
                if when_then == None:
                    when_then = ''
                val = brand_item.get_value_of_filed_name(column_name)
                if isinstance(val, str): # 如果是字符串类型的话，再包一层引号
                    val = "'" + val.replace("'", "\\'") + "'"
                when_then = when_then + '\n' + ' WHEN ' + str(id) + ' THEN ' + str(val)
                when_then_map[column_name] = when_then
        sql_when_then = ''
        idx_when_then = 0
        for column_name, when_then in when_then_map.items():
            if idx_when_then == len(when_then_map)-1:
                sql_when_then = sql_when_then + column_name + ' = CASE id ' + when_then + '\n END \n'
            else:
                sql_when_then = sql_when_then + column_name + ' = CASE id ' + when_then + '\n END, \n'
            idx_when_then = idx_when_then+1
        # 拼接最终 sql
        sql = "UPDATE gt_brand SET \n %s WHERE id IN ( %s ) " % (sql_when_then, val_ids)
        cur.execute(sql)

    def __batch_insert_brands(self, link_map, cur):
        '''向数据库中批量插入品牌记录'''
        sql = "INSERT INTO gt_brand (\
            name,\
            data_initial,\
            logo,\
            link,\
            display_order,\
            channel_id,\
            channel,\
            remark,\
            lock_version,\
            updated_time,\
            created_time\
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = []
        for brand in link_map.values():
            values.append((
                brand.name.replace("'", "\'"),
                brand.data_initial,
                brand.logo,
                brand.link,
                brand.dispaly_order,
                brand.channel_id,
                brand.channel,
                '',                     # remark
                0,                      # lock_version
                int(get_current_timestamp()),
                int(get_current_timestamp())
            ))
        val = tuple(values)
        cur.executemany(sql, val)

    def write_channel(self, category):
        '''将各个分类数据写入到数据库种'''
        con = self.connect_db()
        cur = con.cursor()
        row_id = -1
        try:
            # 先插入到数据库中，获取到记录的 id 之后再更新记录的 treepath 字段
            sql = "INSERT INTO gt_channel (\
                name, treepath, parent_id, cat, jdurl, tburl, max_page_count, \
                handling_time, display_order, lock_version, updated_time, created_time\
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, 0, 0, unix_timestamp(now()))"
            # 将处理时间默和最后更新 (完成时间) 默认设置为 0
            val = (category.name, category.treepath, category.parent_id, category.cat,
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
            logging.exception('Insert Operation Error :\n %s' % traceback.format_exc())
        finally:
            cur.close()
            con.close()
        return row_id

    def next_page_to_handle_prameters(self, source: int, page_size: int, start_id: int):
        '''从商品列表中取出下一个需要解析的商品，设计的逻辑参考品类爬取相关的逻辑'''
        handling_before = get_current_timestamp() - get_seconds_of_minutes(GOODS_HANDLE_TIMEOUT_IN_MINUTE)
        # 查询的时候增加 parameters 条件，也即只有当参数为空的时候才爬取，每个产品只爬取一次
        sql = ("SELECT * FROM gt_item WHERE \
            handling_time < %s and \
            parameters is null and \
            store is null and \
            brand is null and \
            price != -1 and \
            id > %s and \
            source = %s \
            ORDER BY id LIMIt %s") % (handling_before, start_id, source, page_size) # 每次取出来 5 个数据吧
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

    def next_goods_page(self, source: int, page_size: int, start_id: int):
        """
        从商品列表中读取一页数据来查询商品的价格信息，这里查询到了数据之后就直接返回了，
        处理数据的时候也不会进行加锁和标记.
        """
        sql = ("SELECT * FROM gt_item WHERE \
            price != -1 \
            AND source = %s \
            AND id > %s \
            ORDER BY id LIMIT %s") % (source, start_id, page_size)
        con = self.connect_db()
        cur = con.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows

    def next_goods_page_for_icons(self, source: int, icons, page_size: int, start_id: int):
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
            AND (%s) \
            ORDER BY id LIMIT %s") % (source, start_id, sql_like, page_size)
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

    def update_goods_list_as_sold_out(self, goods_list):
        '''将指定的产品列表标记为下架状态'''
        succeed = True
        id_list = []
        for good_item in goods_list:
            id_list.append(str(good_item[GOODS_ID_ROW_INDEX]))
        ids = ','.join(id_list)
        if len(ids.strip()) == 0:
            logging.info("Empty Goods Id List.")
            return False
        sql = "UPDATE gt_item SET price = -1, updated_time = %s WHERE id IN ( %s )" % (str(get_current_timestamp()), ids)
        try:
            con = self.connect_db()
            cur = con.cursor()
            cur.execute(sql)
            con.commit()
        except:
            succeed = False
            logging.error("Failed While Batch Update Sold Out:\n%s" % traceback.format_exc())
            logging.error("SQL:\n%s" % sql)
            con.rollback()
        finally:
            cur.close()
            con.close()
        return succeed

    def get_channels_of_channel_ids(self, channel_id_list):
        '''通过 channel id 列表获取 channel 数据'''
        id_list = []
        for id in channel_id_list:
            id_list.append(str(id))
        ids = ','.join(id_list)
        if len(ids.strip()) == 0:
            logging.info("Empty Channel Id List!")
            return
        sql = 'SELECT * FROM gt_channel WHERE id IN ( %s )' % ids
        rows = []
        try: 
            con = self.connect_db()
            cur = con.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
        except BaseException as e:
            logging.error("Error While Getting Channels: %s" % traceback.format_exc())
            logging.error("SQL:\n%s" % sql)
        return rows

    def get_discounts_of_batch_ids(self, batch_id_list):
        '''根据传入的折扣的 id 列表查出数据库中存储的折扣记录'''
        rows = []
        id_list = []
        for id in batch_id_list:
            id_list.append(str(id))
        batch_ids = ','.join(id_list)
        if len(batch_ids.strip()) == 0:
            logging.info("Empty Batch Id List!") # 出现这个信息属于正常现象，即商品没有折扣信息
            return rows
        sql = "SELECT * FROM gt_discount WHERE batch_id IN ( %s )" % batch_ids
        try:
            con = self.connect_db()
            cur = con.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
        except BaseException as e:
            logging.error("Error While Getting Discounts:\n%s" % traceback.format_exc())
            logging.error("SQL:\n%s" % sql)
        return rows

    def batch_insert_discounts(self, discounts):
        '''批量向数据库中插入折扣信息'''
        succeed = True
        if len(discounts) == 0:
            logging.info("Empty Discounts To Insert!!")
            return succeed
        sql = "INSERT INTO gt_discount (goods_id, batch_id, quota, discount, start_time, end_time,\
            lock_version, updated_time, created_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        try:
            values = []
            con = self.connect_db()
            cur = con.cursor()
            for discount in discounts:
                values.append((discount.goods_id, discount.batch_id, discount.quota, discount.discount, 
                    discount.start_time, discount.end_time, 0, get_current_timestamp(), get_current_timestamp()))
            cur.executemany(sql, tuple(values))
            con.commit()
        except BaseException as e:
            succeed = False
            logging.error("Failed While Batch Insert Discounts:\n%s" % traceback.format_exc())
            logging.error("SQL:\n%s" % sql)
            con.rollback()
        finally:
            cur.close()
            con.close()
        return succeed

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
        self.connect_redis()
        today = get_timestamp_of_today_start()
        rows = dBOperator.get_goods_list_from_database(goods_list)
        for row in rows:
            goods_id = row[GOODS_ID_ROW_INDEX]
            price = row[GOODS_PRICE_ROW_INDEX]
            name = GOODS_PRICE_HISTORY_REDIS_KEY_PATTERN % goods_id
            self.r.hset(name, str(today), price)

    def add_prices(self, goods_item, price_map):

        '''
        添加历史价格
        添加历史价格，不过有个问题，这里价格是统计了折扣之后的结果，所以可能有问题，
        这里计算出来的价格也就当作一个补充吧，即项目正式开启爬虫之前进行的数据抓取
        '''
        goods_id = goods_item[GOODS_ID_ROW_INDEX]
        name = GOODS_PRICE_HISTORY_REDIS_KEY_PATTERN % goods_id
        self.connect_redis()
        for d,p in price_map.items():
            price = self.r.hget(name, str(d))
            if price == None:
                self.r.hset(name, str(d), p)

    def connect_redis(self):
        '''连接 Redis'''
        if not self.connected:
            self.connected = True
        pool = ConnectionPool(host=config.redis.host, port=config.redis.port,\
            db=config.redis.db, password=config.redis.password)
        self.r = StrictRedis(connection_pool=pool)

redisOperator = RedisOperator()

dBOperator = DBOperator()
