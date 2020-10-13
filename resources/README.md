## 京东商品价格抓取

以 https://item.jd.com/100008348542.html 页面为例

访问该地址，可以从响应报文中，查看到所有的 sku

通过 skuId 可以对商品价格进行查询，以 100004770235 为例

访问 https://p.3.cn/prices/mgets?skuIds=100004770235 可以得到对应价格

```json
[{"p":"5499.00","op":"5499.00","cbf":"0","id":"J_100004770235","m":"5500.00"}]
```

该接口支持多个 sku 查询，如果需要更具体的信息，可以访问

https://c0.3.cn/stock?skuId=100004770235&area=12_904_3373_0&venderId=1000000127&cat=9987,653,655

可以得到更为具体的商品信息

在上述的链接中，area 是配送地址，可以由 https://static.360buyimg.com/item/assets/address/area.js 查询到全量信息

venderId 是店铺的 id，cat 是产品的具体分类

上面得到的产品价格，不包括促销与优惠信息，如果需要查询到手价，还需要计算促销与优惠

访问 https://cd.jd.com/promotion/v2?skuId=100008348542&area=12_904_3373_0&venderId=1000000127&cat=9987,653,655 得到结果

其中 skuCoupon 是优惠券，pickOneTag 是促销

如果需要查询促销更具体的信息，可以查看

https://wq.jd.com/commodity/promo/get?skuid=100004770235
