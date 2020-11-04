# -*- coding: utf-8 -*-
# __author__ = "zok"  362416272@qq.com
# Date: 2019-10-6  Python: 3.7

import time
import random
import asyncio
import pyppeteer
from pyppeteer import page
import logging
import traceback
from pyppeteer.dialog import Dialog
from typing import *

from models import *
from config import *
from utils import *
from goods_operator import *

class TaoBao(object):
    """淘宝的登录类"""
    def __init__(self, username: str, password: str, debug=False, headless=True):
        super().__init__()
        pyppeteer.DEBUG = debug
        self.page: page.Page = None
        self.headless = headless
        self.username = username
        self.password = password
        self.cookies = []
        self.args = ['--disable-extensions',
            '--hide-scrollbars',
            '--disable-bundled-ppapi-flash',
            '--mute-audio',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-gpu',
            '--disable-infobars']
        if not self.headless: # 非 headless 模式的时候加上窗口限制
            self.args.append('--window-size={1200},{600}')
        # 调整 websorckets 的日志等级
        logging.getLogger('websockets.protocol').setLevel(logging.WARNING)

    async def init(self):
        """初始化浏览器"""
        browser = await pyppeteer.launch(options = { 'logLevel': logging.WARNING }, headless= self.headless, args=self.args, dumpio = True)
        self.page = await browser.newPage()
        # 设置浏览器头部
        # for cookie in self.cookies:
            # await self.page.setCookie(cookie)
        await self.page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36")
        # 设置浏览器大小
        await self.page.setViewport({'width': 1200, 'height': 600})
        # 注入 js
        await self.page.evaluateOnNewDocument('()=>{ Object.defineProperties(navigator,' '{ webdriver:{ get: () => false } }) }')  # 本页刷新后值不变

    async def login(self, is_redirct: bool = False):
        """登陆"""
        # 打开淘宝登陆页面
        if not is_redirct:
            res = await self.page.goto('https://login.taobao.com')
        time.sleep(random.random() * 2)
        # 输入用户名
        await self.page.type('#fm-login-id', self.username, {'delay': random.randint(100, 151) - 50})
        # 输入密码
        await self.page.type('#fm-login-password', self.password, {'delay': random.randint(100, 151)})
        # 获取滑块元素
        # slider = await self.page.Jeval('#nocaptcha', 'node => node.style')
        # if slider:
        #     print('有滑块')
        #     # 移动滑块
        #     flag = await self.mouse_slider()
        #     if not flag:
        #         print('滑动滑块失败')
        #         return None
        #     time.sleep(random.random() + 1.5)
        # 点击登陆
        await asyncio.sleep(3)
        await self.page.click('.password-login')
        await asyncio.sleep(5)
        cookies_list = await self.page.cookies()
        return cookies_list

    async def login_first_time(self, phone: str):
        '''首次登录'''
        # 初始化浏览器
        await self.init()
        # 打开淘宝登陆页面
        await self.page.goto('https://login.taobao.com')
        # 打开淘宝登陆页面
        time.sleep(random.random() * 2)
        await self.page.click('.sms-login-tab-item')
        # 输入用户名
        await self.page.type('#fm-sms-login-id', phone, {'delay': random.randint(100, 151) - 50})
        await self.page.click('.send-btn-link')
        code = input('input code:')
        # 输入密码
        await self.page.type('#fm-smscode', code, {'delay': random.randint(100, 151)})
        # 确定
        await self.page.click('.sms-login')
        await asyncio.sleep(5)
        cookies_list = await self.page.cookies()
        return cookies_list

    async def crawl_keyword(self, keyword: str, max_page: int, tg, channel: Channel):
        """爬取指定关键字的商品"""
        current_page = 0
        hit_max_fail_count = False
        while(current_page <= max_page):
            try:
                # 总是+1，这样某页失败了，这页直接跳过
                current_page += 1
                pageurl = "https://s.taobao.com/search?q=%s&s=%d" % (keyword, current_page*44)
                logging.debug('Crawling %s' % pageurl)
                (goods_list, parsed_max_page) = await self.__crawl_goods_list_page(pageurl, channel)
                # 解析总页数
                if current_page == 1 and parsed_max_page != None:
                    max_page = min(max_page, parsed_max_page)
                # 批量插入或者更新到数据库中
                go.batch_insert_or_update_goods(goods_list)
                existed_goods = go.get_existed_goods(goods_list)
                redis.add_goods_price_histories(existed_goods)
            except BaseException as e:
                hit_max_fail_count = tg.increase_fail_count()
                logging.error("Error While Crawling TB Goods:\n%s" % traceback.format_exc())
                logging.error("REQ:%s" % pageurl)
            finally:
                if hit_max_fail_count:
                    break

    async def __drop_down(self):
        """网页下拉，不下拉抓取不到部分数据"""
        for x in range(1, 11, 2):
            time.sleep(1)
            j = x / 10
            js = 'document.documentElement.scrollTop = document.documentElement.scrollHeight * %f' % j
            await self.page.evaluate(js)

    async def __get_cookie(self):
        """获取 cookie"""
        cookies_list = await self.page.cookies()
        logging.info("Getting Cookie ...")
        cookies = ''
        for cookie in cookies_list:
            str_cookie = '{0}={1};'
            str_cookie = str_cookie.format(cookie.get('name'), cookie.get('value'))
            cookies += str_cookie
        return cookies

    async def __mouse_slider(self):
        """滑动滑块（暂时还没用到）"""
        await asyncio.sleep(3)
        try:
            await self.page.hover('#nc_1_n1z')
            # 鼠标按下按钮
            await self.page.mouse.down()
            # 移动鼠标
            await self.page.mouse.move(2000, 0, {'steps': 30})
            # 松开鼠标
            await self.page.mouse.up()
            await asyncio.sleep(2)
        except Exception as e:
            print(e, '      :错误')
            return None
        else:
            await asyncio.sleep(3)
            # 获取元素内容
            slider_again = await self.page.querySelectorEval('#nc_1__scale_text', 'node => node.textContent')
            if slider_again != '验证通过':
                return None
            else:
                print('验证通过')
                return True

    async def __crawl_goods_list_page(self, pageurl: str, channel: Channel, retry: bool = False) -> (List[GoodsItem], int):
        """搜索指定的关键字"""
        await self.page.goto(pageurl)
        time.sleep(random.random() * 2)
        await self.__drop_down() # 下拉
        items = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div')
        page_count = None
        e_page_count = await self.page.xpath('//*[@id="J_relative"]/div[1]/div/div[2]/ul/li[2]')
        if len(e_page_count) > 0:
            str_page_count = await (await e_page_count[0].getProperty('textContent')).jsonValue()
            str_page_counts = str_page_count.split('/')
            if len(str_page_counts) > 1:
                page_count = parse_number_or_none(str_page_counts[1])
        goods_list = []
        for idx in range(1, len(items)+1):
            # 循环体内进行 try...catch 某个条目解析出现异常不影响其他条目
            try:
                # 有时候第一个商品的链接有点问题，会塞成一个广告
                e_link = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div[%d]/div[1]/div/div[1]/a' % idx)
                e_img = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div[%d]/div[1]/div/div[1]/a/img' % idx)
                e_price = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div[%d]/div[2]/div[1]/div[1]/strong' % idx)
                e_price_type = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div[%d]/div[2]/div[1]/div[1]/span' % idx)
                e_title = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div[%d]/div[2]/div[2]/a' % idx)
                e_store_link = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div[%d]/div[2]/div[3]/div[1]/a' % idx)
                e_store = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div[%d]/div[2]/div[3]/div[1]/a/span[2]' % idx)
                e_icons = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div[%d]/div[2]/div[4]/div[1]/ul/li' % idx)
                e_tmall = await self.page.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/div[%d]/div[2]/div[4]/div[1]/ul/li/a' % idx)
                link: str = await (await e_link[0].getProperty('href')).jsonValue()
                image = await (await e_img[0].getProperty('src')).jsonValue()
                price = await (await e_price[0].getProperty('textContent')).jsonValue()
                price_type = await (await e_price_type[0].getProperty('textContent')).jsonValue()
                title: str = await (await e_title[0].getProperty('textContent')).jsonValue()
                store: str = await (await e_store[0].getProperty('textContent')).jsonValue()
                store_link = await (await e_store_link[0].getProperty('href')).jsonValue()
                sku_id = link[link.index('=')+1: link.index('&')]
                if len(link) > 490: # 当链接超长的时候的处理方案
                    link = 'https://item.taobao.com/item.htm?id=%s' + sku_id
                goods_item = GoodsItem(title.strip(), '', link, image, int(float(price)*100), price_type, '', '')
                goods_item.sku_id = sku_id.strip()
                goods_item.channel = channel.name
                goods_item.channel_id = channel.id
                goods_item.store = store
                goods_item.store_link = store_link
                # 设置商品的来源字段
                goods_item.source = 1 #默认淘宝
                if len(e_tmall) > 0:
                    label: str = await (await e_tmall[0].getProperty('href')).jsonValue()
                    if label.startswith('https://www.tmall.com'):
                        goods_item.source = 2
                    else:
                        goods_item.source = 1
                # icons
                icon_list = []
                for e_icon in e_icons:
                    e_icon_title = await e_icon.querySelector('.icon > *')
                    if e_icon_title != None:
                        icon_title = await (await e_icon_title.getProperty('title')).jsonValue()
                        icon_list.append(icon_title.strip())
                if len(icon_list) > 0:
                    goods_item.icons = ' '.join(icon_list)
                # 加入到列表中
                goods_list.append(goods_item)
            except BaseException as e:
                logging.error('Failed to get info from list:\n%s' % traceback.format_exc())
        # 检查是否触发了强制登录
        if len(items) == 0 and not retry:
            e_login_form = await self.page.querySelector('.login-form')
            if e_login_form != None:
                logging.warning('Login event was invoked!!!!')
                await self.login(is_redirct=True) # 进行登录
                return await self.__crawl_goods_list_page(pageurl, channel, retry=True)
        elif len(items) == 0 and retry:
            # 重新登录，但是还是无法进入商品列表
            e_login_form = await self.page.querySelector('.login-form')
            if e_login_form != None:
                raise Exception('Invoked Login Event!!!')
        return (goods_list, page_count)

    async def craw_items(self):
        '''从列表中取出商品并进行爬取'''
        # 从数据库中取条目
        # 爬取条目信息
        # 更新到数据库
        await self.__init()
        await self.login()
        #await self.__crawl_item('https://detail.tmall.com/item.htm?id=626313427864')
        #await self.__crawl_item('https://item.taobao.com/item.htm?id=629032933807')

    async def __crawl_item(self, pageurl: str):
        """爬取某个条目的详情信息"""
        if pageurl.startswith("https://detail.tmall"):
            await self.__crawl_item_tmall(pageurl)
        else:
            await self.__crawl_item_taobao(pageurl)

    async def __crawl_item_taobao(self, pageurl: str):
        """爬取淘宝商品的条目"""
        # self.page.on('dialog', lambda dialog: asyncio.ensure_future(__handle_dialog(dialog)))
        await self.page.goto(pageurl)
        time.sleep(random.random() * 2)
        e_error = await self.page.xpath('//*[@id="error-notice"]')
        if e_error != None:
            # 讲商品标记为下架吧
            pass
        # e_close = await self.page.xpath('//*[@id="sufei-dialog-close"]')
        # if e_close != None:
            # await self.page.click('#sufei-dialog-close')
        await self.__drop_down() # 下拉
        e_store = await self.page.xpath('//*[@id="header-content"]/div[2]/div[1]/div[1]/a')
        e_comment = await self.page.xpath('//*[@id="J_RateCounter"]')
        e_params = await self.page.xpath('//*[@id="tb_attributes"]/ul[1]/li')
        e_details = await self.page.xpath('//*[@id="tb_attributes"]/ul[2]/li')
        store: str = await (await e_store[0].getProperty('textContent')).jsonValue()
        store_link: str = await (await e_store[0].getProperty('href')).jsonValue()
        comment: str = await (await e_comment[0].getProperty('textContent')).jsonValue()
        for e_param in e_params:
            param: str = await (await e_param.getProperty('textContent')).jsonValue()
            print(param.strip())
        for e_detail in e_details:
            detail: str = await (await e_detail.getProperty('textContent')).jsonValue()
            print(detail.strip())
        print(store.strip())
        print(store_link)
        # print(comment)

    async def __crawl_item_tmall(self, pageurl: str):
        """爬取天猫商品的条目"""
        # self.page.on('dialog', lambda dialog: asyncio.ensure_future(__handle_dialog(dialog)))
        await self.page.goto(pageurl)
        time.sleep(random.random() * 2)
        e_error = await self.page.xpath('//*[@id="error-notice"]')
        if e_error != None:
            # 讲商品标记为下架吧
            pass
        # e_close = await self.page.xpath('//*[@id="sufei-dialog-close"]')
        # if e_close != None:
        #     await self.page.click('#sufei-dialog-close')
        await self.__drop_down() # 下拉
        e_store = await self.page.xpath('//*[@id="shopExtra"]/div[1]/a')
        # e_comment = await self.page.xpath('//*[@id="J_ItemRates"]/div')
        e_brand = await self.page.xpath('//*[@id="J_BrandAttr"]/div')
        e_params = await self.page.xpath('//*[@id="J_AttrUL"]/li')
        e_details = await self.page.xpath('//*[@id="J_Attrs"]/table[1]/tbody/tr')
        store: str = await (await e_store[0].getProperty('textContent')).jsonValue()
        store_link: str = await (await e_store[0].getProperty('href')).jsonValue()
        # comment: str = await (await e_comment[0].getProperty('textContent')).jsonValue()
        brand: str = await (await e_brand[0].getProperty('textContent')).jsonValue()
        for e_param in e_params:
            param: str = await (await e_param.getProperty('textContent')).jsonValue()
            print(param.strip())
        for e_detail in e_details:
            detail: str = await (await e_detail.getProperty('textContent')).jsonValue()
            print(detail.strip())
        print(store.strip())
        print(store_link)
        # print(comment)
        print(brand.strip())

    async def __handle_dialog(self, dialog: Dialog):
        print(dialog.message)#打印出弹框的信息
        print(dialog.type)#打印出弹框的类型，是alert、confirm、prompt哪种
        # print(dialog.defaultValue())#打印出默认的值只有prompt弹框才有
        await self.page.waitFor(2000)#特意加两秒等可以看到弹框出现后取消

if __name__ == '__main__':
    config.config_logging()
    tb = TaoBao('***REMOVED***', '***REMOVED***', debug=False, headless=False)
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(tb.login_first_time('17753137089'))
    loop.run_until_complete(task)
