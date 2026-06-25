package dev.stacksleuth.toolserver.config;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Clock;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = "stacksleuth.tool-server.clock-instant=2026-06-24T03:00:00Z")
class FixedClockConfigurationTest {

    @Autowired
    Clock clock;

    @Test
    void usesConfiguredClockForDeterministicDemoWindows() {
        assertThat(clock.instant()).isEqualTo(Instant.parse("2026-06-24T03:00:00Z"));
    }
}
