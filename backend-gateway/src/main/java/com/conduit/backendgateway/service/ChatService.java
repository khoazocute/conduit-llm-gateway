package com.conduit.backendgateway.service;

import com.conduit.backendgateway.adapter.ChatCompletionResult;
import com.conduit.backendgateway.adapter.ChatProxyProperties;
import com.conduit.backendgateway.adapter.ChatTurn;
import com.conduit.backendgateway.adapter.ProxyChatClient;
import com.conduit.backendgateway.adapter.ProxyChatException;
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
import com.conduit.backendgateway.dto.conversation.MessageResponse;
import com.conduit.backendgateway.exception.InsufficientCreditException;
import com.conduit.backendgateway.repository.MessageRepository;
import com.conduit.backendgateway.repository.ModelPricingRepository;
import com.conduit.backendgateway.repository.RoutingDecisionRepository;
import com.conduit.backendgateway.repository.UsageLogRepository;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Service
public class ChatService {

    private final ConversationService conversationService;
    private final MessageRepository messageRepository;
    private final ProxyChatClient proxyChatClient;
    private final CreditService creditService;
    private final ModelPricingRepository modelPricingRepository;
    private final UsageLogRepository usageLogRepository;
    private final RoutingDecisionRepository routingDecisionRepository;
    private final ChatProxyProperties chatProxyProperties;
    // Self-injection so @Transactional billing below goes through the Spring
    // AOP proxy (see CreditService for the same pattern/reasoning).
    private final ChatService self;

    public ChatService(
            ConversationService conversationService,
            MessageRepository messageRepository,
            ProxyChatClient proxyChatClient,
            CreditService creditService,
            ModelPricingRepository modelPricingRepository,
            UsageLogRepository usageLogRepository,
            RoutingDecisionRepository routingDecisionRepository,
            ChatProxyProperties chatProxyProperties,
            @Lazy ChatService self) {
        this.conversationService = conversationService;
        this.messageRepository = messageRepository;
        this.proxyChatClient = proxyChatClient;
        this.creditService = creditService;
        this.modelPricingRepository = modelPricingRepository;
        this.usageLogRepository = usageLogRepository;
        this.routingDecisionRepository = routingDecisionRepository;
        this.chatProxyProperties = chatProxyProperties;
        this.self = self;
    }

    public void sendMessage(UUID conversationId, UUID userId, String content, SseEmitter emitter) {
        // Defense in depth: this runs on its own virtual thread (see
        // ConversationController), completely detached from the request
        // thread - NOTHING may escape uncaught here, or the SseEmitter is
        // left in limbo and the connection hangs/breaks with no clean error.
        try {
            doSendMessage(conversationId, userId, content, emitter);
        } catch (Exception e) {
            emitError(emitter, "Unexpected error: " + e.getMessage());
        }
    }

    private void doSendMessage(UUID conversationId, UUID userId, String content, SseEmitter emitter) {
        conversationService.getOwned(conversationId, userId); // ABAC check

        Message userMessage = new Message();
        userMessage.setConversationId(conversationId);
        userMessage.setRole(MessageRole.user);
        userMessage.setContent(content);
        messageRepository.saveAndFlush(userMessage);

        List<ChatTurn> turns = messageRepository.findByConversationIdOrderByCreatedAtAsc(conversationId).stream()
                .filter(m -> m.getContent() != null)
                .map(m -> new ChatTurn(m.getRole().name(), m.getContent()))
                .toList();

        String model = chatProxyProperties.getDefaultModel();
        RoutingProxy activeProxy = RoutingProxy.valueOf(chatProxyProperties.getActiveProxy());

        long start = System.currentTimeMillis();
        ChatCompletionResult result;
        try {
            result = proxyChatClient.complete(model, turns);
        } catch (ProxyChatException e) {
            int elapsed = (int) (System.currentTimeMillis() - start);
            self.recordFailedTurn(conversationId, model, activeProxy, elapsed);
            emitError(emitter, "Chat provider error: " + e.getMessage());
            return;
        }

        try {
            Message assistantMessage = self.recordSuccessfulTurn(userId, conversationId, model, activeProxy, result);
            emitSuccess(emitter, result.content(), assistantMessage);
        } catch (InsufficientCreditException e) {
            emitError(emitter, "Insufficient credit balance");
        }
    }

    // Ghi Message + tru credit + log usage_logs/routing_decisions trong CUNG 1
    // transaction: neu debit that bai (khong du credit), toan bo rollback -
    // dung yeu cau CLAUDE.md muc 5 "billing chi tinh khi co usage that... khong
    // luu usage/routing thanh cong khi khong tru duoc credit".
    @Transactional
    protected Message recordSuccessfulTurn(
            UUID userId, UUID conversationId, String requestedModel, RoutingProxy activeProxy,
            ChatCompletionResult result) {
        Message assistantMessage = new Message();
        assistantMessage.setConversationId(conversationId);
        assistantMessage.setRole(MessageRole.assistant);
        assistantMessage.setContent(result.content());
        assistantMessage.setModelUsed(result.model());
        assistantMessage.setLatencyMs(result.latencyMs());
        assistantMessage = messageRepository.saveAndFlush(assistantMessage);

        LlmProvider provider = inferProvider(result.model());
        BigDecimal costUpstream = BigDecimal.ZERO;
        long credit = 0;

        BigDecimal inputPrice = unitPrice(provider, result.model(), UnitType.token_input);
        BigDecimal outputPrice = unitPrice(provider, result.model(), UnitType.token_output);
        BigDecimal inputMarkup = unitMarkup(provider, result.model(), UnitType.token_input);
        BigDecimal outputMarkup = unitMarkup(provider, result.model(), UnitType.token_output);

        if (result.tokenInput() != null) {
            costUpstream = costUpstream.add(inputPrice.multiply(BigDecimal.valueOf(result.tokenInput())));
            credit += ceilCredit(result.tokenInput(), inputMarkup);
        }
        if (result.tokenOutput() != null) {
            costUpstream = costUpstream.add(outputPrice.multiply(BigDecimal.valueOf(result.tokenOutput())));
            credit += ceilCredit(result.tokenOutput(), outputMarkup);
        }

        creditService.debit(
                userId, credit, CreditTxType.usage_deduct, assistantMessage.getId(), null,
                "Chat usage for model " + result.model());

        assistantMessage.setCreditCharged((int) credit);
        assistantMessage = messageRepository.saveAndFlush(assistantMessage);

        UsageLog usageLog = new UsageLog();
        usageLog.setMessageId(assistantMessage.getId());
        usageLog.setProvider(provider);
        usageLog.setModel(result.model());
        usageLog.setTokenInput(result.tokenInput());
        usageLog.setTokenOutput(result.tokenOutput());
        usageLog.setCostUpstream(costUpstream);
        usageLog.setRevenueCredit(BigDecimal.valueOf(credit));
        usageLog.setLatencyMs(result.latencyMs());
        usageLog.setStatus(UsageStatus.success);
        usageLogRepository.saveAndFlush(usageLog);

        RoutingDecision routingDecision = new RoutingDecision();
        routingDecision.setMessageId(assistantMessage.getId());
        routingDecision.setProxyName(activeProxy);
        routingDecision.setSelectedModel(result.model());
        routingDecision.setPredictedCost(costUpstream);
        routingDecision.setTokenInput(result.tokenInput());
        routingDecision.setTokenOutput(result.tokenOutput());
        routingDecision.setLatencyMs(result.latencyMs());
        routingDecisionRepository.saveAndFlush(routingDecision);

        return assistantMessage;
    }

    // Loi tu proxy: van phai ghi log theo CLAUDE.md muc 2 ("moi luot goi phai
    // ghi vao routing_decisions"), nhung KHONG tru credit (muc 5).
    @Transactional
    protected void recordFailedTurn(UUID conversationId, String requestedModel, RoutingProxy activeProxy, int elapsedMs) {
        Message assistantMessage = new Message();
        assistantMessage.setConversationId(conversationId);
        assistantMessage.setRole(MessageRole.assistant);
        assistantMessage.setContent(null);
        assistantMessage.setModelUsed(requestedModel);
        assistantMessage.setLatencyMs(elapsedMs);
        assistantMessage = messageRepository.saveAndFlush(assistantMessage);

        UsageLog usageLog = new UsageLog();
        usageLog.setMessageId(assistantMessage.getId());
        usageLog.setProvider(inferProvider(requestedModel));
        usageLog.setModel(requestedModel);
        usageLog.setLatencyMs(elapsedMs);
        usageLog.setStatus(UsageStatus.error);
        usageLogRepository.saveAndFlush(usageLog);

        RoutingDecision routingDecision = new RoutingDecision();
        routingDecision.setMessageId(assistantMessage.getId());
        routingDecision.setProxyName(activeProxy);
        routingDecision.setSelectedModel(requestedModel);
        routingDecision.setPredictedCost(BigDecimal.ZERO);
        routingDecision.setLatencyMs(elapsedMs);
        routingDecisionRepository.saveAndFlush(routingDecision);
    }

    // Luu y: ModelPricingRepository.findFirstByProviderAndModelAndEffectiveFrom...
    // KHONG loc theo unit_type (token_input/token_output la 2 dong rieng), nen
    // khong the dung truc tiep de tra ve dung dong - phai tu loc bang
    // findByUnitType ben duoi.
    private BigDecimal unitPrice(LlmProvider provider, String model, UnitType unitType) {
        return findByUnitType(provider, model, unitType)
                .map(ModelPricing::getPriceUsdPerUnit)
                .orElse(BigDecimal.ZERO);
    }

    private BigDecimal unitMarkup(LlmProvider provider, String model, UnitType unitType) {
        return findByUnitType(provider, model, unitType)
                .map(ModelPricing::getCreditMarkupMultiplier)
                .orElse(new BigDecimal("1.5"));
    }

    private java.util.Optional<ModelPricing> findByUnitType(LlmProvider provider, String model, UnitType unitType) {
        return modelPricingRepository.findByProvider(provider).stream()
                .filter(p -> p.getModel().equals(model) && p.getUnitType() == unitType)
                .filter(p -> !p.getEffectiveFrom().isAfter(Instant.now()))
                .max(java.util.Comparator.comparing(ModelPricing::getEffectiveFrom));
    }

    // credit = ceil(token_upstream x credit_markup_multiplier) - CLAUDE.md muc 4.
    private long ceilCredit(int tokens, BigDecimal markup) {
        return BigDecimal.valueOf(tokens).multiply(markup).setScale(0, RoundingMode.CEILING).longValue();
    }

    private LlmProvider inferProvider(String model) {
        if (model == null) {
            return LlmProvider.openai;
        }
        String m = model.toLowerCase();
        if (m.startsWith("claude")) {
            return LlmProvider.anthropic;
        }
        if (m.startsWith("gemini")) {
            return LlmProvider.google;
        }
        return LlmProvider.openai;
    }

    private void emitSuccess(SseEmitter emitter, String content, Message assistantMessage) {
        try {
            emitter.send(SseEmitter.event().name("chunk").data(Map.of("delta", content)));
            emitter.send(SseEmitter.event().name("done").data(Map.of("message", MessageResponse.from(assistantMessage))));
            emitter.complete();
        } catch (Exception e) {
            // The emitter may already be closed/timed-out (e.g. a slow LLM
            // call) - swallow rather than rethrow, or an uncaught exception
            // here corrupts the whole request (Content-Type is already
            // committed as text/event-stream, so Spring's generic error
            // handler can't write a JSON body over it and the connection
            // breaks uncleanly instead of just ending the SSE stream).
            safeCompleteWithError(emitter, e);
        }
    }

    private void emitError(SseEmitter emitter, String message) {
        try {
            emitter.send(SseEmitter.event().name("error").data(Map.of("message", message)));
            emitter.complete();
        } catch (Exception e) {
            safeCompleteWithError(emitter, e);
        }
    }

    private void safeCompleteWithError(SseEmitter emitter, Exception e) {
        try {
            emitter.completeWithError(e);
        } catch (Exception ignored) {
            // Emitter already completed one way or another - nothing left to do.
        }
    }
}
