#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from jd.category_spider import CategorySpider as JDCategorySpider
from tb.category_spider import CategorySpider as TBCategorySpider

if __name__ == "__main__":
    tbc = TBCategorySpider()
    tbc.crawlCategory()
