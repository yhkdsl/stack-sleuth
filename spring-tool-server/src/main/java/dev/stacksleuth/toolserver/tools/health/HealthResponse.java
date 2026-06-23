package dev.stacksleuth.toolserver.tools.health;

import java.time.Instant;

public record HealthResponse(
    String status,
    Instant checkedAt,
    JvmHealth jvm,
    DbPoolHealth dbPool
) {

    public record JvmHealth(long heapUsedBytes, long heapMaxBytes, int availableProcessors) {
    }

    public record DbPoolHealth(String status, String detail) {
    }
}
