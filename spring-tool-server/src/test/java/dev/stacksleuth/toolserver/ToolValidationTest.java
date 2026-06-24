package dev.stacksleuth.toolserver;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = "stacksleuth.tool-server.token=test-token")
class ToolValidationTest {

    @Autowired
    MockMvc mockMvc;

    @Test
    void rejectsEmptyLogKeyword() throws Exception {
        mockMvc.perform(post("/internal/tools/logs/search")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"keyword\":\"\",\"sinceMinutes\":60,\"limit\":10}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("VALIDATION_FAILED"));
    }

    @Test
    void rejectsOverlyBroadLogLimit() throws Exception {
        mockMvc.perform(post("/internal/tools/logs/search")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"keyword\":\"ERROR\",\"sinceMinutes\":60,\"limit\":101}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("VALIDATION_FAILED"));
    }

    @Test
    void blocksDestructiveSql() throws Exception {
        mockMvc.perform(post("/internal/tools/sql/read-only")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"sql\":\"DELETE FROM users\"}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("SQL_WRITE_BLOCKED"));
    }

    @Test
    void blocksMultiStatementSql() throws Exception {
        mockMvc.perform(post("/internal/tools/sql/read-only")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"sql\":\"SELECT id FROM users; DELETE FROM users\"}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("SQL_MULTI_STATEMENT_BLOCKED"));
    }

    @Test
    void blocksSelectInto() throws Exception {
        mockMvc.perform(post("/internal/tools/sql/read-only")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"sql\":\"SELECT * INTO backup_users FROM users\"}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("SQL_WRITE_BLOCKED"));
    }

    @Test
    void blocksDataModifyingCte() throws Exception {
        mockMvc.perform(post("/internal/tools/sql/read-only")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"sql\":\"WITH deleted AS (DELETE FROM users RETURNING *) SELECT * FROM deleted\"}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("SQL_WRITE_BLOCKED"));
    }

    @Test
    void blocksSelectForUpdate() throws Exception {
        mockMvc.perform(post("/internal/tools/sql/read-only")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"sql\":\"SELECT id FROM users FOR UPDATE\"}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("SQL_LOCK_BLOCKED"));
    }

    @Test
    void blocksLockingSelectInsideFromSubquery() throws Exception {
        mockMvc.perform(post("/internal/tools/sql/read-only")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"sql\":\"SELECT * FROM (SELECT id FROM users FOR UPDATE) locked_users\"}"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("SQL_LOCK_BLOCKED"));
    }

    @Test
    void returnsStructuredErrorForMalformedJson() throws Exception {
        mockMvc.perform(post("/internal/tools/health")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"includeJvm\":"))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("MALFORMED_JSON"));
    }
}
