package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.Conversation;
import com.conduit.backendgateway.domain.enums.PaymentStatus;
import com.conduit.backendgateway.dto.conversation.ConversationListResponse;
import com.conduit.backendgateway.dto.conversation.ConversationResponse;
import com.conduit.backendgateway.dto.conversation.MessageListResponse;
import com.conduit.backendgateway.exception.ForbiddenActionException;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.AgentPurchaseRepository;
import com.conduit.backendgateway.repository.ConversationRepository;
import com.conduit.backendgateway.repository.MessageRepository;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ConversationService {

    private final ConversationRepository conversationRepository;
    private final AgentPurchaseRepository agentPurchaseRepository;
    private final MessageRepository messageRepository;

    public ConversationService(
            ConversationRepository conversationRepository,
            AgentPurchaseRepository agentPurchaseRepository,
            MessageRepository messageRepository) {
        this.conversationRepository = conversationRepository;
        this.agentPurchaseRepository = agentPurchaseRepository;
        this.messageRepository = messageRepository;
    }

    @Transactional
    public ConversationResponse create(UUID userId, UUID agentId) {
        boolean purchased = agentPurchaseRepository.existsByUserIdAndAgentIdAndPaymentStatus(
                userId, agentId, PaymentStatus.paid);
        if (!purchased) {
            throw new ForbiddenActionException("You must purchase this agent before starting a conversation");
        }

        Conversation conversation = new Conversation();
        conversation.setUserId(userId);
        conversation.setAgentId(agentId);
        return ConversationResponse.from(conversationRepository.saveAndFlush(conversation));
    }

    public ConversationListResponse listMine(UUID userId, Pageable pageable) {
        return ConversationListResponse.from(conversationRepository.findByUserId(userId, pageable));
    }

    public ConversationResponse getOwnedResponse(UUID conversationId, UUID userId) {
        return ConversationResponse.from(getOwned(conversationId, userId));
    }

    public MessageListResponse listMessages(UUID conversationId, UUID userId, Pageable pageable) {
        getOwned(conversationId, userId);
        return MessageListResponse.from(messageRepository.findByConversationId(conversationId, pageable));
    }

    Conversation getOwned(UUID conversationId, UUID userId) {
        Conversation conversation = conversationRepository.findById(conversationId)
                .orElseThrow(() -> new ResourceNotFoundException("Conversation not found"));
        if (!conversation.getUserId().equals(userId)) {
            throw new ForbiddenActionException("You do not own this conversation");
        }
        return conversation;
    }
}
