package com.conduit.backendgateway.adapter;

// Unchecked - caught internally by ChatService to emit an SSE error event and
// log usage_logs(status=error) without charging credit (CLAUDE.md muc 5).
// Never registered in GlobalExceptionHandler: it must not leak as a generic
// JSON error response, only handled inside the chat flow.
public class ProxyChatException extends RuntimeException {
    public ProxyChatException(String message, Throwable cause) {
        super(message, cause);
    }
}
