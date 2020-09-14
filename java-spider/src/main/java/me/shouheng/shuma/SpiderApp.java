package me.shouheng.shuma;

import lombok.extern.slf4j.Slf4j;
import me.shouheng.shuma.dao.TopicDAO;
import me.shouheng.shuma.manager.DataSourceManager;
import me.shouheng.shuma.model.po.Topic;
import org.apache.ibatis.io.Resources;
import org.apache.ibatis.mapping.Environment;
import org.apache.ibatis.session.Configuration;
import org.apache.ibatis.session.SqlSession;
import org.apache.ibatis.session.SqlSessionFactory;
import org.apache.ibatis.session.SqlSessionFactoryBuilder;
import org.apache.ibatis.transaction.TransactionFactory;
import org.apache.ibatis.transaction.jdbc.JdbcTransactionFactory;

import java.io.IOException;
import java.io.InputStream;

@Slf4j
public class SpiderApp {

    public static void main(String... args) throws IOException {
        String resource = "mybatis/mybatis-config.xml";
        InputStream inputStream = Resources.getResourceAsStream(resource);
        SqlSessionFactory sqlSessionFactory = new SqlSessionFactoryBuilder()
                .build(inputStream);
        TransactionFactory transactionFactory = new JdbcTransactionFactory();
        Environment environment = new Environment("development", transactionFactory,
                DataSourceManager.getInstance(SpiderEnv.local).getDataSource());
        Configuration configuration = sqlSessionFactory.getConfiguration();
        log.debug("{}", configuration.hasMapper(TopicDAO.class));
        configuration.getTypeHandlerRegistry().register("me.shouheng.shuma.dao.handler");
        configuration.getTypeAliasRegistry().registerAliases("me.shouheng.shuma.model");
        configuration.setEnvironment(environment);
        try (SqlSession session = sqlSessionFactory.openSession()) {
            TopicDAO mapper = session.getMapper(TopicDAO.class);
            Topic topic = mapper.selectByPrimaryKey(66L);
            log.debug("result {}", topic);
        }
    }
}
