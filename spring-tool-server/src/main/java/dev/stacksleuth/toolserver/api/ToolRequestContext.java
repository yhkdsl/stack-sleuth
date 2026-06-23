package dev.stacksleuth.toolserver.api;

import java.util.UUID;

public record ToolRequestContext(String traceId, String requestId) {

    public static ToolRequestContext fromHeaders(String traceId, String requestId) {
        String resolvedTraceId = isBlank(traceId) ? UUID.randomUUID().toString() : traceId;
        String resolvedRequestId = isBlank(requestId) ? UUID.randomUUID().toString() : requestId;
        return new ToolRequestContext(resolvedTraceId, resolvedRequestId);
    }

    private static boolean isBlank(String value) {
        return value == null || value.isBlank();
    }
}
