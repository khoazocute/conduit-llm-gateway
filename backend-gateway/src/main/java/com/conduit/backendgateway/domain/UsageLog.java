package com.conduit.backendgateway.domain;

import com.conduit.backendgateway.domain.enums.LlmProvider;
import com.conduit.backendgateway.domain.enums.UsageStatus;
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
 * Usage thuong nguon (token_input/output, cost_upstream) - tang do hach toan
 * KHAC voi credit noi bo (revenue_credit). Xem CLAUDE.md muc 4.
 */
@Entity
@Table(name = "usage_logs")
@Getter
@Setter
@NoArgsConstructor
public class UsageLog {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "message_id", nullable = false)
    private UUID messageId;

    @Column(name = "api_key_id")
    private UUID apiKeyId;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "provider", columnDefinition = "llm_provider")
    private LlmProvider provider;

    private String model;

    @Column(name = "token_input")
    private Integer tokenInput;

    @Column(name = "token_output")
    private Integer tokenOutput;

    @Column(name = "cost_upstream")
    private BigDecimal costUpstream;

    @Column(name = "revenue_credit")
    private BigDecimal revenueCredit;

    @Column(name = "latency_ms")
    private Integer latencyMs;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "status", columnDefinition = "usage_status", nullable = false)
    private UsageStatus status = UsageStatus.success;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
}
