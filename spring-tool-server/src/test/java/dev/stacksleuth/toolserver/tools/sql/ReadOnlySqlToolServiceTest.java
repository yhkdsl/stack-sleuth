package dev.stacksleuth.toolserver.tools.sql;

import static org.assertj.core.api.Assertions.assertThat;

import dev.stacksleuth.toolserver.config.ToolServerProperties;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
class ReadOnlySqlToolServiceTest {

    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:17.5-alpine");

    private JdbcTemplate jdbcTemplate;
    private ReadOnlySqlToolService service;

    @BeforeEach
    void setUp() {
        DriverManagerDataSource dataSource = new DriverManagerDataSource(
            POSTGRES.getJdbcUrl(),
            POSTGRES.getUsername(),
            POSTGRES.getPassword()
        );
        jdbcTemplate = new JdbcTemplate(dataSource);
        jdbcTemplate.execute("DROP TABLE IF EXISTS users");
        jdbcTemplate.execute("""
            CREATE TABLE users (
                id bigint PRIMARY KEY,
                account_status text NOT NULL,
                profile_img text
            )
            """);
        jdbcTemplate.update(
            "INSERT INTO users (id, account_status, profile_img) VALUES (?, ?, ?)",
            42,
            "active",
            null
        );

        ReadOnlySqlGuardrail guardrail = new ReadOnlySqlGuardrail(
            new ToolServerProperties(true, "test-token", 50, 100, 1000, "unused.log")
        );
        service = new ReadOnlySqlToolService(guardrail, jdbcTemplate);
    }

    @Test
    void executesGuardedSelectAndPreservesNullValues() {
        ReadOnlySqlResponse response = service.run(
            new ReadOnlySqlRequest("SELECT id, account_status, profile_img FROM users WHERE id = 42")
        );

        assertThat(response.status()).isEqualTo("ok");
        assertThat(response.columns()).containsExactly("id", "account_status", "profile_img");
        assertThat(response.rows()).singleElement().satisfies(row -> {
            assertThat(row).containsEntry("id", 42L);
            assertThat(row).containsEntry("account_status", "active");
            assertThat(row).containsKey("profile_img");
            assertThat(row.get("profile_img")).isNull();
        });
        assertThat(response.rowCount()).isEqualTo(1);
        assertThat(response.executionTimeMs()).isGreaterThanOrEqualTo(0);
    }
}
