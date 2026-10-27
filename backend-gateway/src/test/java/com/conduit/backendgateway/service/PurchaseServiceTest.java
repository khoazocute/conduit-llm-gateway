package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.AgentPurchase;
import com.conduit.backendgateway.domain.PaymentWebhookLog;
import com.conduit.backendgateway.domain.enums.AgentStatus;
import com.conduit.backendgateway.domain.enums.CreditTxType;
import com.conduit.backendgateway.domain.enums.PaymentMethod;
import com.conduit.backendgateway.domain.enums.PaymentStatus;
import com.conduit.backendgateway.domain.enums.WebhookResult;
import com.conduit.backendgateway.dto.purchase.CreatePurchaseResponse;
import com.conduit.backendgateway.exception.AgentNotPurchasableException;
import com.conduit.backendgateway.exception.InvalidWebhookSignatureException;
import com.conduit.backendgateway.repository.AgentPurchaseRepository;
import com.conduit.backendgateway.repository.AgentRepository;
import com.conduit.backendgateway.repository.PaymentWebhookLogRepository;
import java.nio.charset.StandardCharsets;
import java.util.HexFormat;
import java.util.Optional;
import java.util.UUID;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

/**
 * TASK-53: PurchaseService voi repository MOCK. Rang buoc bao mat CLAUDE.md muc 7: webhook sai chu
 * ky bi tu choi; webhook goi lai (cung transaction_ref) KHONG cong credit lan 2.
 */
class PurchaseServiceTest {

    private static final String SECRET = "test-webhook-secret";
    private static final UUID BUYER = UUID.randomUUID();

    private final AgentRepository agentRepository = mock(AgentRepository.class);
    private final AgentPurchaseRepository purchaseRepository = mock(AgentPurchaseRepository.class);
    private final PaymentWebhookLogRepository webhookLogRepository = mock(PaymentWebhookLogRepository.class);
    private final CreditService creditService = mock(CreditService.class);
    private PurchaseService service;
    private Agent agent;

    @BeforeEach
    void setUp() {
        service = new PurchaseService(agentRepository, purchaseRepository, webhookLogRepository, creditService, SECRET);
        agent = new Agent();
        agent.setId(UUID.randomUUID());
        agent.setStatus(AgentStatus.published);
        agent.setPriceVnd(50_000);
        agent.setDefaultCreditGranted(1_000);
        when(agentRepository.findById(agent.getId())).thenReturn(Optional.of(agent));
        when(purchaseRepository.saveAndFlush(any(AgentPurchase.class))).thenAnswer(inv -> {
            AgentPurchase p = inv.getArgument(0);
            if (p.getId() == null) {
                p.setId(UUID.randomUUID());
            }
            return p;
        });
    }

    // ------------------------------------------------------------------ createPurchase

    @Test
    void freeAgentIsPaidAndGrantsCreditImmediately() {
        agent.setPriceVnd(0);

        CreatePurchaseResponse res = service.createPurchase(BUYER, agent.getId(), PaymentMethod.mock);

        assertThat(res.purchase().paymentStatus()).isEqualTo(PaymentStatus.paid);
        verify(creditService).credit(eq(BUYER), eq(1_000L), eq(CreditTxType.purchase_grant), any(), any(), anyString());
    }

    @Test
    void paidAgentWaitsForTheWebhookAndGrantsNothingYet() {
        CreatePurchaseResponse res = service.createPurchase(BUYER, agent.getId(), PaymentMethod.mock);

        assertThat(res.purchase().paymentStatus()).isEqualTo(PaymentStatus.pending);
        assertThat(res.purchase().transactionRef()).startsWith("MOCK-");
        verify(creditService, never()).credit(any(), anyLong(), any(), any(), any(), anyString());
    }

    @Test
    void unpublishedAgentCannotBePurchased() {
        agent.setStatus(AgentStatus.pending);
        assertThatThrownBy(() -> service.createPurchase(BUYER, agent.getId(), PaymentMethod.mock))
                .isInstanceOf(AgentNotPurchasableException.class);
    }

    @Test
    void alreadyPurchasedAgentCannotBePurchasedAgain() {
        when(purchaseRepository.existsByUserIdAndAgentIdAndPaymentStatus(BUYER, agent.getId(), PaymentStatus.paid))
                .thenReturn(true);
        assertThatThrownBy(() -> service.createPurchase(BUYER, agent.getId(), PaymentMethod.mock))
                .isInstanceOf(AgentNotPurchasableException.class);
        verify(purchaseRepository, never()).saveAndFlush(any());
    }

    @Test
    void vnpayIsRejectedUntilImplemented() {
        assertThatThrownBy(() -> service.createPurchase(BUYER, agent.getId(), PaymentMethod.vnpay))
                .isInstanceOf(AgentNotPurchasableException.class);
    }

    // ------------------------------------------------------------------ webhook

    @Test
    void validSuccessWebhookPaysAndGrantsCreditOnce() {
        AgentPurchase pending = pendingPurchase("MOCK-1");
        String body = "{\"transaction_ref\":\"MOCK-1\",\"result\":\"success\"}";

        var res = service.handleMockWebhook(body, sign(body), "MOCK-1", "success");

        assertThat(res.result()).isEqualTo(WebhookResult.accepted);
        assertThat(pending.getPaymentStatus()).isEqualTo(PaymentStatus.paid);
        assertThat(pending.getPaidAt()).isNotNull();
        verify(creditService).credit(eq(BUYER), eq(1_000L), eq(CreditTxType.purchase_grant), any(), eq(pending.getId()), anyString());
    }

    @Test
    void replayedWebhookIsIdempotentAndGrantsNoSecondCredit() {
        AgentPurchase paid = pendingPurchase("MOCK-2");
        paid.setPaymentStatus(PaymentStatus.paid); // webhook dau da xu ly xong
        String body = "{\"transaction_ref\":\"MOCK-2\",\"result\":\"success\"}";

        var res = service.handleMockWebhook(body, sign(body), "MOCK-2", "success");

        assertThat(res.result()).isEqualTo(WebhookResult.duplicate);
        verify(creditService, never()).credit(any(), anyLong(), any(), any(), any(), anyString());
        assertThat(loggedResult()).isEqualTo(WebhookResult.duplicate);
    }

    @Test
    void invalidSignatureIsRejectedAndLoggedWithoutTouchingThePurchase() {
        AgentPurchase pending = pendingPurchase("MOCK-3");
        String body = "{\"transaction_ref\":\"MOCK-3\",\"result\":\"success\"}";

        assertThatThrownBy(() -> service.handleMockWebhook(body, "deadbeef", "MOCK-3", "success"))
                .isInstanceOf(InvalidWebhookSignatureException.class);
        assertThatThrownBy(() -> service.handleMockWebhook(body, null, "MOCK-3", "success"))
                .isInstanceOf(InvalidWebhookSignatureException.class);

        assertThat(pending.getPaymentStatus()).isEqualTo(PaymentStatus.pending);
        verify(creditService, never()).credit(any(), anyLong(), any(), any(), any(), anyString());
    }

    @Test
    void signatureOverADifferentBodyIsRejected() {
        pendingPurchase("MOCK-4");
        String signedBody = "{\"transaction_ref\":\"MOCK-4\",\"result\":\"failed\"}";
        String tamperedBody = "{\"transaction_ref\":\"MOCK-4\",\"result\":\"success\"}";

        assertThatThrownBy(() -> service.handleMockWebhook(tamperedBody, sign(signedBody), "MOCK-4", "success"))
                .isInstanceOf(InvalidWebhookSignatureException.class);
        verify(creditService, never()).credit(any(), anyLong(), any(), any(), any(), anyString());
    }

    @Test
    void failedPaymentMarksFailedWithoutCredit() {
        AgentPurchase pending = pendingPurchase("MOCK-5");
        String body = "{\"transaction_ref\":\"MOCK-5\",\"result\":\"failed\"}";

        var res = service.handleMockWebhook(body, sign(body), "MOCK-5", "failed");

        assertThat(res.result()).isEqualTo(WebhookResult.accepted);
        assertThat(pending.getPaymentStatus()).isEqualTo(PaymentStatus.failed);
        verify(creditService, never()).credit(any(), anyLong(), any(), any(), any(), anyString());
    }

    // ------------------------------------------------------------------ helpers

    private AgentPurchase pendingPurchase(String ref) {
        AgentPurchase p = new AgentPurchase();
        p.setId(UUID.randomUUID());
        p.setUserId(BUYER);
        p.setAgentId(agent.getId());
        p.setDefaultCreditGranted(1_000);
        p.setPaymentStatus(PaymentStatus.pending);
        p.setTransactionRef(ref);
        when(purchaseRepository.findByTransactionRef(ref)).thenReturn(Optional.of(p));
        return p;
    }

    private WebhookResult loggedResult() {
        ArgumentCaptor<PaymentWebhookLog> captor = ArgumentCaptor.forClass(PaymentWebhookLog.class);
        verify(webhookLogRepository).saveAndFlush(captor.capture());
        return captor.getValue().getResult();
    }

    private static String sign(String body) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(SECRET.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            return HexFormat.of().formatHex(mac.doFinal(body.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
}
