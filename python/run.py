#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys, getopt
from category import JDCategory as JDCategory
from category import TBCategory as TBCategory
from goods import JDGoods as JDGoods
from operators import DBOperator as DB
from utils import TimeHelper as TH
from config import GlobalConfig as Config

# 主程序入口
def main(argv):
    """主程序入口"""
    Config.config_logging()
    command_info = "\
    选项说明：\n\
        -h[--help]    帮助信息。\n\
        -c[--crawl]   爬取数据，同时必需参数 [-t] 指定目标对象，接受参数：\n\
            c         表示爬取品类信息\n\
            g         表示爬取商品信息\n\
        -w[--write]   写入数据，同时必需参数 [-t] 指定目标对象，接受参数：\n\
            c         写入品类数据到数据库中\n\
        -t[--target]  目标对象，接受参数 jd, tb，分别表示爬取对象京东、淘宝的数据。\n\
    "
    # TODO(me) 增加环境配置信息
    try:
        # :和= 表示接受参数
        opts, args = getopt.getopt(argv, "-c:-w:-t:-h", ["help", "crawl=", 'target=', ['write=']])
    except getopt.GetoptError:
        print(command_info)
        sys.exit(2)
    # 目标：京东还是淘宝等等
    target = None
    for opt, arg in opts:
        if opt in ('-t', '--target'):
            target = arg
    logging.debug("target: " + str(target))
    # 指令
    for opt, arg in opts:
        if opt in ('-h', '--help'): # 帮助
            print(command_info)
            sys.exit()
        elif opt in ("-c", "--crawl"): # 爬取
            if target == None:
                print(command_info)
                break
            if arg == 'c': # 爬品类
                if target == 'jd':
                    print("爬取京东品类信息...")
                    jd = JDCategory()
                    jd.crawl()
                elif target == "tb":
                    print("爬取淘宝品类信息...")
                    tb = TBCategory()
                    tb.crawl()
            elif arg == 'g': # 爬商品
                if target == 'jd':
                    print("爬取京东商品信息...")
                    jd = JDGoods()
                    jd.crawl()
        elif opt in ("-w", "--write"): # 写数据
            if target == None:
                print(command_info)
                break
            if arg == 'c':
                if target == 'jd':
                    # 写入京东的品类处理结果到数据库中
                    # 商品品类信息以京东处理结果
                    print("写入京东品类处理结果到数据库...")
                    jd = JDCategory()
                    jd.write_results()

# 主程序，入口
if __name__ == "__main__":
    main(sys.argv[1:])
