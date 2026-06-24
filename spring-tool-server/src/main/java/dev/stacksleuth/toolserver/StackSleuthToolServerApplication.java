package dev.stacksleuth.toolserver;

import dev.stacksleuth.toolserver.config.ToolServerProperties;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;

@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)
@EnableConfigurationProperties(ToolServerProperties.class)
public class StackSleuthToolServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(StackSleuthToolServerApplication.class, args);
    }

    @Bean
    Clock toolServerClock(@Value("${stacksleuth.tool-server.clock-instant:}") String clockInstant) {
        if (clockInstant == null || clockInstant.isBlank()) {
            return Clock.systemUTC();
        }
        return Clock.fixed(Instant.parse(clockInstant), ZoneOffset.UTC);
    }
}
