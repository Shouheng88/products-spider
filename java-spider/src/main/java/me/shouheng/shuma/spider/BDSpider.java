package me.shouheng.shuma.spider;

import lombok.extern.slf4j.Slf4j;
import me.shouheng.shuma.utils.HttpUtils;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;

@Slf4j
public class BDSpider {

    public static void main(String...args) {
        HttpUtils.request("https://baike.baidu.com/item/%E7%A7%BB%E5%8A%A8%E5%B7%A5%E5%85%B7%E7%AE%B1", new HttpUtils.OnGetPageContentResult() {
            @Override
            public void onFail(String code, String message) {

            }

            @Override
            public void onSuccess(String content) {
                Document document = Jsoup.parse(content);
                log.debug("Document : {}", document);
                // 如果能找到下面的元素就当作存在该词条，否则当作不存在
                String summary = document.getElementsByClass("lemma-summary").text();
                String logo = document.select(".summary-pic img").attr("src");
            }
        });
    }
}
