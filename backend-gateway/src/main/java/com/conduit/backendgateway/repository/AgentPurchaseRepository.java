package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.AgentPurchase;
import com.conduit.backendgateway.domain.enums.PaymentStatus;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AgentPurchaseRepository extends JpaRepository<AgentPurchase, UUID> {

    Optional<AgentPurchase> findByTransactionRef(String transactionRef);

    boolean existsByUserIdAndAgentIdAndPaymentStatus(UUID userId, UUID agentId, PaymentStatus paymentStatus);
}
