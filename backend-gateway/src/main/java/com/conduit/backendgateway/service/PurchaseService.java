package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.AgentPurchase;
import com.conduit.backendgateway.domain.PaymentWebhookLog;
import com.conduit.backendgateway.domain.enums.AgentStatus;
import com.conduit.backendgateway.domain.enums.CreditTxType;
import com.conduit.backendgateway.domain.enums.PaymentMethod;
import com.conduit.backendgateway.domain.enums.PaymentStatus;
import com.conduit.backendgateway.domain.enums.WebhookResult;
import com.conduit.backendgateway.dto.purchase.AgentPurchaseResponse;
import com.conduit.backendgateway.dto.purchase.CreatePurchaseResponse;
import com.conduit.backendgateway.dto.purchase.WebhookResponseDto;
import com.conduit.backendgateway.exception.AgentNotPurchasableException;
import com.conduit.backendgateway.exception.ForbiddenActionException;
import com.conduit.backendgateway.exception.InvalidWebhookSignatureException;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.AgentPurchaseRepository;
import com.conduit.backendgateway.repository.AgentRepository;
import com.conduit.backendgateway.repository.PaymentWebhookLogRepository;
import java.time.Instant;
import java.util.UUID;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import java.util.HexFormat;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PurchaseService {

    private static final String HMAC_ALGO = "HmacSHA256";

    private final AgentRepository agentRepository;
    private final AgentPurchaseRepository agentPurchaseRepository;
    private final PaymentWebhookLogRepository paymentWebhookLogRepository;
    private final CreditService creditService;
    private final String mockWebhookSecret;

    public PurchaseService(
            AgentRepository agentRepository,
            AgentPurchaseRepository agentPurchaseRepository,
            PaymentWebhookLogRepository paymentWebhookLogRepository,
            CreditService creditService,
            @Value("${app.webhook.mock-secret:dev-only-mock-webhook-secret}") String mockWebhookSecret) {
        this.agentRepository = agentRepository;
        this.agentPurchaseRepository = agentPurchaseRepository;
        this.paymentWebhookLogRepository = paymentWebhookLogRepository;
        this.creditService = creditService;
        this.mockWebhookSecret = mockWebhookSecret;
    }

    @Transactional
    public CreatePurchaseResponse createPurchase(UUID userId, UUID agentId, PaymentMethod method) {
        Agent agent = agentRepository.findById(agentId)
                .orElseThrow(() -> new ResourceNotFoundException("Agent not found"));

        if (agent.getStatus() != AgentStatus.published) {
            throw new AgentNotPurchasableException("Agent is not published");
        }
        if (agentPurchaseRepository.existsByUserIdAndAgentIdAndPaymentStatus(userId, agentId, PaymentStatus.paid)) {
            throw new AgentNotPurchasableException("Agent already purchased");
        }
        if (method == PaymentMethod.vnpay) {
            throw new AgentNotPurchasableException("VNPay is not implemented yet (Should-have)");
        }

        AgentPurchase purchase = new AgentPurchase();
        purchase.setUserId(userId);
        purchase.setAgentId(agentId);
        purchase.setAmountVnd(agent.getPriceVnd());
        purchase.setDefaultCreditGranted(agent.getDefaultCreditGranted());
        purchase.setPaymentMethod(method);
        purchase.setTransactionRef("MOCK-" + UUID.randomUUID());

        if (agent.getPriceVnd() == 0) {
            // Agent mien phi: khong can cho webhook, cong credit va danh dau paid ngay.
            purchase.setPaymentStatus(PaymentStatus.paid);
            purchase.setPaidAt(Instant.now());
            purchase = agentPurchaseRepository.saveAndFlush(purchase);
            grantCredit(userId, purchase);
        } else {
            purchase.setPaymentStatus(PaymentStatus.pending);
            purchase = agentPurchaseRepository.saveAndFlush(purchase);
        }

        return new CreatePurchaseResponse(AgentPurchaseResponse.from(purchase), null);
    }

    public AgentPurchaseResponse getPurchase(String transactionRef, UUID currentUserId) {
        AgentPurchase purchase = agentPurchaseRepository.findByTransactionRef(transactionRef)
                .orElseThrow(() -> new ResourceNotFoundException("Purchase not found"));
        if (!purchase.getUserId().equals(currentUserId)) {
            throw new ForbiddenActionException("You do not own this purchase");
        }
        return AgentPurchaseResponse.from(purchase);
    }

    @Transactional
    public WebhookResponseDto handleMockWebhook(
            String rawBody, String signatureHeader, String transactionRef, String result) {
        if (!isValidSignature(rawBody, signatureHeader)) {
            logWebhook(transactionRef, WebhookResult.invalid_signature, rawBody);
            throw new InvalidWebhookSignatureException("Webhook signature is invalid");
        }

        AgentPurchase purchase = agentPurchaseRepository.findByTransactionRef(transactionRef)
                .orElseThrow(() -> new ResourceNotFoundException("Purchase not found"));

        if (purchase.getPaymentStatus() != PaymentStatus.pending) {
            // Da xu ly roi (paid/failed) - idempotent, KHONG cong credit lan 2.
            logWebhook(transactionRef, WebhookResult.duplicate, rawBody);
            return new WebhookResponseDto(WebhookResult.duplicate);
        }

        if ("success".equals(result)) {
            purchase.setPaymentStatus(PaymentStatus.paid);
            purchase.setPaidAt(Instant.now());
            agentPurchaseRepository.saveAndFlush(purchase);
            grantCredit(purchase.getUserId(), purchase);
        } else {
            purchase.setPaymentStatus(PaymentStatus.failed);
            agentPurchaseRepository.saveAndFlush(purchase);
        }

        logWebhook(transactionRef, WebhookResult.accepted, rawBody);
        return new WebhookResponseDto(WebhookResult.accepted);
    }

    private void grantCredit(UUID userId, AgentPurchase purchase) {
        creditService.credit(
                userId,
                purchase.getDefaultCreditGranted(),
                CreditTxType.purchase_grant,
                null,
                purchase.getId(),
                "Purchase grant for agent " + purchase.getAgentId());
    }

    private void logWebhook(String transactionRef, WebhookResult result, String rawPayload) {
        PaymentWebhookLog log = new PaymentWebhookLog();
        log.setTransactionRef(transactionRef);
        log.setResult(result);
        log.setRawPayload(rawPayload);
        paymentWebhookLogRepository.saveAndFlush(log);
    }

    private boolean isValidSignature(String rawBody, String signatureHeader) {
        if (signatureHeader == null || signatureHeader.isBlank()) {
            return false;
        }
        try {
            Mac mac = Mac.getInstance(HMAC_ALGO);
            mac.init(new SecretKeySpec(mockWebhookSecret.getBytes(), HMAC_ALGO));
            byte[] computed = mac.doFinal(rawBody.getBytes());
            String computedHex = HexFormat.of().formatHex(computed);
            return computedHex.equalsIgnoreCase(signatureHeader);
        } catch (Exception e) {
            return false;
        }
    }
}
