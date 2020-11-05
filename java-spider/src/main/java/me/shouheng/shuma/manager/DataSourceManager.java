package me.shouheng.shuma.manager;

import com.alibaba.druid.pool.DruidDataSource;
import com.mysql.cj.jdbc.Driver;
import lombok.extern.slf4j.Slf4j;
import me.shouheng.shuma.SpiderApp;
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
import java.sql.SQLException;

@Slf4j
public class DataSourceManager {

    private static volatile DataSourceManager sourceManager;

    private DruidDataSource source;

    private SpiderApp.SpiderEnv env;

    public static DataSourceManager getInstance(SpiderApp.SpiderEnv env) {
        if (sourceManager == null) {
            synchronized (DataSourceManager.class) {
                if (sourceManager == null) {
                    sourceManager = new DataSourceManager(env);
                }
            }
        }
        return sourceManager;
    }

    private DataSourceManager(SpiderApp.SpiderEnv env) {
        this.env = env;
        initDataSource();
    }

    private void initDataSource() {
        source = new DruidDataSource();
        try {
            source.setDriver(new Driver());
        } catch (SQLException e) {
            e.printStackTrace();
        }
        source.setInitialSize(1);
        source.setMinIdle(1);
        source.setMaxWait(10_000);
        source.setTimeBetweenEvictionRunsMillis(60_000);
        source.setMinEvictableIdleTimeMillis(300_000);
        source.setTestWhileIdle(true);
        source.setTestOnBorrow(true);
        source.setTestOnReturn(false);
        source.setPoolPreparedStatements(true);
        source.setMaxPoolPreparedStatementPerConnectionSize(20);
        source.setDefaultAutoCommit(true);
        source.setValidationQuery("select 1");
        switch (env) {
            case prod:
                break;
            case test:
                break;
            case local:
                source.setUrl("jdbc:mysql://localhost:3306/beauty_dev?serverTimezone=GMT%2B8&allowMultiQueries=true");
                source.setUsername("root");
                source.setPassword("***REMOVED***");
                break;
        }
    }

    public SqlSession getSqlSession() throws IOException {
        String resource = "mybatis/mybatis-config.xml";
        InputStream inputStream = Resources.getResourceAsStream(resource);
        SqlSessionFactory sqlSessionFactory = new SqlSessionFactoryBuilder().build(inputStream);
        TransactionFactory transactionFactory = new JdbcTransactionFactory();
        Environment environment = new Environment("development", transactionFactory, source);
        Configuration configuration = sqlSessionFactory.getConfiguration();
        configuration.getTypeHandlerRegistry().register("me.shouheng.shuma.dao.handler");
        configuration.getTypeAliasRegistry().registerAliases("me.shouheng.shuma.model");
        configuration.setEnvironment(environment);
        return sqlSessionFactory.openSession();
    }
}
