#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys, getopt
from category import *
from goods import JDGoods as JDGoods
from operators import DBOperator as DB
from config import *

command_info = "\
Options: \n\
    -h[--help]                  Help info\n\
    -c[--command]               Command\n\
        write_category          : Write handled categories from excel to database\n\
        crawl_jd_category       : Crawl jingdong categories\n\
        crawl_jd_goods          : Crawl jingdong goods for every channel\n\
        crawl_jd_detail         : Crawl jingdong item detail\n\
        crawl_jd_discount       : Crawl jingdong item discount\n\
        crawl_jd_price_batch    : Crawl jingdong item prices from batch api, used to detect item sold out\n\
    -e[--env]                   Environment\n\
        local                   : Local develop\n\
        test                    : Test server\n\
        server_local            : Server local\n\
        server_remote           : Local connect to remote\
    "

def main(argv):
    """主程序入口"""
    try:
        # :和= 表示接受参数
        opts, args = getopt.getopt(argv, "-h:-c:-e:", ["help", "command=", 'env='])
    except getopt.GetoptError:
        print(command_info)
        sys.exit(2)
    env = None # 环境
    for opt, arg in opts:
        if opt in ('-e', '--env'):
            env = arg
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(command_info)
            sys.exit()
        elif opt in ("-c", "--command"):
            if env == None:
                print('Error: Missing evnironment.')
                print(command_info)
                return
            __config_environment(env)
            if arg == 'write_category':
                logging.info("Writing jingdong handled categories to database ...")
                jd = JDCategory()
                jd.write_results()
            elif arg == 'crawl_jd_category':
                logging.info("Crawling jingdong categories ...")
                jd = JDCategory()
                jd.crawl()
            elif arg == 'crawl_jd_goods':
                logging.info("Crawling jingdong goods for every channel ...")
                jd = JDGoods()
                jd.crawl()
            else:
                print(command_info)

def __config_environment(env: str):
    """配置日志"""
    if env == 'local' or env == 'test':
        config.logLevel = logging.DEBUG
    config.config_logging()
    config.set_env(env)
    logging.debug("Execution: env " + str(env))

if __name__ == "__main__":
    main(sys.argv[1:])
