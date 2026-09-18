package com.conduit.backendgateway.dto.admin.pricing;

import com.conduit.backendgateway.domain.ModelPricing;
import com.conduit.backendgateway.domain.enums.LlmProvider;
import com.conduit.backendgateway.domain.enums.UnitType;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

public record ModelPricingResponse(
        UUID id,
        LlmProvider provider,
        String model,
        @JsonProperty("unit_type") UnitType unitType,
        @JsonProperty("price_usd_per_unit") BigDecimal priceUsdPerUnit,
        @JsonProperty("credit_markup_multiplier") BigDecimal creditMarkupMultiplier,
        @JsonProperty("effective_from") Instant effectiveFrom,
        @JsonProperty("created_at") Instant createdAt) {

    public static ModelPricingResponse from(ModelPricing pricing) {
        return new ModelPricingResponse(
                pricing.getId(),
                pricing.getProvider(),
                pricing.getModel(),
                pricing.getUnitType(),
                pricing.getPriceUsdPerUnit(),
                pricing.getCreditMarkupMultiplier(),
                pricing.getEffectiveFrom(),
                pricing.getCreatedAt());
    }
}
