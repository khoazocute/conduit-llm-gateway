package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.dto.purchase.MockWebhookRequest;
import com.conduit.backendgateway.dto.purchase.WebhookResponseDto;
import com.conduit.backendgateway.service.PurchaseService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/payments/webhook")
public class PaymentWebhookController {

    private final PurchaseService purchaseService;
    private final ObjectMapper objectMapper;

    public PaymentWebhookController(PurchaseService purchaseService, ObjectMapper objectMapper) {
        this.purchaseService = purchaseService;
        this.objectMapper = objectMapper;
    }

    @PostMapping("/mock")
    public WebhookResponseDto handleMockWebhook(
            @RequestBody String rawBody,
            @RequestHeader(value = "X-Webhook-Signature", required = false) String signature)
            throws com.fasterxml.jackson.core.JsonProcessingException {
        MockWebhookRequest request = objectMapper.readValue(rawBody, MockWebhookRequest.class);
        return purchaseService.handleMockWebhook(
                rawBody, signature, request.transactionRef(), request.result());
    }
}
