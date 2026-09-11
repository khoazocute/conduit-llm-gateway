package com.conduit.backendgateway.domain;

import com.conduit.backendgateway.domain.enums.RoutingProxy;
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
 * Moi luot goi qua 1 trong 3 proxy danh gia (LiteLLM/Bifrost/Portkey) phai
 * ghi vao bang nay - day la du lieu dau vao truc tiep cho bao cao khoa luan
 * (CLAUDE.md muc 2), khong duoc bo qua du dang o giai doan thu nghiem nhanh.
 */
@Entity
@Table(name = "routing_decisions")
@Getter
@Setter
@NoArgsConstructor
public class RoutingDecision {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "message_id", nullable = false)
    private UUID messageId;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "proxy_name", columnDefinition = "routing_proxy", nullable = false)
    private RoutingProxy proxyName;

    @Column(name = "selected_model", nullable = false)
    private String selectedModel;

    @Column(name = "predicted_cost", nullable = false)
    private BigDecimal predictedCost;

    @Column(name = "token_input")
    private Integer tokenInput;

    @Column(name = "token_output")
    private Integer tokenOutput;

    @Column(name = "response_quality_score")
    private BigDecimal responseQualityScore;

    @Column(name = "latency_ms")
    private Integer latencyMs;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
}
