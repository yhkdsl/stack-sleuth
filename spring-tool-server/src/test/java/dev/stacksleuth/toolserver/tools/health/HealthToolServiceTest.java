package dev.stacksleuth.toolserver.tools.health;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.Clock;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.support.StaticListableBeanFactory;

class HealthToolServiceTest {

    @Test
    void reportsAvailableWhenReadOnlyDatabaseAcceptsConnections() throws SQLException {
        Connection connection = mock(Connection.class);
        when(connection.isValid(1)).thenReturn(true);
        DataSource dataSource = mock(DataSource.class);
        when(dataSource.getConnection()).thenReturn(connection);

        StaticListableBeanFactory beanFactory = new StaticListableBeanFactory();
        beanFactory.addBean("dataSource", dataSource);
        HealthToolService service = new HealthToolService(
            beanFactory.getBeanProvider(DataSource.class),
            Clock.systemUTC()
        );

        HealthResponse response = service.check(new HealthRequest(false, true));

        assertThat(response.status()).isEqualTo("ok");
        assertThat(response.dbPool().status()).isEqualTo("available");
        assertThat(response.dbPool().detail()).isEqualTo("Read-only database connection is available.");
    }

    @Test
    void reportsUnavailableWhenReadOnlyDatabaseConnectionFails() throws SQLException {
        DataSource dataSource = mock(DataSource.class);
        when(dataSource.getConnection()).thenThrow(new SQLException("connection refused"));

        StaticListableBeanFactory beanFactory = new StaticListableBeanFactory();
        beanFactory.addBean("dataSource", dataSource);
        HealthToolService service = new HealthToolService(
            beanFactory.getBeanProvider(DataSource.class),
            Clock.systemUTC()
        );

        HealthResponse response = service.check(new HealthRequest(false, true));

        assertThat(response.status()).isEqualTo("degraded");
        assertThat(response.dbPool().status()).isEqualTo("unavailable");
        assertThat(response.dbPool().detail()).isEqualTo("Read-only database connection is unavailable.");
    }

    @Test
    void reportsNotConfiguredWhenDatabaseIsDisabled() {
        StaticListableBeanFactory beanFactory = new StaticListableBeanFactory();
        HealthToolService service = new HealthToolService(
            beanFactory.getBeanProvider(DataSource.class),
            Clock.systemUTC()
        );

        HealthResponse response = service.check(new HealthRequest(false, true));

        assertThat(response.dbPool().status()).isEqualTo("not_configured");
        assertThat(response.dbPool().detail()).isEqualTo("Read-only database access is disabled.");
    }
}
