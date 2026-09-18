package com.conduit.backendgateway.dto.purchase;

import com.conduit.backendgateway.domain.enums.WebhookResult;

public record WebhookResponseDto(WebhookResult result) {
}
