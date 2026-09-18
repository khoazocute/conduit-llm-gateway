package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.ModelPricing;
import com.conduit.backendgateway.domain.enums.LlmProvider;
import com.conduit.backendgateway.dto.admin.pricing.CreateModelPricingRequest;
import com.conduit.backendgateway.dto.admin.pricing.ModelPricingResponse;
import com.conduit.backendgateway.dto.admin.pricing.UpdateModelPricingRequest;
import com.conduit.backendgateway.exception.InvalidPricingTransitionException;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.ModelPricingRepository;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AdminModelPricingService {

    private final ModelPricingRepository modelPricingRepository;

    public AdminModelPricingService(ModelPricingRepository modelPricingRepository) {
        this.modelPricingRepository = modelPricingRepository;
    }

    public List<ModelPricingResponse> list(LlmProvider provider) {
        List<ModelPricing> rows = provider == null
                ? modelPricingRepository.findAll(Sort.by(Sort.Direction.DESC, "effectiveFrom"))
                : modelPricingRepository.findByProvider(provider);
        return rows.stream().map(ModelPricingResponse::from).toList();
    }

    @Transactional
    public ModelPricingResponse create(CreateModelPricingRequest request) {
        ModelPricing pricing = new ModelPricing();
        pricing.setProvider(request.provider());
        pricing.setModel(request.model());
        pricing.setUnitType(request.unitType());
        pricing.setPriceUsdPerUnit(request.priceUsdPerUnit());
        pricing.setCreditMarkupMultiplier(
                request.creditMarkupMultiplier() != null
                        ? request.creditMarkupMultiplier()
                        : new java.math.BigDecimal("1.5"));
        pricing.setEffectiveFrom(request.effectiveFrom());
        return ModelPricingResponse.from(modelPricingRepository.saveAndFlush(pricing));
    }

    // Tao row MOI thay vi sua row cu - giu lich su tang gia (dung comment trong
    // openapi.json). Chi cho phep neu row dang "sua" chua ap dung (effective_from
    // con o tuong lai) - tranh sua nham gia da/dang dung trong qua khu.
    @Transactional
    public ModelPricingResponse update(UUID pricingId, UpdateModelPricingRequest request) {
        ModelPricing existing = modelPricingRepository.findById(pricingId)
                .orElseThrow(() -> new ResourceNotFoundException("Model pricing not found"));

        if (existing.getEffectiveFrom().isBefore(Instant.now())) {
            throw new InvalidPricingTransitionException(
                    "Cannot modify a pricing row that has already taken effect");
        }

        ModelPricing next = new ModelPricing();
        next.setProvider(existing.getProvider());
        next.setModel(existing.getModel());
        next.setUnitType(existing.getUnitType());
        next.setPriceUsdPerUnit(
                request.priceUsdPerUnit() != null ? request.priceUsdPerUnit() : existing.getPriceUsdPerUnit());
        next.setCreditMarkupMultiplier(
                request.creditMarkupMultiplier() != null
                        ? request.creditMarkupMultiplier()
                        : existing.getCreditMarkupMultiplier());
        next.setEffectiveFrom(
                request.effectiveFrom() != null ? request.effectiveFrom() : existing.getEffectiveFrom());

        return ModelPricingResponse.from(modelPricingRepository.saveAndFlush(next));
    }
}
