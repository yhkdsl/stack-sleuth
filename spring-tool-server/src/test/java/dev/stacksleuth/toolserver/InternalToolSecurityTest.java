package dev.stacksleuth.toolserver;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import dev.stacksleuth.toolserver.audit.AuditSink;
import java.util.List;
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
        int eventCount = auditSink.events().size();

        mockMvc.perform(post("/internal/tools/health")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"includeJvm\":true,\"includeDbPool\":true}"))
            .andExpect(status().isUnauthorized())
            .andExpect(jsonPath("$.code").value("UNAUTHORIZED_TOOL_REQUEST"));

        assertThat(auditSink.events().subList(eventCount, auditSink.events().size()))
            .singleElement()
            .satisfies(event -> {
                assertThat(event.toolName()).isEqualTo("check_server_health");
                assertThat(event.status()).isEqualTo("rejected");
                assertThat(event.rejectionReason()).isEqualTo("UNAUTHORIZED_TOOL_REQUEST");
            });
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

    @Test
    void validationFailureIsAudited() throws Exception {
        int eventCount = auditSink.events().size();

        mockMvc.perform(post("/internal/tools/logs/search")
                .header("X-Tool-Server-Token", "test-token")
                .header("X-Trace-Id", "trace-validation")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"keyword\":\"\",\"sinceMinutes\":60,\"limit\":10}"))
            .andExpect(status().isBadRequest());

        assertThat(auditSink.events().subList(eventCount, auditSink.events().size()))
            .singleElement()
            .satisfies(event -> {
                assertThat(event.traceId()).isEqualTo("trace-validation");
                assertThat(event.toolName()).isEqualTo("search_error_logs");
                assertThat(event.status()).isEqualTo("rejected");
                assertThat(event.rejectionReason()).isEqualTo("VALIDATION_FAILED");
            });
    }

    @Test
    void rawActuatorHealthIsNotExposed() throws Exception {
        mockMvc.perform(get("/actuator/health"))
            .andExpect(status().isNotFound());
    }

    @Test
    void policyRejectionReturnsTheSameTraceIdentifiersRecordedByAudit() throws Exception {
        int eventCount = auditSink.events().size();

        String responseTraceId = mockMvc.perform(post("/internal/tools/sql/read-only")
                .header("X-Tool-Server-Token", "test-token")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"sql\":\"DELETE FROM users\"}"))
            .andExpect(status().isBadRequest())
            .andExpect(header().exists("X-Trace-Id"))
            .andExpect(header().exists("X-Request-Id"))
            .andReturn()
            .getResponse()
            .getHeader("X-Trace-Id");

        List<dev.stacksleuth.toolserver.audit.AuditEvent> newEvents =
            auditSink.events().subList(eventCount, auditSink.events().size());
        assertThat(newEvents).singleElement()
            .extracting(event -> event.traceId())
            .isEqualTo(responseTraceId);
    }
}
