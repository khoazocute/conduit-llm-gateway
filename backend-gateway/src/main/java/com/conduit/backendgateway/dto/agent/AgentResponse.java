package com.conduit.backendgateway.dto.agent;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.enums.AgentStatus;
import com.conduit.backendgateway.domain.enums.AgentType;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public record AgentResponse(
        UUID id,
        @JsonProperty("creator_id") UUID creatorId,
        String title,
        String introduction,
        @JsonProperty("agent_type") AgentType agentType,
        @JsonProperty("price_vnd") Integer priceVnd,
        @JsonProperty("default_credit_granted") Integer defaultCreditGranted,
        AgentStatus status,
        @JsonProperty("reject_reason") String rejectReason,
        @JsonProperty("created_at") Instant createdAt,
        @JsonProperty("updated_at") Instant updatedAt) {

    public static AgentResponse from(Agent agent) {
        return new AgentResponse(
                agent.getId(),
                agent.getCreatorId(),
                agent.getTitle(),
                agent.getIntroduction(),
                agent.getAgentType(),
                agent.getPriceVnd(),
                agent.getDefaultCreditGranted(),
                agent.getStatus(),
                agent.getRejectReason(),
                agent.getCreatedAt(),
                agent.getUpdatedAt());
    }
}
