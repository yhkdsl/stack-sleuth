package dev.stacksleuth.toolserver.audit;

public record AuditEvent(
    String traceId,
    String requestId,
    String toolName,
    String status,
    long latencyMs,
    String rejectionReason
) {
}
