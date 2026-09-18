package com.conduit.backendgateway.dto.admin.pricing;

import com.conduit.backendgateway.domain.enums.LlmProvider;
import com.conduit.backendgateway.domain.enums.UnitType;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.Instant;

public record CreateModelPricingRequest(
        @NotNull LlmProvider provider,
        @NotBlank String model,
        @NotNull @JsonProperty("unit_type") UnitType unitType,
        @NotNull @JsonProperty("price_usd_per_unit") BigDecimal priceUsdPerUnit,
        @JsonProperty("credit_markup_multiplier") BigDecimal creditMarkupMultiplier,
        @NotNull @JsonProperty("effective_from") Instant effectiveFrom) {
}
