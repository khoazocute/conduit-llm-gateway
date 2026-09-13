package com.conduit.backendgateway.dto.common;

import java.util.Map;

public record ErrorResponse(String error, String message, Map<String, Object> details) {

    public static ErrorResponse of(String error, String message) {
        return new ErrorResponse(error, message, null);
    }

    public static ErrorResponse of(String error, String message, Map<String, Object> details) {
        return new ErrorResponse(error, message, details);
    }
}
