package com.conduit.backendgateway.dto.wallet;

import com.conduit.backendgateway.domain.CreditWallet;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public record CreditWalletResponse(
        UUID id,
        @JsonProperty("user_id") UUID userId,
        long balance,
        @JsonProperty("updated_at") Instant updatedAt) {

    public static CreditWalletResponse from(CreditWallet wallet) {
        return new CreditWalletResponse(
                wallet.getId(), wallet.getUserId(), wallet.getBalance(), wallet.getUpdatedAt());
    }
}
