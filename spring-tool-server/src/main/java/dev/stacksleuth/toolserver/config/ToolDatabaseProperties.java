package dev.stacksleuth.toolserver.config;

import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "stacksleuth.tool-server.database")
public record ToolDatabaseProperties(
    boolean enabled,
    @NotBlank String url,
    @NotBlank String username,
    @NotBlank String password
) {
}
