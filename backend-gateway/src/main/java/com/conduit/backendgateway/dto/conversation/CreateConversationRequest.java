package com.conduit.backendgateway.dto.conversation;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public record CreateConversationRequest(@NotNull @JsonProperty("agent_id") UUID agentId) {
}
