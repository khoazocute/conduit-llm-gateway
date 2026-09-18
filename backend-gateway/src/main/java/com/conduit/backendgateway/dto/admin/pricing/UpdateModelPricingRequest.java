package com.conduit.backendgateway.dto.admin.pricing;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.Instant;

// Partial update - each field optional, null means "keep the old row's value"
// when creating the new pricing row (see AdminModelPricingService.update).
public record UpdateModelPricingRequest(
        @JsonProperty("price_usd_per_unit") BigDecimal priceUsdPerUnit,
        @JsonProperty("credit_markup_multiplier") BigDecimal creditMarkupMultiplier,
        @JsonProperty("effective_from") Instant effectiveFrom) {
}
