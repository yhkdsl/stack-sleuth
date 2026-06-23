package dev.stacksleuth.toolserver.tools.logs;

import java.time.Instant;
import java.util.List;

public record LogSearchResponse(
    String status,
    String keyword,
    int matchCount,
    List<LogMatch> matches
) {

    public record LogMatch(Instant timestamp, String level, String message) {
    }
}
