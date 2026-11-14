package com.conduit.backendgateway.rag;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

// Ket qua ai-service POST /chunk-embed (ai-service/main.py).
public record ChunkEmbeddingResult(
        String model,
        @JsonProperty("prompt_tokens") Integer promptTokens,
        List<Chunk> chunks) {

    public record Chunk(int index, String text, List<Double> embedding) {}
}
