package dev.stacksleuth.toolserver.tools.sql;

public record PreparedReadOnlyQuery(String sql, int maxRows) {
}
