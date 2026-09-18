package com.conduit.backendgateway.dto.admin.apikey;

import com.conduit.backendgateway.domain.ApiKey;
import com.conduit.backendgateway.domain.enums.ApiKeyStatus;
import com.conduit.backendgateway.domain.enums.LlmProvider;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

// key_encrypted is NEVER exposed here (CLAUDE.md muc 7).
public record ApiKeyResponse(
        UUID id,
        LlmProvider provider,
        ApiKeyStatus status,
        int priority,
        @JsonProperty("last_used_at") Instant lastUsedAt,
        @JsonProperty("created_at") Instant createdAt) {

    public static ApiKeyResponse from(ApiKey apiKey) {
        return new ApiKeyResponse(
                apiKey.getId(),
                apiKey.getProvider(),
                apiKey.getStatus(),
                apiKey.getPriority(),
                apiKey.getLastUsedAt(),
                apiKey.getCreatedAt());
    }
}
