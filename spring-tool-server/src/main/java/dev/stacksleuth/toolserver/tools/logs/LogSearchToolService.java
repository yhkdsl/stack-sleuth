package dev.stacksleuth.toolserver.tools.logs;

import dev.stacksleuth.toolserver.config.ToolServerProperties;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;
import org.springframework.stereotype.Service;

@Service
public class LogSearchToolService {

    private final ToolServerProperties properties;
    private final Clock clock;

    public LogSearchToolService(ToolServerProperties properties, Clock clock) {
        this.properties = properties;
        this.clock = clock;
    }

    public LogSearchResponse search(LogSearchRequest request) {
        Path logPath = Path.of(properties.sampleLogPath());
        if (!Files.exists(logPath)) {
            return new LogSearchResponse("log_file_not_configured", request.keyword(), 0, List.of());
        }

        Instant cutoff = clock.instant().minusSeconds(request.sinceMinutes() * 60L);
        try (Stream<String> lines = Files.lines(logPath)) {
            List<LogSearchResponse.LogMatch> matches = lines
                .map(LogSearchToolService::parseLine)
                .flatMap(Optional::stream)
                .filter(match -> !match.timestamp().isBefore(cutoff))
                .filter(match -> match.message().contains(request.keyword()) || match.level().contains(request.keyword()))
                .limit(Math.min(request.limit(), properties.logMaxMatches()))
                .toList();
            return new LogSearchResponse("ok", request.keyword(), matches.size(), matches);
        } catch (IOException exception) {
            return new LogSearchResponse("log_file_unavailable", request.keyword(), 0, List.of());
        }
    }

    private static Optional<LogSearchResponse.LogMatch> parseLine(String line) {
        String[] parts = line.strip().split("\\s+", 3);
        if (parts.length < 3) {
            return Optional.empty();
        }

        try {
            return Optional.of(new LogSearchResponse.LogMatch(
                Instant.parse(parts[0]),
                parts[1],
                truncate(parts[2])
            ));
        } catch (RuntimeException exception) {
            return Optional.empty();
        }
    }

    private static String truncate(String message) {
        if (message.length() <= 500) {
            return message;
        }
        return message.substring(0, 500);
    }
}
