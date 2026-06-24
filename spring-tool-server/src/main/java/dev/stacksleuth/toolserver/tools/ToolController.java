package dev.stacksleuth.toolserver.tools;

import dev.stacksleuth.toolserver.api.ToolException;
import dev.stacksleuth.toolserver.api.ToolRequestContext;
import dev.stacksleuth.toolserver.audit.AuditEvent;
import dev.stacksleuth.toolserver.audit.AuditSink;
import dev.stacksleuth.toolserver.tools.health.HealthRequest;
import dev.stacksleuth.toolserver.tools.health.HealthResponse;
import dev.stacksleuth.toolserver.tools.health.HealthToolService;
import dev.stacksleuth.toolserver.tools.logs.LogSearchRequest;
import dev.stacksleuth.toolserver.tools.logs.LogSearchResponse;
import dev.stacksleuth.toolserver.tools.logs.LogSearchToolService;
import dev.stacksleuth.toolserver.tools.sql.ReadOnlySqlRequest;
import dev.stacksleuth.toolserver.tools.sql.ReadOnlySqlResponse;
import dev.stacksleuth.toolserver.tools.sql.ReadOnlySqlToolService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.function.Supplier;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/tools")
public class ToolController {

    private final HealthToolService healthToolService;
    private final LogSearchToolService logSearchToolService;
    private final ReadOnlySqlToolService readOnlySqlToolService;
    private final AuditSink auditSink;

    public ToolController(
        HealthToolService healthToolService,
        LogSearchToolService logSearchToolService,
        ReadOnlySqlToolService readOnlySqlToolService,
        AuditSink auditSink
    ) {
        this.healthToolService = healthToolService;
        this.logSearchToolService = logSearchToolService;
        this.readOnlySqlToolService = readOnlySqlToolService;
        this.auditSink = auditSink;
    }

    @PostMapping("/health")
    ResponseEntity<HealthResponse> health(
        @Valid @RequestBody HealthRequest request,
        HttpServletRequest servletRequest
    ) {
        return execute("check_server_health", servletRequest, () -> healthToolService.check(request));
    }

    @PostMapping("/logs/search")
    ResponseEntity<LogSearchResponse> searchLogs(
        @Valid @RequestBody LogSearchRequest request,
        HttpServletRequest servletRequest
    ) {
        return execute("search_error_logs", servletRequest, () -> logSearchToolService.search(request));
    }

    @PostMapping("/sql/read-only")
    ResponseEntity<ReadOnlySqlResponse> readOnlySql(
        @Valid @RequestBody ReadOnlySqlRequest request,
        HttpServletRequest servletRequest
    ) {
        return execute("run_read_only_query", servletRequest, () -> readOnlySqlToolService.run(request));
    }

    private <T> ResponseEntity<T> execute(String toolName, HttpServletRequest request, Supplier<T> supplier) {
        ToolRequestContext context = ToolRequestContext.fromRequest(request);
        long startedAt = System.nanoTime();
        String status = "success";
        String rejectionReason = null;
        try {
            T body = supplier.get();
            return ResponseEntity.ok()
                .header("X-Trace-Id", context.traceId())
                .header("X-Request-Id", context.requestId())
                .body(body);
        } catch (ToolException exception) {
            status = "rejected";
            rejectionReason = exception.code();
            throw exception;
        } catch (RuntimeException exception) {
            status = "failed";
            rejectionReason = exception.getClass().getSimpleName();
            throw exception;
        } finally {
            long latencyMs = (System.nanoTime() - startedAt) / 1_000_000;
            auditSink.record(new AuditEvent(context.traceId(), context.requestId(), toolName, status, latencyMs, rejectionReason));
        }
    }
}
