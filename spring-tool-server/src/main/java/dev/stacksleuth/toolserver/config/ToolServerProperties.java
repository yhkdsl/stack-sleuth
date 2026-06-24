package dev.stacksleuth.toolserver.config;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "stacksleuth.tool-server")
public record ToolServerProperties(
    boolean authEnabled,
    @NotBlank String token,
    @Min(1) int sqlMaxRows,
    @Min(1) int logMaxMatches,
    @Min(1) int auditMaxEvents,
    String sampleLogPath
) {

    public ToolServerProperties {
        if (token == null || token.isBlank()) {
            token = "local-dev-token";
        }
        if (sqlMaxRows <= 0) {
            sqlMaxRows = 50;
        }
        if (logMaxMatches <= 0) {
            logMaxMatches = 100;
        }
        if (auditMaxEvents <= 0) {
            auditMaxEvents = 1000;
        }
        if (sampleLogPath == null || sampleLogPath.isBlank()) {
            sampleLogPath = "../infra/sample-logs/app.log";
        }
    }
}
