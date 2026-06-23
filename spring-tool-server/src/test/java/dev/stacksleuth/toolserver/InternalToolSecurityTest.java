package dev.stacksleuth.toolserver;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import dev.stacksleuth.toolserver.audit.AuditSink;
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
class InternalToolSecurityTest {

    @Autowired
    MockMvc mockMvc;

    @Autowired
    AuditSink auditSink;

    @Test
    void rejectsMissingInternalToken() throws Exception {
        mockMvc.perform(post("/internal/tools/health")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"includeJvm\":true,\"includeDbPool\":true}"))
            .andExpect(status().isUnauthorized())
            .andExpect(jsonPath("$.code").value("UNAUTHORIZED_TOOL_REQUEST"));
    }

    @Test
    void rejectsInvalidInternalToken() throws Exception {
        mockMvc.perform(post("/internal/tools/health")
                .header("X-Tool-Server-Token", "wrong-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"includeJvm\":true,\"includeDbPool\":true}"))
            .andExpect(status().isUnauthorized())
            .andExpect(jsonPath("$.code").value("UNAUTHORIZED_TOOL_REQUEST"));
    }

    @Test
    void validTokenAllowsToolExecutionAndAuditsRequest() throws Exception {
        mockMvc.perform(post("/internal/tools/health")
                .header("X-Tool-Server-Token", "test-token")
                .header("X-Trace-Id", "trace-123")
                .header("X-Request-Id", "request-456")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"includeJvm\":true,\"includeDbPool\":true}"))
            .andExpect(status().isOk())
            .andExpect(header().string("X-Trace-Id", "trace-123"))
            .andExpect(header().exists("X-Request-Id"))
            .andExpect(jsonPath("$.status").value("ok"))
            .andExpect(jsonPath("$.jvm.heapUsedBytes").isNumber())
            .andExpect(jsonPath("$.environment").doesNotExist());

        assertThat(auditSink.events())
            .anySatisfy(event -> {
                assertThat(event.toolName()).isEqualTo("check_server_health");
                assertThat(event.traceId()).isEqualTo("trace-123");
                assertThat(event.requestId()).isEqualTo("request-456");
                assertThat(event.status()).isEqualTo("success");
                assertThat(event.rejectionReason()).isNull();
            });
    }
}
