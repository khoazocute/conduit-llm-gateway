package com.conduit.backendgateway.dto.agent;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

public record RejectAgentRequest(@NotBlank @JsonProperty("reject_reason") String rejectReason) {
}
