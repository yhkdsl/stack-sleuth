package dev.stacksleuth.toolserver.tools.health;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.sql.Connection;
import java.sql.SQLException;
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
            dbPool = checkDatabase();
        }

        String status = dbPool != null && "unavailable".equals(dbPool.status()) ? "degraded" : "ok";
        return new HealthResponse(status, clock.instant(), jvm, dbPool);
    }

    private HealthResponse.DbPoolHealth checkDatabase() {
        if (dataSource == null) {
            return new HealthResponse.DbPoolHealth("not_configured", "Read-only database access is disabled.");
        }

        try (Connection connection = dataSource.getConnection()) {
            if (connection.isValid(1)) {
                return new HealthResponse.DbPoolHealth(
                    "available",
                    "Read-only database connection is available."
                );
            }
        } catch (SQLException exception) {
            // Return a stable, non-sensitive health result instead of connection details.
        }

        return new HealthResponse.DbPoolHealth(
            "unavailable",
            "Read-only database connection is unavailable."
        );
    }
}
