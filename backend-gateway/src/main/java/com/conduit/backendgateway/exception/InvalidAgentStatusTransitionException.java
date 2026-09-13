package com.conduit.backendgateway.exception;

public class InvalidAgentStatusTransitionException extends RuntimeException {
    public InvalidAgentStatusTransitionException(String message) {
        super(message);
    }
}
