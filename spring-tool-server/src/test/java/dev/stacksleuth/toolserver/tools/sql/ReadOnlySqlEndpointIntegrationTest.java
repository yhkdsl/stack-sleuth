package dev.stacksleuth.toolserver.tools.sql;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import dev.stacksleuth.toolserver.audit.AuditSink;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest
@AutoConfigureMockMvc
@Testcontainers
class ReadOnlySqlEndpointIntegrationTest {

    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:17.5-alpine")
        .withDatabaseName("test")
        .withInitScript("sql/read-only-integration-init.sql");

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("stacksleuth.tool-server.token", () -> "test-token");
        registry.add("stacksleuth.tool-server.database.enabled", () -> true);
        registry.add("stacksleuth.tool-server.database.url", POSTGRES::getJdbcUrl);
        registry.add("stacksleuth.tool-server.database.username", () -> "stacksleuth_test_reader");
        registry.add("stacksleuth.tool-server.database.password", () -> "test-reader-password");
    }

    @Autowired
    MockMvc mockMvc;

    @Autowired
    AuditSink auditSink;

    @Test
    void healthEndpointReportsAvailableReadOnlyDatabase() throws Exception {
        mockMvc.perform(post("/internal/tools/health")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"includeJvm\":false,\"includeDbPool\":true}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("ok"))
            .andExpect(jsonPath("$.dbPool.status").value("available"))
            .andExpect(jsonPath("$.dbPool.detail").value("Read-only database connection is available."));
    }

    @Test
    void endpointExecutesAsRestrictedReaderAccount() throws Exception {
        mockMvc.perform(post("/internal/tools/sql/read-only")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"sql\":\"SELECT current_user AS database_user, id, account_status, profile_img FROM users WHERE id = 42\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("ok"))
            .andExpect(jsonPath("$.rowCount").value(1))
            .andExpect(jsonPath("$.rows[0].database_user").value("stacksleuth_test_reader"))
            .andExpect(jsonPath("$.rows[0].id").value(42))
            .andExpect(jsonPath("$.rows[0].account_status").value("active"))
            .andExpect(jsonPath("$.rows[0].profile_img").isEmpty());
    }

    @Test
    void databaseExecutionFailureIsAuditedAsFailed() throws Exception {
        int eventCount = auditSink.events().size();

        mockMvc.perform(post("/internal/tools/sql/read-only")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"sql\":\"SELECT * FROM missing_table\"}"))
            .andExpect(status().isBadGateway())
            .andExpect(jsonPath("$.code").value("SQL_EXECUTION_FAILED"));

        assertThat(auditSink.events().subList(eventCount, auditSink.events().size()))
            .singleElement()
            .satisfies(event -> {
                assertThat(event.status()).isEqualTo("failed");
                assertThat(event.rejectionReason()).isEqualTo("SQL_EXECUTION_FAILED");
            });
    }
}
