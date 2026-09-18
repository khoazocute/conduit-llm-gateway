package com.conduit.backendgateway.dto.purchase;

import com.conduit.backendgateway.domain.AgentPurchase;
import com.conduit.backendgateway.domain.enums.PaymentMethod;
import com.conduit.backendgateway.domain.enums.PaymentStatus;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public record AgentPurchaseResponse(
        UUID id,
        @JsonProperty("user_id") UUID userId,
        @JsonProperty("agent_id") UUID agentId,
        @JsonProperty("amount_vnd") int amountVnd,
        @JsonProperty("default_credit_granted") int defaultCreditGranted,
        @JsonProperty("payment_method") PaymentMethod paymentMethod,
        @JsonProperty("payment_status") PaymentStatus paymentStatus,
        @JsonProperty("transaction_ref") String transactionRef,
        @JsonProperty("paid_at") Instant paidAt,
        @JsonProperty("created_at") Instant createdAt) {

    public static AgentPurchaseResponse from(AgentPurchase purchase) {
        return new AgentPurchaseResponse(
                purchase.getId(),
                purchase.getUserId(),
                purchase.getAgentId(),
                purchase.getAmountVnd(),
                purchase.getDefaultCreditGranted(),
                purchase.getPaymentMethod(),
                purchase.getPaymentStatus(),
                purchase.getTransactionRef(),
                purchase.getPaidAt(),
                purchase.getCreatedAt());
    }
}
