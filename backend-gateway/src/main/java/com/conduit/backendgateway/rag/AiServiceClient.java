package com.conduit.backendgateway.rag;

// Goi ai-service (Python, CLAUDE.md muc 3) de chia doan + embedding. ai-service tu goi LiteLLM.
public interface AiServiceClient {

    ChunkEmbeddingResult chunkAndEmbed(String fileName, byte[] data);
}
