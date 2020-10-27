
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
- fake-useragent，用来模拟 useragent
    install : `pip install fake-useragent`
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


