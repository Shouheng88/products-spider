# 数码电商爬虫系统

## 1、基本的说明

当初为了在几个电商网站抓取商品信息数据搭建的系统。该系统主要用来抓取电商网站上面的一百个左右品类的商品的价格信息、商品信息和折扣信息等。抓取的电商网站主要是某宝和某东。其他的电商网站抓取信息的方式无外乎这两种。跟其他的示例代码不同，该系统通过定时执行的方式将商品的信息分开抓取、存储，用到的时候再组合以降低被 block 的可能性。另外，在开发的时候我设计了任务调度的规则，以使得多个计算机可以并行执行任务。

该系统分成几个部分，java 部分主要是用来进行开发调试使用的，爬虫没用选择使用 java 来实现。java 部分使用了基于 jsoup 的静态网页分析框架。另外，部分数据库 schema 是通过 java 的代码生成的 SQL 语句。Python 部分分成某宝和某东两种爬虫方式。这两个网站的爬虫方式有所区别，但是也可以基本覆盖你需要爬虫的网页类型。

具体的项目结构，

```
-- data:        Excel 处理之后的部分数据表格
-- java-spider: 包含数据库读写的 java 程序，用来自动生成数据库 schema，包含 jsoup 爬虫示例
-- python:      某东和某宝的爬虫系统
-- shell:       用来在服务器上面部署的定时脚本
-- resources:   一些相关的资料和 API
-- sql：        数据库表的创建语句
```

另外，这个系统没用使用任何框架比如 Scrapy. 

## 2、具体的设计

系统是使用 Linux 系统的 Cron 服务采用定时的方式执行的，如上所述，将商品的信息分开抓取。如果要分析代码，从 shell 脚本开始查看即可。关于具体的环境和配置中可能存在的一些问题，可以参考 python 目录下面的 README 文件。

### 2.1 某东的抓取系统设计

这里用到了两种持久化方式，分别是**关系型数据库 MySQL** 以及**非关系型数据库 Redis**. MySQL 用来记录某个商品的信息、分类信息、品牌信息和折扣信息。Redis 通过哈希表数据结构存储某个商品在某个时间段的价格信息。这也是为了后续使用数据库的时候的性能和方便的考虑。

首先抓取需要抓取信息的品类的信息，这里将所有的品类信息存储到 gt_channel 数据库表中。这里用到了**乐观锁设计**，可以拓展多个系统，每个系统执行的时候首先从数据库中根据上次处理时间找到当天需要抓取数据的品类，然后对该品类的信息进行抓取。这样，只要数据源唯一，就可以通过增加服务器提升抓取数据的数量。

某东的数据抓起来比较简单，有些信息是通过接口获取的，有些是通过静态的网页分析就可以拿到的。所以，我们完全可以根据具体的接口的详情设计系统。比如，当你使用一些框架的时候，对某个产品你需要依次获取它的价格、折扣和详情信息。但是对于详情信息这种数据，没必要多次获取。对于折扣信息，我们可以通过一个接口获取多个产品的信息，如果对每个产品请求一次，请求太多，被 block 的风险也高。

### 2.2 某宝的抓取设计

某宝的反爬做得更好，商品信息是通过动态网页的形式下发的，抓取比较困难。而且查看商品信息的时候需要使用手机验证码登录之后才能查看商品的完整的信息。所以，这需要用到动态网页信息抓取的框架。当前，比较好用的两个框架分别是，**pyppeteer** 和 selenium. 但是后者使用起来配置环境比较麻烦，前者更加简单。前者通过 HeadlessChrome 实现，是按照基于 javascript 的 puppeteer 实现的非官方的 Python 框架。这里不介绍它的使用了，可以参考 `tb.py` 这个文件来了解如何使用的。

### 2.3 关于防爬和 UserAgent

网站会在域名下的 **robots.txt** 文件中声明自己的爬虫许可，比如 Bing 的是 `https://cn.bing.com/robots.txt`. 关于具体的含义可以查看相关的文章自行了解。

对 UserAgent 被禁的情形。开源的库 fake_useragent 可以用来动态获取 UserAgent，但是这并不总是有效。所以，这里我用了 useragent.py 用来随机获取 UserAgent. 

## 其他

开发这个系统的时候，我看了一些关于爬虫的书籍，不过感觉都跟小孩玩过家家一样，并不具备实际应用的可能性。这个项目主要是一个系统性的设计。我觉得这是写代码最有意思的地方。当然这个项目还有需要完善的地方。

该项目仅供交流使用。
