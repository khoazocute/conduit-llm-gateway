package com.conduit.backendgateway.domain;

import com.conduit.backendgateway.domain.enums.ApiKeyStatus;
import com.conduit.backendgateway.domain.enums.LlmProvider;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/**
 * key_encrypted luu AES-GCM, encryption key nam ngoai DB (bien moi truong) -
 * KHONG bao gio tra field nay qua API/log (CLAUDE.md muc 7).
 */
@Entity
@Table(name = "api_keys")
@Getter
@Setter
@NoArgsConstructor
public class ApiKey {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "provider", columnDefinition = "llm_provider", nullable = false)
    private LlmProvider provider;

    @Column(name = "key_encrypted", nullable = false, columnDefinition = "text")
    private String keyEncrypted;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "status", columnDefinition = "api_key_status", nullable = false)
    private ApiKeyStatus status = ApiKeyStatus.active;

    private Integer priority = 0;

    @Column(name = "last_used_at")
    private Instant lastUsedAt;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
}
