package dev.stacksleuth.toolserver.config;

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

    @Bean
    DataSource toolDataSource(ToolDatabaseProperties properties) {
        return DataSourceBuilder.create()
            .url(properties.url())
            .username(properties.username())
            .password(properties.password())
            .build();
    }

    @Bean
    JdbcTemplate toolJdbcTemplate(DataSource toolDataSource) {
        return new JdbcTemplate(toolDataSource);
    }
}
