#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
from bs4 import BeautifulSoup
from common.file_operator import ExcelOperator as ExcelOperator

# 京东-分类爬取
class CategorySpider(object):
    def __init__(self):
        self.dist = {}
        self.dist["一级品类"] = []
        self.dist["二级品类"] = []
        self.dist["二级品类链接"] = []
        self.dist["三级品类"] = []
        self.dist["三级品类链接"] = []

    def crawlCategory(self):
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
        eo.write_excel("京东", self.dist, "../京东分类.xlsx")
