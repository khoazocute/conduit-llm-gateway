package com.conduit.backendgateway.dto.conversation;

import com.conduit.backendgateway.domain.Message;
import com.conduit.backendgateway.domain.enums.MessageRole;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public record MessageResponse(
        UUID id,
        @JsonProperty("conversation_id") UUID conversationId,
        MessageRole role,
        String content,
        @JsonProperty("credit_charged") Integer creditCharged,
        @JsonProperty("model_used") String modelUsed,
        @JsonProperty("latency_ms") Integer latencyMs,
        @JsonProperty("created_at") Instant createdAt) {

    public static MessageResponse from(Message message) {
        return new MessageResponse(
                message.getId(),
                message.getConversationId(),
                message.getRole(),
                message.getContent(),
                message.getCreditCharged(),
                message.getModelUsed(),
                message.getLatencyMs(),
                message.getCreatedAt());
    }
}
