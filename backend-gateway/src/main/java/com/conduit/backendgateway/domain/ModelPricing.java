package com.conduit.backendgateway.domain;

import com.conduit.backendgateway.domain.enums.LlmProvider;
import com.conduit.backendgateway.domain.enums.UnitType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/**
 * Bang ty gia quy doi usage thuong nguon -> credit noi bo. Cong thuc text:
 * credit = ceil(token_upstream * credit_markup_multiplier), mac dinh 1.5 =
 * markup 50% chi phi thuong nguon (~33.3% bien loi nhuan tren gia ban -
 * KHONG phai 50%, xem CLAUDE.md muc 4).
 */
@Entity
@Table(name = "model_pricing")
@Getter
@Setter
@NoArgsConstructor
public class ModelPricing {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "provider", columnDefinition = "llm_provider", nullable = false)
    private LlmProvider provider;

    @Column(nullable = false)
    private String model;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "unit_type", columnDefinition = "unit_type", nullable = false)
    private UnitType unitType;

    @Column(name = "price_usd_per_unit", nullable = false)
    private BigDecimal priceUsdPerUnit;

    @Column(name = "credit_markup_multiplier", nullable = false)
    private BigDecimal creditMarkupMultiplier = new BigDecimal("1.5");

    @Column(name = "effective_from", nullable = false)
    private Instant effectiveFrom;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
}
