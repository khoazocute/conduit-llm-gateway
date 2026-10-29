package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.conduit.backendgateway.adapter.ChatCompletionResult;
import com.conduit.backendgateway.adapter.ChatProxyProperties;
import com.conduit.backendgateway.adapter.ProxyChatClient;
import com.conduit.backendgateway.adapter.ProxyChatException;
import com.conduit.backendgateway.domain.CreditTransaction;
import com.conduit.backendgateway.domain.CreditWallet;
import com.conduit.backendgateway.adapter.ChatTurn;
import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.Conversation;
import com.conduit.backendgateway.domain.Message;
import com.conduit.backendgateway.domain.ModelPricing;
import com.conduit.backendgateway.domain.RoutingDecision;
import com.conduit.backendgateway.domain.UsageLog;
import com.conduit.backendgateway.domain.enums.CreditTxType;
import com.conduit.backendgateway.domain.enums.LlmProvider;
import com.conduit.backendgateway.domain.enums.MessageRole;
import com.conduit.backendgateway.domain.enums.RoutingProxy;
import com.conduit.backendgateway.domain.enums.UnitType;
import com.conduit.backendgateway.domain.enums.UsageStatus;
import com.conduit.backendgateway.exception.InsufficientCreditException;
import com.conduit.backendgateway.repository.AgentRepository;
import com.conduit.backendgateway.repository.MessageRepository;
import com.conduit.backendgateway.repository.ModelPricingRepository;
import com.conduit.backendgateway.repository.RoutingDecisionRepository;
import com.conduit.backendgateway.repository.UsageLogRepository;
import java.io.IOException;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * TASK-53: ChatService voi provider MOCK - khong goi LLM that. Kiem 3 rang buoc billing cua
 * CLAUDE.md muc 4-5: luot loi khong tru credit; co usage thi tru dung ceil(token x markup);
 * khong du credit thi khong ghi usage/routing thanh cong.
 */
class ChatServiceTest {

    private static final UUID USER = UUID.randomUUID();
    private static final UUID CONVERSATION = UUID.randomUUID();

    private final ConversationService conversationService = mock(ConversationService.class);
    private final MessageRepository messageRepository = mock(MessageRepository.class);
    private final ProxyChatClient proxyChatClient = mock(ProxyChatClient.class);
    private final CreditService creditService = mock(CreditService.class);
    private final ModelPricingRepository modelPricingRepository = mock(ModelPricingRepository.class);
    private final UsageLogRepository usageLogRepository = mock(UsageLogRepository.class);
    private final RoutingDecisionRepository routingDecisionRepository = mock(RoutingDecisionRepository.class);
    private final ChatProxyProperties properties = new ChatProxyProperties();
    private final AgentRepository agentRepository = mock(AgentRepository.class);
    private final Agent agent = new Agent();

    private ChatService chatService;
    private RecordingEmitter emitter;

    @BeforeEach
    void setUp() {
        properties.setActiveProxy("litellm");
        properties.setProxyDefaultModels(Map.of("litellm", "conduit-pool"));

        agent.setId(UUID.randomUUID());
        Conversation conversation = new Conversation();
        conversation.setId(CONVERSATION);
        conversation.setUserId(USER);
        conversation.setAgentId(agent.getId());
        when(conversationService.getOwned(CONVERSATION, USER)).thenReturn(conversation);
        when(agentRepository.findById(agent.getId())).thenReturn(java.util.Optional.of(agent));

        // `self` di qua proxy Spring khi chay that (de @Transactional co tac dung); o day dung mot
        // ban that thu hai cung dung chung cac mock - recordSuccessfulTurn/recordFailedTurn khong
        // goi lai self nen khong can vong lap.
        ChatService inner = newChatService(null);
        chatService = newChatService(inner);
        emitter = new RecordingEmitter();

        when(messageRepository.saveAndFlush(any(Message.class))).thenAnswer(inv -> {
            Message m = inv.getArgument(0);
            if (m.getId() == null) {
                m.setId(UUID.randomUUID());
            }
            return m;
        });
        Message history = new Message();
        history.setRole(MessageRole.user);
        history.setContent("hello");
        when(messageRepository.findByConversationIdOrderByCreatedAtAsc(CONVERSATION)).thenReturn(List.of(history));
        when(modelPricingRepository.findByProvider(LlmProvider.openai)).thenReturn(List.of(
                price("gpt-4o-mini", UnitType.token_input, "0.00000015"),
                price("gpt-4o-mini", UnitType.token_output, "0.0000006")));
    }

    private ChatService newChatService(ChatService self) {
        return new ChatService(conversationService, messageRepository, proxyChatClient, creditService,
                modelPricingRepository, usageLogRepository, routingDecisionRepository, properties,
                agentRepository, self);
    }

    @Test
    void providerErrorDoesNotChargeCreditAndIsLoggedAsError() {
        when(proxyChatClient.complete(eq("conduit-pool"), any()))
                .thenThrow(new ProxyChatException("Proxy returned 401 UNAUTHORIZED", null));

        chatService.sendMessage(CONVERSATION, USER, "hello", emitter);

        verify(creditService, never()).debit(any(), anyLong(), any(), any(), any(), anyString());
        UsageLog usage = captureUsageLog();
        assertThat(usage.getStatus()).isEqualTo(UsageStatus.error);
        RoutingDecision decision = captureRoutingDecision();
        assertThat(decision.getProxyName()).isEqualTo(RoutingProxy.litellm);
        assertThat(decision.getPredictedCost()).isEqualByComparingTo(BigDecimal.ZERO);
        assertThat(emitter.events).anyMatch(e -> e.contains("error") && e.contains("401"));
    }

    @Test
    void successChargesCeilOfTokensTimesMarkupPerUnitType() {
        // 101 token vao, 51 ra, markup 1.5: ceil(151.5) + ceil(76.5) = 152 + 77 = 229.
        // (Lam tron TUNG dong gia - input va output la 2 dong model_pricing rieng, co the khac markup.)
        when(proxyChatClient.complete(eq("conduit-pool"), any()))
                .thenReturn(new ChatCompletionResult("hi there", "gpt-4o-mini", 101, 51, 900));

        chatService.sendMessage(CONVERSATION, USER, "hello", emitter);

        verify(creditService).debit(eq(USER), eq(229L), eq(CreditTxType.usage_deduct), any(), any(), anyString());
        UsageLog usage = captureUsageLog();
        assertThat(usage.getStatus()).isEqualTo(UsageStatus.success);
        // 101 x 0.00000015 + 51 x 0.0000006 = 0.00001515 + 0.0000306 = 0.00004575 USD
        assertThat(usage.getCostUpstream()).isEqualByComparingTo("0.00004575");
        assertThat(usage.getRevenueCredit()).isEqualByComparingTo("229");
        RoutingDecision decision = captureRoutingDecision();
        assertThat(decision.getSelectedModel()).isEqualTo("gpt-4o-mini");
        assertThat(decision.getPredictedCost()).isEqualByComparingTo("0.00004575");
        assertThat(emitter.events).anyMatch(e -> e.contains("done"));
    }

    @Test
    void insufficientCreditRecordsNoSuccessfulUsage() {
        when(proxyChatClient.complete(eq("conduit-pool"), any()))
                .thenReturn(new ChatCompletionResult("hi there", "gpt-4o-mini", 10, 10, 500));
        when(creditService.debit(any(), anyLong(), any(), any(), any(), anyString()))
                .thenThrow(new InsufficientCreditException("Not enough credit balance"));

        chatService.sendMessage(CONVERSATION, USER, "hello", emitter);

        // Tru credit xay ra TRUOC khi ghi usage_logs/routing_decisions; trong transaction that ca
        // luot rollback. O day kiem rang khong co dong usage/routing nao duoc ghi sau khi tru loi.
        verify(usageLogRepository, never()).saveAndFlush(any());
        verify(routingDecisionRepository, never()).saveAndFlush(any());
        assertThat(emitter.events).anyMatch(e -> e.contains("Insufficient credit"));
    }

    @Test
    void optimisticLockConflictOnTheWalletIsRetriedInAFreshTransaction() {
        // TASK-56: cung 1 nguoi dung chat song song. Lan dau thua khoa lac quan, lan sau thanh cong.
        when(proxyChatClient.complete(eq("conduit-pool"), any()))
                .thenReturn(new ChatCompletionResult("hi", "gpt-4o-mini", 10, 10, 500));
        when(creditService.debit(any(), anyLong(), any(), any(), any(), anyString()))
                .thenThrow(new ObjectOptimisticLockingFailureException(CreditWallet.class, UUID.randomUUID()))
                .thenReturn(new CreditTransaction());

        chatService.sendMessage(CONVERSATION, USER, "hello", emitter);

        verify(creditService, times(2)).debit(eq(USER), eq(30L), any(), any(), any(), anyString());
        verify(proxyChatClient, times(1)).complete(any(), any()); // KHONG goi LLM lai
        assertThat(emitter.events).anyMatch(e -> e.contains("done"));
    }

    @Test
    void persistentWalletConflictGivesUpAfterTheCap() {
        when(proxyChatClient.complete(eq("conduit-pool"), any()))
                .thenReturn(new ChatCompletionResult("hi", "gpt-4o-mini", 10, 10, 500));
        when(creditService.debit(any(), anyLong(), any(), any(), any(), anyString()))
                .thenThrow(new ObjectOptimisticLockingFailureException(CreditWallet.class, UUID.randomUUID()));

        chatService.sendMessage(CONVERSATION, USER, "hello", emitter);

        verify(creditService, times(ChatService.BILLING_MAX_ATTEMPTS)).debit(any(), anyLong(), any(), any(), any(), anyString());
        assertThat(emitter.events).anyMatch(e -> e.contains("error"));
    }

    @Test
    @SuppressWarnings("unchecked")
    void agentInstructionsAreSentAsTheFirstSystemTurn() {
        // TASK-66 (D8): instructions cua agent thanh luot system o dau danh sach gui cho proxy.
        agent.setInstructions("You are a terse math tutor.");
        when(proxyChatClient.complete(eq("conduit-pool"), any()))
                .thenReturn(new ChatCompletionResult("4", "gpt-4o-mini", 10, 1, 300));

        chatService.sendMessage(CONVERSATION, USER, "hello", emitter);

        ArgumentCaptor<List<ChatTurn>> turns = ArgumentCaptor.forClass(List.class);
        verify(proxyChatClient).complete(eq("conduit-pool"), turns.capture());
        assertThat(turns.getValue()).hasSize(2);
        assertThat(turns.getValue().get(0)).isEqualTo(new ChatTurn("system", "You are a terse math tutor."));
        assertThat(turns.getValue().get(1)).isEqualTo(new ChatTurn("user", "hello"));
    }

    @Test
    @SuppressWarnings("unchecked")
    void agentWithoutInstructionsSendsNoSystemTurn() {
        // Rong/NULL -> request y het luc do thuc nghiem 720 luot.
        agent.setInstructions(null);
        when(proxyChatClient.complete(eq("conduit-pool"), any()))
                .thenReturn(new ChatCompletionResult("4", "gpt-4o-mini", 10, 1, 300));

        chatService.sendMessage(CONVERSATION, USER, "hello", emitter);

        ArgumentCaptor<List<ChatTurn>> turns = ArgumentCaptor.forClass(List.class);
        verify(proxyChatClient).complete(eq("conduit-pool"), turns.capture());
        assertThat(turns.getValue()).containsExactly(new ChatTurn("user", "hello"));
    }

    @Test
    void unknownModelPriceIsChargedWithDefaultMarkupButZeroUpstreamCost() {
        // Ghi lai hanh vi hien tai (verify_results.py duoc viet de bat dung truong hop nay): model
        // khong co dong model_pricing -> cost_upstream = 0 nhung van tru credit theo markup 1.5.
        when(proxyChatClient.complete(eq("conduit-pool"), any()))
                .thenReturn(new ChatCompletionResult("hi", "some-unpriced-model", 10, 10, 500));

        chatService.sendMessage(CONVERSATION, USER, "hello", emitter);

        verify(creditService).debit(eq(USER), eq(30L), eq(CreditTxType.usage_deduct), any(), any(), anyString());
        assertThat(captureUsageLog().getCostUpstream()).isEqualByComparingTo(BigDecimal.ZERO);
    }

    // ------------------------------------------------------------------ helpers

    private UsageLog captureUsageLog() {
        ArgumentCaptor<UsageLog> captor = ArgumentCaptor.forClass(UsageLog.class);
        verify(usageLogRepository).saveAndFlush(captor.capture());
        return captor.getValue();
    }

    private RoutingDecision captureRoutingDecision() {
        ArgumentCaptor<RoutingDecision> captor = ArgumentCaptor.forClass(RoutingDecision.class);
        verify(routingDecisionRepository).saveAndFlush(captor.capture());
        return captor.getValue();
    }

    private static ModelPricing price(String model, UnitType unit, String usdPerUnit) {
        ModelPricing p = new ModelPricing();
        p.setProvider(LlmProvider.openai);
        p.setModel(model);
        p.setUnitType(unit);
        p.setPriceUsdPerUnit(new BigDecimal(usdPerUnit));
        p.setCreditMarkupMultiplier(new BigDecimal("1.5"));
        p.setEffectiveFrom(Instant.parse("2026-01-01T00:00:00Z"));
        return p;
    }

    /** SseEmitter ghi lai noi dung cac su kien da gui de kiem. */
    private static final class RecordingEmitter extends SseEmitter {
        final List<String> events = new ArrayList<>();

        @Override
        public void send(SseEventBuilder builder) throws IOException {
            StringBuilder sb = new StringBuilder();
            builder.build().forEach(d -> sb.append(d.getData()));
            events.add(sb.toString());
        }

        @Override
        public void complete() {
        }
    }
}
