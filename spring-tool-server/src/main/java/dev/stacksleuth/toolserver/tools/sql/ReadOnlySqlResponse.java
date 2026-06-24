package dev.stacksleuth.toolserver.tools.sql;

import java.util.List;
import java.util.Map;

public record ReadOnlySqlResponse(
    String status,
    List<String> columns,
    List<Map<String, Object>> rows,
    int rowCount,
    long executionTimeMs
) {
}
