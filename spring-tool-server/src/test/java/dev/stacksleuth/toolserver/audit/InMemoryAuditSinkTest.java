package dev.stacksleuth.toolserver.audit;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class InMemoryAuditSinkTest {

    @Test
    void evictsOldestEventsWhenCapacityIsReached() {
        InMemoryAuditSink sink = new InMemoryAuditSink(2);
        sink.record(new AuditEvent("trace-1", "request-1", "tool", "success", 1, null));
        sink.record(new AuditEvent("trace-2", "request-2", "tool", "success", 1, null));
        sink.record(new AuditEvent("trace-3", "request-3", "tool", "success", 1, null));

        assertThat(sink.events())
            .extracting(AuditEvent::traceId)
            .containsExactly("trace-2", "trace-3");
    }
}
