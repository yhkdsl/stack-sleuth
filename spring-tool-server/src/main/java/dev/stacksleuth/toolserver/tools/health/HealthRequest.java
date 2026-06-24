package dev.stacksleuth.toolserver.tools.health;

public record HealthRequest(boolean includeJvm, boolean includeDbPool) {
}
