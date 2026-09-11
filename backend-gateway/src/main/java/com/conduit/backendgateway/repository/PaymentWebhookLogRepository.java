package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.PaymentWebhookLog;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PaymentWebhookLogRepository extends JpaRepository<PaymentWebhookLog, UUID> {

    List<PaymentWebhookLog> findByTransactionRef(String transactionRef);
}
