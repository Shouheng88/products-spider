package me.shouheng.shuma.spider;

import org.jsoup.Connection;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;

import java.io.IOException;

public class JDSpider {

    public void parseCategories() throws IOException {
        Connection connection = Jsoup.connect("https://www.jd.com/allSort.aspx");
        Document document = connection.get();
        Elements elements = document.getElementsByClass("items");
        elements.select("dt");
    }
}
