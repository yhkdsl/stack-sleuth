package dev.stacksleuth.toolserver.api;

import dev.stacksleuth.toolserver.audit.AuditEvent;
import dev.stacksleuth.toolserver.audit.AuditSink;
import jakarta.servlet.http.HttpServletRequest;
import java.time.Instant;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private final AuditSink auditSink;

    public GlobalExceptionHandler(AuditSink auditSink) {
        this.auditSink = auditSink;
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ErrorResponse> validationFailed(
        MethodArgumentNotValidException exception,
        HttpServletRequest request
    ) {
        List<ErrorResponse.FieldError> fieldErrors = exception.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(error -> new ErrorResponse.FieldError(error.getField(), error.getDefaultMessage()))
            .toList();
        ToolRequestContext context = auditRejection(request, "VALIDATION_FAILED");
        return ResponseEntity.badRequest()
            .header("X-Trace-Id", context.traceId())
            .header("X-Request-Id", context.requestId())
            .body(new ErrorResponse("VALIDATION_FAILED", "Request validation failed.", Instant.now(), fieldErrors));
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    ResponseEntity<ErrorResponse> malformedJson(HttpMessageNotReadableException exception, HttpServletRequest request) {
        ToolRequestContext context = auditRejection(request, "MALFORMED_JSON");
        return ResponseEntity.badRequest()
            .header("X-Trace-Id", context.traceId())
            .header("X-Request-Id", context.requestId())
            .body(ErrorResponse.of("MALFORMED_JSON", "Request body contains malformed JSON."));
    }

    @ExceptionHandler(ToolException.class)
    ResponseEntity<ErrorResponse> toolError(ToolException exception, HttpServletRequest request) {
        ToolRequestContext context = ToolRequestContext.fromRequest(request);
        return ResponseEntity.status(exception.status())
            .header("X-Trace-Id", context.traceId())
            .header("X-Request-Id", context.requestId())
            .body(ErrorResponse.of(exception.code(), exception.getMessage()));
    }

    private ToolRequestContext auditRejection(HttpServletRequest request, String reason) {
        ToolRequestContext context = ToolRequestContext.fromRequest(request);
        auditSink.record(new AuditEvent(
            context.traceId(),
            context.requestId(),
            ToolRequestContext.toolNameForPath(request.getRequestURI()),
            "rejected",
            0,
            reason
        ));
        return context;
    }
}
