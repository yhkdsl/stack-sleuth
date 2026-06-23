package dev.stacksleuth.toolserver.tools.health;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.time.Instant;
import org.springframework.stereotype.Service;

@Service
public class HealthToolService {

    public HealthResponse check(HealthRequest request) {
        HealthResponse.JvmHealth jvm = null;
        if (request.includeJvm()) {
            MemoryMXBean memory = ManagementFactory.getMemoryMXBean();
            jvm = new HealthResponse.JvmHealth(
                memory.getHeapMemoryUsage().getUsed(),
                memory.getHeapMemoryUsage().getMax(),
                Runtime.getRuntime().availableProcessors()
            );
        }

        HealthResponse.DbPoolHealth dbPool = null;
        if (request.includeDbPool()) {
            dbPool = new HealthResponse.DbPoolHealth("not_configured", "Database pool is added in the demo data phase.");
        }

        return new HealthResponse("ok", Instant.now(), jvm, dbPool);
    }
}
