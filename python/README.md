
# 基本环境配置

- requests:
  - install: `pip install requests`
- BeautifulSoup
    install : `pip install beautifulsoup4`
- Redis
    install : `pip install redis`
- Selenium
    install : `pip install selenium`
- pyppeteer
    install : `pip install pyppeteer`
    then : `pyppeteer-install`
- xlwt & xlrd
    install : `pip install xlwt`
    install : `pip install xlrd`
- pymysql:
    install : `pip install pymysql`
    可能需要 ：`pip install cryptography`
- fake-useragent，用来模拟 useragent
    install : `pip install fake-useragent`
- jieba
  - install : `pip install jieba`
- pip 超时问题：
  - 使用 pip 的时候增加参数以指定镜像地址，如 `pip install redis -i https://pypi.douban.com/simple`

## tor

在服务器安装 tor [centos]: `yum install tor`，如果遇到了 Python2 和 python3 的问题，可以通过修改文件的第一行代码为 `#!/usr/bin/env python2.7` 解决

然后修改 /etc/tor/torrc 文件，并追加几行代码：
```
Socks5Proxy 192.168.159.1:1080 # 使用ss代理连接tor桥
CookieAuthentication 1         # 开启cookies
ControlPort 9051               # 配置通讯端口
```

重启 tor：`systemctl restart tor`

测试，访问 `http://checkip.amzaonaws.com` 返回公网 ip 地址，

```python
# 首先是无代理的方式
print(requests.get("http://checkip.amazonaws.com").text)
# 然后是代理的方式
proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
print(requests.get("http://checkip.amazonaws.com", proxies=proxies).text)
```

  - install： `pip install pysocks`

## pyppeteer 

在 Linux 系统上安装可能会出现缺少 so 文件的情况，此时可以参考 puppeteer 项目安装，

https://github.com/puppeteer/puppeteer/blob/main/docs/troubleshooting.md#chrome-headless-doesnt-launch-on-unix

即到 chrome 的安装目录下面执行 `ldd chrome | grep not` 查看缺少的文件

缺少 `libatk-bridge-2.0.so.0` 等 so 的情况，参考 https://github.com/puppeteer/puppeteer/issues/1598 ：

```
sudo yum install libXcomposite libXcursor libXi libXtst libXScrnSaver libXrandr atk at-spi2-atk gtk3 -y
```

# 淘宝的登录策略

之前看到有人说会有滑块，但是登录了几次没发现滑块，后来登录次数多了出现了滑块。当前（2020-11-04）淘宝的登录策略猜测：

1. 一般情况下输入用户名和密码可以直接登录，

2. 如果在这个网络或者设备上面没有登录过，登录之后会进入环境监测页面，要求输入手机验证码才能最终完成登录。

3. 如果在一个设备上面登录的次数多了，则会出现滑块要求滑动之后进行登录。

所以，我的想法是，先在服务器（CentOS）上面进行验证码登录让系统记录在这个设备和网络上面登录过，然后熟悉了这个环境之后再使用账号+密码的方式进行登录。

## 已爬历史价格

[*]68, []71, []72, []73, []89
