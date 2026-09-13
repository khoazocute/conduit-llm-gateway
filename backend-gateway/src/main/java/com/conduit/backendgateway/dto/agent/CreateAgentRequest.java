package com.conduit.backendgateway.dto.agent;

import com.conduit.backendgateway.domain.enums.AgentType;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record CreateAgentRequest(
        @NotBlank String title,
        String introduction,
        @JsonProperty("agent_type") AgentType agentType,
        @NotNull @Min(0) @JsonProperty("price_vnd") Integer priceVnd,
        @NotNull @Min(0) @JsonProperty("default_credit_granted") Integer defaultCreditGranted) {
}
