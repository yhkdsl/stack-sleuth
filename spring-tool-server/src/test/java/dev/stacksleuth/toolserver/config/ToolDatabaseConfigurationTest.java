package dev.stacksleuth.toolserver.config;

import static org.assertj.core.api.Assertions.assertThat;

import com.zaxxer.hikari.HikariDataSource;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;

class ToolDatabaseConfigurationTest {

    @Test
    void configuresABoundedDatabaseConnectionTimeout() {
        ToolDatabaseProperties properties = new ToolDatabaseProperties(
            true,
            "jdbc:postgresql://localhost:5432/stacksleuth",
            "stacksleuth_reader",
            "unused"
        );

        DataSource dataSource = new ToolDatabaseConfiguration().toolDataSource(properties);

        assertThat(dataSource).isInstanceOfSatisfying(HikariDataSource.class, hikariDataSource -> {
            try (hikariDataSource) {
                assertThat(hikariDataSource.getConnectionTimeout()).isEqualTo(2_000L);
                assertThat(hikariDataSource.getMinimumIdle()).isZero();
            }
        });
    }
}
