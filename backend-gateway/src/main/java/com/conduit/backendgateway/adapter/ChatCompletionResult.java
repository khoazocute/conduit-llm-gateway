package com.conduit.backendgateway.adapter;

public record ChatCompletionResult(
        String content,
        String model,
        Integer tokenInput,
        Integer tokenOutput,
        int latencyMs) {
}
