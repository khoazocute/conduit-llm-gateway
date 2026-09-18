package com.conduit.backendgateway.dto.conversation;

import jakarta.validation.constraints.NotBlank;

public record SendMessageRequest(@NotBlank String content) {
}
