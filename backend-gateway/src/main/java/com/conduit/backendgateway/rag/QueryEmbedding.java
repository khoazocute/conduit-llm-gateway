package com.conduit.backendgateway.rag;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

// Ket qua ai-service POST /embed (ai-service/main.py).
public record QueryEmbedding(
        String model,
        @JsonProperty("prompt_tokens") Integer promptTokens,
        List<Double> embedding) {
}
