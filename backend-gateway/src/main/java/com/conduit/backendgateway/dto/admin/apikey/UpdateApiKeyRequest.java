package com.conduit.backendgateway.dto.admin.apikey;

import com.conduit.backendgateway.domain.enums.ApiKeyStatus;
import jakarta.validation.constraints.NotNull;

public record UpdateApiKeyRequest(
        @NotNull ApiKeyStatus status,
        @NotNull Integer priority) {
}
