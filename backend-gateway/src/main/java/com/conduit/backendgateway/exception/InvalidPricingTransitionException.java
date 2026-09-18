package com.conduit.backendgateway.exception;

public class InvalidPricingTransitionException extends RuntimeException {
    public InvalidPricingTransitionException(String message) {
        super(message);
    }
}
