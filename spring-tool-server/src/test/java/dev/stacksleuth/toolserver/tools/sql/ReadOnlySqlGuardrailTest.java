package dev.stacksleuth.toolserver.tools.sql;

import static org.assertj.core.api.Assertions.assertThat;

import dev.stacksleuth.toolserver.config.ToolServerProperties;
import org.junit.jupiter.api.Test;

class ReadOnlySqlGuardrailTest {

    private final ReadOnlySqlGuardrail guardrail = new ReadOnlySqlGuardrail(
        new ToolServerProperties(true, "test-token", 50, 100, 1000, "unused.log")
    );

    @Test
    void wrapsSelectWithServerSideRowLimit() {
        PreparedReadOnlyQuery query = guardrail.prepare("SELECT id FROM users");

        assertThat(query.sql()).isEqualTo("SELECT * FROM (SELECT id FROM users) stacksleuth_query LIMIT 50");
        assertThat(query.maxRows()).isEqualTo(50);
    }

    @Test
    void serverSideLimitCapsExistingLargerLimit() {
        PreparedReadOnlyQuery query = guardrail.prepare("SELECT id FROM users LIMIT 500");

        assertThat(query.sql()).endsWith("LIMIT 50");
        assertThat(query.maxRows()).isEqualTo(50);
    }
}
