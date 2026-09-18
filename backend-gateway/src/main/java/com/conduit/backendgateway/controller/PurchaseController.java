package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.dto.purchase.AgentPurchaseResponse;
import com.conduit.backendgateway.dto.purchase.CreatePurchaseRequest;
import com.conduit.backendgateway.dto.purchase.CreatePurchaseResponse;
import com.conduit.backendgateway.security.UserPrincipal;
import com.conduit.backendgateway.service.PurchaseService;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PurchaseController {

    private final PurchaseService purchaseService;

    public PurchaseController(PurchaseService purchaseService) {
        this.purchaseService = purchaseService;
    }

    @PostMapping("/agents/{agentId}/purchases")
    @ResponseStatus(HttpStatus.CREATED)
    public CreatePurchaseResponse createPurchase(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID agentId,
            @Valid @RequestBody CreatePurchaseRequest request) {
        return purchaseService.createPurchase(principal.getId(), agentId, request.paymentMethod());
    }

    @GetMapping("/purchases/{transactionRef}")
    public AgentPurchaseResponse getPurchase(
            @AuthenticationPrincipal UserPrincipal principal, @PathVariable String transactionRef) {
        return purchaseService.getPurchase(transactionRef, principal.getId());
    }
}
