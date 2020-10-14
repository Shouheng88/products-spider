package me.shouheng.shuma.spider;

import lombok.extern.slf4j.Slf4j;
import me.shouheng.shuma.utils.HttpUtils;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
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
                Elements pageCount = document.getElementById("J_bottomPage").getElementsByClass("p-skip");
                log.debug("PageCountElements : {}", pageCount);
                // 解析最大页码信息
                document.getElementById("J_topPage").getElementsByTag("span").text();
                // 解析产品列表，返回一个列表，包含大概 30 个元素
                Elements items = document.getElementById("J_goodsList").getElementsByClass("gl-item");
                for (Element item : items) {
                    String url = item.getElementsByClass("p-img").select("a").attr("href"); // 产品的链接地址
                    String cover = item.getElementsByClass("p-img").select("img").attr("data-lazy-img"); // 或者 src，两个一起吧，哪个有值用哪个
                    String priceType = item.getElementsByClass("p-price").select("em").text(); // 价格符号，譬如 ￥ 等
                    String price = item.getElementsByClass("p-price").select("i").text(); // 价格，浮点数
                    String promo = item.getElementsByClass("p-name").select("a").attr("title"); // 提示
                    String name = item.getElementsByClass("p-name").select("a").select("em").text(); // 名称
                    // 评论的总数没有
                    String commitLink = item.getElementsByClass("p-commit").select("a").attr("href"); // 评论的地址，没有评论的数量
                    // 商店信息没有
                    Elements icons = item.getElementsByClass("p-icons").select("i");
                    icons.forEach(Element::text); // icons
                }
                // 解析品牌列表
                Elements brandTags = document.select("li[id^=brand]");
                for (Element brandTag : brandTags) {
                    String dataInitial = brandTag.attr("data-initial");
                    String link = brandTag.select("a").attr("href");
                    String name = brandTag.select("a").attr("title");
                    String logo = brandTag.select("img").attr("src");
                }
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
