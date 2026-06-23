package dev.stacksleuth.toolserver.audit;

import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class InMemoryAuditSink implements AuditSink {

    private static final Logger logger = LoggerFactory.getLogger(InMemoryAuditSink.class);

    private final List<AuditEvent> events = new ArrayList<>();

    @Override
    public synchronized void record(AuditEvent event) {
        events.add(event);
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
