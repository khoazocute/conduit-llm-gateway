package com.conduit.backendgateway.dto.purchase;

import com.conduit.backendgateway.domain.enums.PaymentMethod;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotNull;

public record CreatePurchaseRequest(
        @NotNull @JsonProperty("payment_method") PaymentMethod paymentMethod) {
}
