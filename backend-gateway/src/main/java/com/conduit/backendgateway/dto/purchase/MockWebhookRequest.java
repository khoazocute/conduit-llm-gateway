package com.conduit.backendgateway.dto.purchase;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record MockWebhookRequest(
        @NotBlank @JsonProperty("transaction_ref") String transactionRef,
        @NotBlank @Pattern(regexp = "success|failed") String result) {
}
