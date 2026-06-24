package dev.stacksleuth.toolserver.tools.sql;

import jakarta.validation.constraints.NotBlank;

public record ReadOnlySqlRequest(@NotBlank String sql) {
}
