#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys, getopt
from category import *
from goods import *
from details import *
from prices import *
from config import *
from discount import *
from mmb import *

command_info = "\
Options: \n\
    -h[--help]                  Help info\n\
    -c[--command]               Command\n\
        %s          : Write handled categories from excel to database\n\
        %s       : Crawl jingdong categories\n\
        %s          : Crawl jingdong goods for every channel\n\
        %s         : Crawl jingdong item detail\n\
        %s       : Crawl jingdong item discount\n\
        %s         : Crawl jingdong item prices from batch api, used to detect item sold out\n\
        %s           : Crawl price hisotry\n\
        %s          : Crawl taobao goods for every channel\n\
    -e[--env]                   Environment\n\
        %s                   : Local develop\n\
        %s                    : Test server\n\
        %s            : Server local\n\
        %s           : Local connect to remote\n\
    -s[--starter]               The starter used to set a restart point for some jobs.\n\
    " % (CMD_WRITE_JD_CATEGORY, CMD_CRAWL_JD_CATEGORY, CMD_CRAWL_JD_GOODS, \
        CMD_CRAWL_JD_DETAIL, CMD_CRAWL_JD_DISCOUNT, CMD_CRAWL_JD_PRICES, CMD_CRAWL_HISTORY, CMD_CRAWL_TB_GOODS,\
        ENV_LOCAL, ENV_TEST, ENV_SERVER_LOCAL, ENV_SERVER_REMOTE)

def main(argv):
    """主程序入口"""
    try:
        # :和= 表示接受参数
        opts, args = getopt.getopt(argv, "-h:-c:-e:-s:", ["help", "command=", 'env=', 'starter='])
    except BaseException as e:
        __show_invalid_command(str(e))
        sys.exit(2)
    if len(opts) == 0:
        __show_invalid_command('empty parameters')
        return
    cmd = starter = env = None
    for opt, arg in opts:
        if opt in ('-e', '--env'):
            env = arg
        elif opt in ('-s', '--starter'):
            starter = arg
        elif opt in ("-c", "--command"):
            cmd = arg
        elif opt in ('-h', '--help'):
            print(command_info)
            return
    if cmd == None:
        __show_invalid_command('command required')
    elif env == None:
        __show_invalid_command('environment required')
    else:
        config.set_cmd(cmd)
        config.set_env(env)
        config.config_logging()
        logging.debug("Execution: env[%s] Cmd[%s] starter[%s] args%s" % (env, arg, starter, str(args)))
        if cmd == CMD_WRITE_JD_CATEGORY: # 讲处理好的品类信息写入到数据库中
            print("Start to write JD categories to database ...")
            JDCategory().write_results()
        elif cmd == CMD_CRAWL_JD_CATEGORY: # 爬取京东的产品的品类信息
            print("CraStart to crawlwling JD category ...")
            JDCategory().crawl()
        elif cmd == CMD_CRAWL_JD_GOODS: # 爬取京东每个品类的产品列表
            print("Start to crawl JD goods ...")
            JDGoods().crawl()
        elif cmd == CMD_CRAWL_JD_DETAIL: # 爬取京东每个产品的详情信息
            print('Start to crawl JD detail ...')
            JDDetails().crawl()
        elif cmd == CMD_CRAWL_JD_DISCOUNT: # 爬取京东每个商品的折扣信息
            print('Start to crawl JD discount, starter[%s] ...' % starter)
            JDDiscount().crawl(starter)
        elif cmd == CMD_CRAWL_JD_PRICES: # 爬取京东每个产品的价格信息
            print('Start to crawl JD prices, starter[%s] ...' % starter)
            JDPrices().crawl(starter)
        elif cmd == CMD_CRAWL_HISTORY: # 爬取商品的历史价格信息
            print('Start to crawl price histories, starter[%s] ...' % starter)
            ManmanBuy().crawl(starter, args)
        elif cmd == CMD_CRAWL_TB_GOODS:
            print("Start to crawl TB goods ...")
            TBGoods().crawl()
        else:
            __show_invalid_command('unknown command')

def __show_invalid_command(info: str):
    print('Error: Unrecognized command: %s' % info)
    print(command_info)     

if __name__ == "__main__":
    main(sys.argv[1:])
