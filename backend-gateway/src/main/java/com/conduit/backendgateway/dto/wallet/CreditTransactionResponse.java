package com.conduit.backendgateway.dto.wallet;

import com.conduit.backendgateway.domain.CreditTransaction;
import com.conduit.backendgateway.domain.enums.CreditTxType;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public record CreditTransactionResponse(
        UUID id,
        @JsonProperty("wallet_id") UUID walletId,
        CreditTxType type,
        long amount,
        @JsonProperty("related_message_id") UUID relatedMessageId,
        @JsonProperty("related_purchase_id") UUID relatedPurchaseId,
        String description,
        @JsonProperty("created_at") Instant createdAt) {

    public static CreditTransactionResponse from(CreditTransaction tx) {
        return new CreditTransactionResponse(
                tx.getId(), tx.getWalletId(), tx.getType(), tx.getAmount(),
                tx.getRelatedMessageId(), tx.getRelatedPurchaseId(),
                tx.getDescription(), tx.getCreatedAt());
    }
}
