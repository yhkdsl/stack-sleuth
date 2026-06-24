package dev.stacksleuth.toolserver.config;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;

@SpringBootTest
class LocalBindingConfigurationTest {

    @Autowired
    Environment environment;

    @Test
    void defaultsToLoopbackAddress() {
        assertThat(environment.getProperty("server.address")).isEqualTo("127.0.0.1");
    }
}
