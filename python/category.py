#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
from bs4 import BeautifulSoup

from models import Category

from operators import ExcelOperator as ExcelOperator
from operators import dBOperator as db
from config import *

class JDCategory(object):
    '''京东分类信息管理类'''
    def __init__(self):
        self.dist = {}
        self.dist["一级品类"] = []
        self.dist["二级品类"] = []
        self.dist["二级品类链接"] = []
        self.dist["三级品类"] = []
        self.dist["三级品类链接"] = []

    def crawl(self):
        '''爬取京东的品类信息'''
        html = requests.get("https://www.jd.com/allSort.aspx").text
        soup = BeautifulSoup(html, "html.parser")
        categories = soup.find_all(class_="category-item m")
        for category in categories:
            item_title = category.find(class_="item-title").span.string
            items = category.find_all(class_="items")
            for item in items:
                collections = item.find_all("dt")
                for collection in collections:
                    collection_name = collection.a.string
                    collection_link = "https:" + collection.a["href"]
                    collection_items = collection.find_next_sibling("dd").find_all("a")
                    for collection_item in collection_items:
                        collection_item_name = collection_item.string
                        collection_item_link = "https:" + collection_item["href"]
                        print(item_title + "-" + collection_name + "(" + collection_link +  ")-" + collection_item_name + "(" + collection_item_link +  ")")
                        self.dist["一级品类"].append(item_title)
                        self.dist["二级品类"].append(collection_name)
                        self.dist["二级品类链接"].append(collection_link)
                        self.dist["三级品类"].append(collection_item_name)
                        self.dist["三级品类链接"].append(collection_item_link)
        eo = ExcelOperator()
        eo.write_excel("京东", self.dist, JD_CATEGORY_STORE)

    def write_results(self):
        """将处理结果写入到数据库中"""
        # 读取 Excel
        eo = ExcelOperator()
        r_dist = eo.read_excel(JD_HANDLED_CATEGORY_STORE)
        cols = r_dist["京东"]
        dist = {}
        for idx in range(0, len(cols[0])):
            c_name = cols[0][idx] # 一级品类名称
            sc_name = cols[1][idx] # 二级品类名称
            tc_name = cols[3][idx] # 三级品类名称
            max_page_count = cols[5][idx]
            channel = dist.get(c_name) # 一级品类
            if channel == None:
                channel = Category(cols[0][idx], display_order=idx)
                dist[c_name] = channel
            s_channel = channel.children.get(sc_name) # 二级品类
            if s_channel == None:
                s_channel = Category(sc_name, cols[2][idx], display_order=idx)
                channel.children[sc_name] = s_channel
            link =  cols[4][idx]
            t_channel = Category(tc_name, link, display_order=idx, max_page_count=max_page_count, cat=link[(link.rfind('=')+1):]) # 三级品类
            s_channel.children[tc_name] = t_channel
        # 写入 DB
        for c_name, c_channel in dist.items(): # 一级品类遍历
            p_id = db.write_channel(c_channel)
            if p_id == -1:
                logging.error("INSERT INTO DB ERROR!!!!!!")
                break
            for s_name, s_channel in c_channel.children.items(): # 二级品类遍历
                s_channel.parent_id = p_id
                s_channel.treepath = c_channel.treepath # 子分类先继承父分类的 treepath
                s_channel.jdurl = s_channel.link
                sp_id = db.write_channel(s_channel)
                if sp_id == -1:
                    logging.error("INSERT INTO DB ERROR!!!!!!")
                    break
                for t_name, t_channel in s_channel.children.items(): # 三级品类遍历
                    t_channel.parent_id = sp_id
                    t_channel.treepath = s_channel.treepath
                    t_channel.jdurl = t_channel.link
                    tp_id = db.write_channel(t_channel)
                    if tp_id == -1:
                        logging.error("INSERT INTO DB ERROR!!!!!!")
                        break

class TBCategory(object):
    '''淘宝分类信息管理类'''
    def __init__(self):
        self.dist = {}
        self.dist["一级品类"] = []
        self.dist["二级品类"] = []
        self.dist["二级品类链接"] = []
        self.dist["三级品类"] = []
        self.dist["三级品类链接"] = []

    def crawl(self):
        '''爬取淘宝分类数据'''
        html = requests.get("https://www.taobao.com/tbhome/page/market-list").text
        soup = BeautifulSoup(html, "html.parser")
        categories = soup.find_all(class_="home-category-list")
        for category in categories:
            item_title = category.find(class_="category-name").string
            collections = category.find_all(class_="category-list-item")
            for collection in collections:
                collection_name = collection.a.string
                if collection_name == None:
                    collection_name = ""
                collection_link = ""
                if collection.a.get("href") != None:
                    collection_link = "https:" + collection.a["href"]
                collection_items = collection.find(class_="category-items").find_all(class_="category-name")
                for collection_item in collection_items:
                    collection_item_name = collection_item.string
                    collection_item_link = ""
                    if collection_item.get("href") != None:
                        collection_item_link = "https:" + collection_item["href"]
                    if collection_item_name == None:
                        collection_item_name = ""
                    print(item_title + "-" + collection_name + "(" + collection_link +  ")-" + collection_item_name + "(" + collection_item_link +  ")")
                    self.dist["一级品类"].append(item_title)
                    self.dist["二级品类"].append(collection_name)
                    self.dist["二级品类链接"].append(collection_link)
                    self.dist["三级品类"].append(collection_item_name)
                    self.dist["三级品类链接"].append(collection_item_link)
        eo = ExcelOperator()
        eo.write_excel("淘宝", self.dist, TB_CATEGORY_STORE)

if __name__ == "__main__":
    config.config_logging()
    jd = JDCategory()
    jd.write_results()
