package me.shouheng.shuma.spider;

import lombok.extern.slf4j.Slf4j;
import me.shouheng.shuma.utils.HttpUtils;
import org.jsoup.Connection;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;

import java.io.IOException;

@Slf4j
public class JDSpider {

    public void parseCategories() throws IOException {
        Connection connection = Jsoup.connect("https://www.jd.com/allSort.aspx");
        Document document = connection.get();
        Elements elements = document.getElementsByClass("items");
        elements.select("dt");
    }

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
}
