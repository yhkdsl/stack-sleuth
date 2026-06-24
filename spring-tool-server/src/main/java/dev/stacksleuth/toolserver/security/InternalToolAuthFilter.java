package dev.stacksleuth.toolserver.security;

import dev.stacksleuth.toolserver.api.ToolRequestContext;
import dev.stacksleuth.toolserver.audit.AuditEvent;
import dev.stacksleuth.toolserver.audit.AuditSink;
import dev.stacksleuth.toolserver.config.ToolServerProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class InternalToolAuthFilter extends OncePerRequestFilter {

    private static final String TOKEN_HEADER = "X-Tool-Server-Token";

    private final ToolServerProperties properties;
    private final AuditSink auditSink;

    public InternalToolAuthFilter(ToolServerProperties properties, AuditSink auditSink) {
        this.properties = properties;
        this.auditSink = auditSink;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
        throws ServletException, IOException {
        if (!request.getRequestURI().startsWith("/internal/tools/") || !properties.authEnabled()) {
            filterChain.doFilter(request, response);
            return;
        }

        String actualToken = request.getHeader(TOKEN_HEADER);
        if (tokensMatch(properties.token(), actualToken)) {
            filterChain.doFilter(request, response);
            return;
        }

        ToolRequestContext context = ToolRequestContext.fromRequest(request);
        response.setHeader("X-Trace-Id", context.traceId());
        response.setHeader("X-Request-Id", context.requestId());
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.getWriter().write("""
            {"code":"UNAUTHORIZED_TOOL_REQUEST","message":"Missing or invalid internal tool token.","timestamp":"%s"}
            """.formatted(Instant.now()));
        auditSink.record(new AuditEvent(
            context.traceId(),
            context.requestId(),
            ToolRequestContext.toolNameForPath(request.getRequestURI()),
            "rejected",
            0,
            "UNAUTHORIZED_TOOL_REQUEST"
        ));
    }

    private static boolean tokensMatch(String expected, String actual) {
        if (actual == null) {
            return false;
        }
        return MessageDigest.isEqual(
            expected.getBytes(StandardCharsets.UTF_8),
            actual.getBytes(StandardCharsets.UTF_8)
        );
    }
}
