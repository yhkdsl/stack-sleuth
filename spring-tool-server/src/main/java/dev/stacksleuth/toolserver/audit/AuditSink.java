package dev.stacksleuth.toolserver.audit;

import java.util.List;

public interface AuditSink {

    void record(AuditEvent event);

    List<AuditEvent> events();
}
