package me.shouheng.shuma.spider;

import lombok.extern.slf4j.Slf4j;
import me.shouheng.shuma.utils.HttpUtils;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;

/**
 * 京东爬虫，Java
 */
@Slf4j
public class JDSpider {

    /**
     * 抓取品类信息
     *
     * 能力描述：可以获取商品的每个品类的链接地址
     */
    public void parseCategories() {
        HttpUtils.request("https://www.jd.com/allSort.aspx", new HttpUtils.OnGetPageContentResult() {
            @Override
            public void onFail(String code, String message) {
                log.error("Failed {} {}", code, message);
            }

            @Override
            public void onSuccess(String content) {
                Document document = Jsoup.parse(content);
                Elements elements = document.getElementsByClass("items");
                elements.select("dt");
            }
        });
    }

    /**
     * 抓取京东某个品类的产品列表
     *
     * 能力描述：可以抓取每个列表展示的信息
     */
    public void parseItemLists() {
        HttpUtils.request("https://list.jd.com/list.html?cat=9987,653,655", new HttpUtils.OnGetPageContentResult() {
            @Override
            public void onFail(String code, String message) {
                log.error("Failed {} {}", code, message);
            }

            @Override
            public void onSuccess(String content) {
                Document document = Jsoup.parse(content);
                log.debug("Document : {}", document);
            }
        });
    }

    /**
     * 抓取京东某个产品的详情信息
     *
     * 能力描述：文字描述的产品信息可以直接获取到
     */
    public void parseItemPage() {
        HttpUtils.request("https://item.jd.com/100009082466.html", new HttpUtils.OnGetPageContentResult() {
            @Override
            public void onFail(String code, String message) {
                log.error("Failed {} {}", code, message);
            }

            @Override
            public void onSuccess(String content) {
                Document document = Jsoup.parse(content);
                log.debug("Document : {}", document);
            }
        });
    }
}
