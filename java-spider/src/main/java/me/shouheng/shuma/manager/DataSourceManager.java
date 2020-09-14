package me.shouheng.shuma.manager;

import com.alibaba.druid.pool.DruidDataSource;
import com.mysql.cj.jdbc.Driver;
import me.shouheng.shuma.SpiderEnv;

import javax.sql.DataSource;
import java.sql.SQLException;

public class DataSourceManager {

    private static volatile DataSourceManager sourceManager;

    private DruidDataSource source;

    private SpiderEnv env;

    public static DataSourceManager getInstance(SpiderEnv env) {
        if (sourceManager == null) {
            synchronized (DataSourceManager.class) {
                if (sourceManager == null) {
                    sourceManager = new DataSourceManager(env);
                }
            }
        }
        return sourceManager;
    }

    private DataSourceManager(SpiderEnv env) {
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
                source.setUrl("jdbc:mysql://localhost:***REMOVED***/beauty_dev?serverTimezone=GMT%2B8&allowMultiQueries=true");
                source.setUsername("root");
                source.setPassword("***REMOVED***");
                break;
        }
    }

    public DataSource getDataSource() {
        return source;
    }
}
