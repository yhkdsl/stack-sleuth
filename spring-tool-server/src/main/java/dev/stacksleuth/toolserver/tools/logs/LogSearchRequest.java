package dev.stacksleuth.toolserver.tools.logs;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

public record LogSearchRequest(
    @NotBlank String keyword,
    @Min(1) @Max(1440) int sinceMinutes,
    @Min(1) @Max(100) int limit
) {
}
