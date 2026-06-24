package dev.stacksleuth.toolserver.tools.health;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.time.Clock;
import javax.sql.DataSource;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Service;

@Service
public class HealthToolService {

    private final DataSource dataSource;
    private final Clock clock;

    public HealthToolService(ObjectProvider<DataSource> dataSourceProvider, Clock clock) {
        this.dataSource = dataSourceProvider.getIfAvailable();
        this.clock = clock;
    }

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
            dbPool = dataSource == null
                ? new HealthResponse.DbPoolHealth("not_configured", "Read-only database access is disabled.")
                : new HealthResponse.DbPoolHealth("configured", "Read-only database access is enabled.");
        }

        return new HealthResponse("ok", clock.instant(), jvm, dbPool);
    }
}
