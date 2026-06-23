package dev.stacksleuth.toolserver.security;

import dev.stacksleuth.toolserver.config.ToolServerProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class InternalToolAuthFilter extends OncePerRequestFilter {

    private static final String TOKEN_HEADER = "X-Tool-Server-Token";

    private final ToolServerProperties properties;

    public InternalToolAuthFilter(ToolServerProperties properties) {
        this.properties = properties;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
        throws ServletException, IOException {
        if (!request.getRequestURI().startsWith("/internal/tools/") || !properties.authEnabled()) {
            filterChain.doFilter(request, response);
            return;
        }

        String actualToken = request.getHeader(TOKEN_HEADER);
        if (properties.token().equals(actualToken)) {
            filterChain.doFilter(request, response);
            return;
        }

        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.getWriter().write("""
            {"code":"UNAUTHORIZED_TOOL_REQUEST","message":"Missing or invalid internal tool token.","timestamp":"%s"}
            """.formatted(Instant.now()));
    }
}
