package me.shouheng.shuma.spider;

import org.jsoup.Connection;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;

import java.io.IOException;

public class TBSpider {

    public void SpiderCategories() throws IOException {
        Connection connection = Jsoup.connect("http://www.taobao.com/tbhome/page/market-list");
        Document document = connection.get();
        Elements elements = document.getElementsByClass("items");
        elements.select("dt");
    }
}
