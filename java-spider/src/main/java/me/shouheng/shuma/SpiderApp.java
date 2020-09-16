package me.shouheng.shuma;

import lombok.extern.slf4j.Slf4j;
import me.shouheng.shuma.spider.JDSpider;
import me.shouheng.shuma.spider.TBSpider;

import java.io.IOException;

@Slf4j
public class SpiderApp {

    public enum SpiderEnv {
        local, test, prod
    }

    public static void main(String... args) throws IOException {
        JDSpider jdSpider = new JDSpider();
        jdSpider.parseItemLists();
    }
}
