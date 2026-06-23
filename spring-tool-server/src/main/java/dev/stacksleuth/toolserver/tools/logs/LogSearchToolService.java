package dev.stacksleuth.toolserver.tools.logs;

import dev.stacksleuth.toolserver.config.ToolServerProperties;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.stream.Stream;
import org.springframework.stereotype.Service;

@Service
public class LogSearchToolService {

    private final ToolServerProperties properties;

    public LogSearchToolService(ToolServerProperties properties) {
        this.properties = properties;
    }

    public LogSearchResponse search(LogSearchRequest request) {
        Path logPath = Path.of(properties.sampleLogPath());
        if (!Files.exists(logPath)) {
            return new LogSearchResponse("log_file_not_configured", request.keyword(), 0, List.of());
        }

        try (Stream<String> lines = Files.lines(logPath)) {
            List<LogSearchResponse.LogMatch> matches = lines
                .filter(line -> line.contains(request.keyword()))
                .limit(Math.min(request.limit(), properties.logMaxMatches()))
                .map(line -> new LogSearchResponse.LogMatch(Instant.now(), inferLevel(line), truncate(line)))
                .toList();
            return new LogSearchResponse("ok", request.keyword(), matches.size(), matches);
        } catch (IOException exception) {
            return new LogSearchResponse("log_file_unavailable", request.keyword(), 0, List.of());
        }
    }

    private static String inferLevel(String line) {
        if (line.contains("ERROR")) {
            return "ERROR";
        }
        if (line.contains("WARN")) {
            return "WARN";
        }
        return "INFO";
    }

    private static String truncate(String line) {
        if (line.length() <= 500) {
            return line;
        }
        return line.substring(0, 500);
    }
}
