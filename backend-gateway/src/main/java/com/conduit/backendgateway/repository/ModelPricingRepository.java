package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.ModelPricing;
import com.conduit.backendgateway.domain.enums.LlmProvider;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ModelPricingRepository extends JpaRepository<ModelPricing, UUID> {

    List<ModelPricing> findByProvider(LlmProvider provider);

    /** Muc gia dang ap dung tai 1 thoi diem (effective_from <= at), moi nhat truoc. */
    Optional<ModelPricing> findFirstByProviderAndModelAndEffectiveFromLessThanEqualOrderByEffectiveFromDesc(
            LlmProvider provider, String model, Instant at);
}
