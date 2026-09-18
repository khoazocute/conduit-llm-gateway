package com.conduit.backendgateway.dto.conversation;

import com.conduit.backendgateway.domain.Conversation;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public record ConversationResponse(
        UUID id,
        @JsonProperty("user_id") UUID userId,
        @JsonProperty("agent_id") UUID agentId,
        String title,
        @JsonProperty("created_at") Instant createdAt,
        @JsonProperty("updated_at") Instant updatedAt) {

    public static ConversationResponse from(Conversation conversation) {
        return new ConversationResponse(
                conversation.getId(),
                conversation.getUserId(),
                conversation.getAgentId(),
                conversation.getTitle(),
                conversation.getCreatedAt(),
                conversation.getUpdatedAt());
    }
}
