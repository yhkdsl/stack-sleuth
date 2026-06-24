package dev.stacksleuth.toolserver.audit;

import dev.stacksleuth.toolserver.config.ToolServerProperties;
import java.util.ArrayDeque;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class InMemoryAuditSink implements AuditSink {

    private static final Logger logger = LoggerFactory.getLogger(InMemoryAuditSink.class);

    private final ArrayDeque<AuditEvent> events = new ArrayDeque<>();
    private final int capacity;

    @Autowired
    public InMemoryAuditSink(ToolServerProperties properties) {
        this(properties.auditMaxEvents());
    }

    InMemoryAuditSink(int capacity) {
        this.capacity = capacity;
    }

    @Override
    public synchronized void record(AuditEvent event) {
        if (events.size() == capacity) {
            events.removeFirst();
        }
        events.addLast(event);
        logger.info(
            "tool_audit traceId={} requestId={} toolName={} status={} latencyMs={} rejectionReason={}",
            event.traceId(),
            event.requestId(),
            event.toolName(),
            event.status(),
            event.latencyMs(),
            event.rejectionReason()
        );
    }

    @Override
    public synchronized List<AuditEvent> events() {
        return List.copyOf(events);
    }
}
