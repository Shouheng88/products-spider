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
        %s      : Crawl price hisotry\m\
    -e[--env]                   Environment\n\
        %s                   : Local develop\n\
        %s                    : Test server\n\
        %s            : Server local\n\
        %s           : Local connect to remote\n\
    -a[--arg]                   Argument, specify an argument for given command. For example,\n\
                                started id for prices and discount crawl job.\n\
    " % (CMD_WRITE_JD_CATEGORY, CMD_CRAWL_JD_CATEGORY, CMD_CRAWL_JD_GOODS, \
        CMD_CRAWL_JD_DETAIL, CMD_CRAWL_JD_DISCOUNT, CMD_CRAWL_JD_PRICES, CMD_CRAWL_HISTORY,\
        ENV_LOCAL, ENV_TEST, ENV_SERVER_LOCAL, ENV_SERVER_REMOTE)

def main(argv):
    """主程序入口"""
    try:
        # :和= 表示接受参数
        opts, args = getopt.getopt(argv, "-h:-c:-e:-a:", ["help", "command=", 'env=', 'arg='])
    except getopt.GetoptError:
        __show_invalid_command()
        sys.exit(2)
    if len(opts) == 0:
        __show_invalid_command()
        return
    env = None # 环境
    for opt, arg in opts:
        if opt in ('-e', '--env'):
            env = arg
    param = None # 参数
    for opt, arg in opts:
        if opt in ('-a', '--arg'):
            param = arg
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(command_info)
            sys.exit()
        elif opt in ("-a", "--arg", "-e", "--env"):
            continue # 过滤掉
        elif opt in ("-c", "--command"):
            if env == None:
                print('Error: Missing evnironment.')
                print(command_info)
                return
            __config_environment(env, arg)
            if arg == CMD_WRITE_JD_CATEGORY: # 讲处理好的品类信息写入到数据库中
                print("Start to write JD categories to database ...")
                jd = JDCategory()
                jd.write_results()
            elif arg == CMD_CRAWL_JD_CATEGORY: # 爬取京东的产品的品类信息
                print("CraStart to crawlwling JD category ...")
                jd = JDCategory()
                jd.crawl()
            elif arg == CMD_CRAWL_JD_GOODS: # 爬取京东每个品类的产品列表
                print("Start to crawl JD goods ...")
                jd = JDGoods()
                jd.crawl()
            elif arg == CMD_CRAWL_JD_DETAIL: # 爬取京东每个产品的详情信息
                print('Start to crawl JD detail ...')
                jd = JDDetails()
                jd.crawl()
                pass
            elif arg == CMD_CRAWL_JD_DISCOUNT: # 爬取京东每个商品的折扣信息
                print('Start to crawl JD discount, starter[%s] ...' % param)
                jd = JDDiscount()
                jd.crawl(param)
                pass
            elif arg == CMD_CRAWL_JD_PRICES: # 爬取京东每个产品的价格信息
                print('Start to crawl JD prices, starter[%s] ...' % param)
                jd = JDPrices()
                jd.crawl(param)
                pass
            elif arg == CMD_CRAWL_HISTORY:
                print('Start to crawl price histories, starter[%s] ...' % param)
                mmb = ManmanBuy()
                mmb.crawl()
            else:
                 __show_invalid_command()
        else:
            __show_invalid_command()

def __show_invalid_command():
    print('Error: Unrecognized command.')
    print(command_info)     

def __config_environment(env: str, cmd: str):
    """配置日志"""
    # 配置日志级别
    if env == ENV_LOCAL or env == ENV_TEST:
        config.logLevel = logging.DEBUG
    elif env == ENV_SERVER_LOCAL or env == ENV_SERVER_REMOTE:
        config.logLevel = logging.INFO
    # 区分日志文件
    if cmd == CMD_WRITE_JD_CATEGORY or cmd == CMD_CRAWL_JD_CATEGORY:
        config.logAppendix = '-category'
    elif cmd == CMD_CRAWL_JD_GOODS:
        config.logAppendix = '-goods'
    elif cmd == CMD_CRAWL_JD_DETAIL:
        config.logAppendix = '-detail'
    elif cmd == CMD_CRAWL_JD_PRICES:
        config.logAppendix = '-prices'
    elif cmd == CMD_CRAWL_JD_DISCOUNT:
        config.logAppendix = '-discount'
    # 其他属性配置
    config.config_logging()
    config.set_env(env)
    logging.debug("Execution: env[%s] Cmd[%s]" % (env, cmd))

if __name__ == "__main__":
    main(sys.argv[1:])
