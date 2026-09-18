package com.conduit.backendgateway.dto.admin.apikey;

import com.conduit.backendgateway.domain.enums.LlmProvider;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record CreateApiKeyRequest(
        @NotNull LlmProvider provider,
        @NotBlank @JsonProperty("raw_key") String rawKey,
        @JsonProperty("priority") Integer priority) {
}
