package com.conduit.backendgateway.dto.purchase;

import com.fasterxml.jackson.annotation.JsonProperty;

public record CreatePurchaseResponse(
        AgentPurchaseResponse purchase,
        @JsonProperty("redirect_url") String redirectUrl) {
}
