package dev.stacksleuth.toolserver.tools.health;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Clock;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.support.StaticListableBeanFactory;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

class HealthToolServiceTest {

    @Test
    void reportsConfiguredWhenReadOnlyDataSourceExists() {
        StaticListableBeanFactory beanFactory = new StaticListableBeanFactory();
        beanFactory.addBean(
            "dataSource",
            new DriverManagerDataSource("jdbc:postgresql://localhost/test", "reader", "unused")
        );
        HealthToolService service = new HealthToolService(
            beanFactory.getBeanProvider(DataSource.class),
            Clock.systemUTC()
        );

        HealthResponse response = service.check(new HealthRequest(false, true));

        assertThat(response.dbPool().status()).isEqualTo("configured");
        assertThat(response.dbPool().detail()).isEqualTo("Read-only database access is enabled.");
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
