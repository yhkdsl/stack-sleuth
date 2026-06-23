package dev.stacksleuth.toolserver.api;

import java.time.Instant;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ErrorResponse> validationFailed(MethodArgumentNotValidException exception) {
        List<ErrorResponse.FieldError> fieldErrors = exception.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(error -> new ErrorResponse.FieldError(error.getField(), error.getDefaultMessage()))
            .toList();
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_FAILED", "Request validation failed.", Instant.now(), fieldErrors));
    }

    @ExceptionHandler(ToolException.class)
    ResponseEntity<ErrorResponse> toolError(ToolException exception) {
        return ResponseEntity.status(exception.status())
            .body(ErrorResponse.of(exception.code(), exception.getMessage()));
    }
}
