package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.dto.conversation.ConversationListResponse;
import com.conduit.backendgateway.dto.conversation.ConversationResponse;
import com.conduit.backendgateway.dto.conversation.CreateConversationRequest;
import com.conduit.backendgateway.dto.conversation.MessageListResponse;
import com.conduit.backendgateway.dto.conversation.SendMessageRequest;
import com.conduit.backendgateway.security.UserPrincipal;
import com.conduit.backendgateway.service.ChatService;
import com.conduit.backendgateway.service.ConversationService;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/conversations")
public class ConversationController {

    private static final long SSE_TIMEOUT_MS = 60_000L;

    private final ConversationService conversationService;
    private final ChatService chatService;

    public ConversationController(ConversationService conversationService, ChatService chatService) {
        this.conversationService = conversationService;
        this.chatService = chatService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ConversationResponse create(
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody CreateConversationRequest request) {
        return conversationService.create(principal.getId(), request.agentId());
    }

    @GetMapping
    public ConversationListResponse listMine(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return conversationService.listMine(principal.getId(), PageRequest.of(page, size));
    }

    @GetMapping("/{conversationId}")
    public ConversationResponse getById(
            @AuthenticationPrincipal UserPrincipal principal, @PathVariable UUID conversationId) {
        return conversationService.getOwnedResponse(conversationId, principal.getId());
    }

    @GetMapping("/{conversationId}/messages")
    public MessageListResponse listMessages(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID conversationId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size) {
        return conversationService.listMessages(conversationId, principal.getId(), PageRequest.of(page, size));
    }

    @PostMapping(value = "/{conversationId}/messages", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter sendMessage(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID conversationId,
            @Valid @RequestBody SendMessageRequest request) {
        SseEmitter emitter = new SseEmitter(SSE_TIMEOUT_MS);
        // Run on a virtual thread so this method returns the emitter to Spring
        // immediately - the actual LLM call (can take many seconds) must NOT
        // block the Tomcat request thread, and must run under Spring's async
        // request lifecycle (not synchronously before the emitter is even
        // registered) so timeouts/errors are handled correctly instead of
        // corrupting the underlying request when the call is slow.
        UUID userId = principal.getId();
        Thread.ofVirtual().start(() -> chatService.sendMessage(conversationId, userId, request.content(), emitter));
        return emitter;
    }
}
