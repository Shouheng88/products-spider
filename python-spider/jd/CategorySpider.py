#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#import common.file_operator as fo
import requests
import logging
from bs4 import BeautifulSoup

# 京东-分类爬取
class CategorySpider(object):
    def __init__(self):
        pass

    def crawlCaegory(self):
        html = requests.get("https://www.jd.com/allSort.aspx").text
        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all(class_="items")
        for item in items.contents:
            print(item)
            print(type(item))
        
if __name__ == "__main__":
    CategorySpider().crawlCaegory()
