#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
from bs4 import BeautifulSoup
from common.file_operator import ExcelOperator as ExcelOperator

# 淘宝品类爬取
class CategorySpider(object):
    def __init__(self):
        self.dist = {}
        self.dist["一级品类"] = []
        self.dist["二级品类"] = []
        self.dist["二级品类链接"] = []
        self.dist["三级品类"] = []
        self.dist["三级品类链接"] = []

    def crawlCategory(self):
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
        eo.write_excel("淘宝", self.dist, "../淘宝分类.xlsx")
