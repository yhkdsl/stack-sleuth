package dev.stacksleuth.toolserver.tools.logs;

import static org.assertj.core.api.Assertions.assertThat;

import dev.stacksleuth.toolserver.config.ToolServerProperties;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class LogSearchToolServiceTest {

    @TempDir
    Path tempDir;

    @Test
    void filtersMatchesByLogTimestampAndPreservesTimestamp() throws Exception {
        Path logFile = tempDir.resolve("app.log");
        Files.writeString(logFile, """
            2026-06-24T00:20:00Z ERROR recent failure
            2026-06-23T22:00:00Z ERROR old failure
            2026-06-24T00:25:00Z INFO healthy
            """);
        ToolServerProperties properties = new ToolServerProperties(
            true,
            "test-token",
            50,
            100,
            1000,
            logFile.toString()
        );
        Clock clock = Clock.fixed(Instant.parse("2026-06-24T00:30:00Z"), ZoneOffset.UTC);
        LogSearchToolService service = new LogSearchToolService(properties, clock);

        LogSearchResponse response = service.search(new LogSearchRequest("ERROR", 60, 10));

        assertThat(response.matches()).singleElement().satisfies(match -> {
            assertThat(match.timestamp()).isEqualTo(Instant.parse("2026-06-24T00:20:00Z"));
            assertThat(match.level()).isEqualTo("ERROR");
            assertThat(match.message()).isEqualTo("recent failure");
        });
    }
}
