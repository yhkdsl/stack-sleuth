package dev.stacksleuth.toolserver.config;

import com.zaxxer.hikari.HikariDataSource;
import javax.sql.DataSource;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;

@Configuration(proxyBeanMethods = false)
@ConditionalOnProperty(
    prefix = "stacksleuth.tool-server.database",
    name = "enabled",
    havingValue = "true"
)
@EnableConfigurationProperties(ToolDatabaseProperties.class)
public class ToolDatabaseConfiguration {

    private static final long CONNECTION_TIMEOUT_MS = 2_000L;

    @Bean
    DataSource toolDataSource(ToolDatabaseProperties properties) {
        HikariDataSource dataSource = DataSourceBuilder.create()
            .type(HikariDataSource.class)
            .url(properties.url())
            .username(properties.username())
            .password(properties.password())
            .build();
        dataSource.setConnectionTimeout(CONNECTION_TIMEOUT_MS);
        dataSource.setMinimumIdle(0);
        return dataSource;
    }

    @Bean
    JdbcTemplate toolJdbcTemplate(DataSource toolDataSource) {
        return new JdbcTemplate(toolDataSource);
    }
}
