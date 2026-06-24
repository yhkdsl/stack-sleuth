package dev.stacksleuth.toolserver.tools.sql;

import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ReadOnlySqlToolService {

    private final ReadOnlySqlGuardrail guardrail;

    public ReadOnlySqlToolService(ReadOnlySqlGuardrail guardrail) {
        this.guardrail = guardrail;
    }

    public ReadOnlySqlResponse run(ReadOnlySqlRequest request) {
        long startedAt = System.nanoTime();
        guardrail.prepare(request.sql());
        long executionTimeMs = (System.nanoTime() - startedAt) / 1_000_000;
        return new ReadOnlySqlResponse("database_not_configured", List.of(), List.of(), 0, executionTimeMs);
    }
}
