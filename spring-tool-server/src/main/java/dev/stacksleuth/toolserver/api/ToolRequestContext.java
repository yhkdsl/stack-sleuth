package dev.stacksleuth.toolserver.api;

import jakarta.servlet.http.HttpServletRequest;
import java.util.UUID;

public record ToolRequestContext(String traceId, String requestId) {

    private static final String ATTRIBUTE = ToolRequestContext.class.getName();

    public static ToolRequestContext fromHeaders(String traceId, String requestId) {
        String resolvedTraceId = isBlank(traceId) ? UUID.randomUUID().toString() : traceId;
        String resolvedRequestId = isBlank(requestId) ? UUID.randomUUID().toString() : requestId;
        return new ToolRequestContext(resolvedTraceId, resolvedRequestId);
    }

    public static ToolRequestContext fromRequest(HttpServletRequest request) {
        Object existing = request.getAttribute(ATTRIBUTE);
        if (existing instanceof ToolRequestContext context) {
            return context;
        }

        ToolRequestContext context = fromHeaders(request.getHeader("X-Trace-Id"), request.getHeader("X-Request-Id"));
        request.setAttribute(ATTRIBUTE, context);
        return context;
    }

    public static String toolNameForPath(String path) {
        return switch (path) {
            case "/internal/tools/health" -> "check_server_health";
            case "/internal/tools/logs/search" -> "search_error_logs";
            case "/internal/tools/sql/read-only" -> "run_read_only_query";
            default -> "unknown_tool";
        };
    }

    private static boolean isBlank(String value) {
        return value == null || value.isBlank();
    }
}
