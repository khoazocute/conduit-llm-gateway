package com.conduit.backendgateway.dto.agent;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Min;

public record UpdateAgentRequest(
        String title,
        String introduction,
        @Min(0) @JsonProperty("price_vnd") Integer priceVnd,
        @Min(0) @JsonProperty("default_credit_granted") Integer defaultCreditGranted) {
}
