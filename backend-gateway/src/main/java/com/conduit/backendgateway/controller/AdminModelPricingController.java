package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.domain.enums.LlmProvider;
import com.conduit.backendgateway.dto.admin.pricing.CreateModelPricingRequest;
import com.conduit.backendgateway.dto.admin.pricing.ModelPricingResponse;
import com.conduit.backendgateway.dto.admin.pricing.UpdateModelPricingRequest;
import com.conduit.backendgateway.service.AdminModelPricingService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/admin/model-pricing")
public class AdminModelPricingController {

    private final AdminModelPricingService adminModelPricingService;

    public AdminModelPricingController(AdminModelPricingService adminModelPricingService) {
        this.adminModelPricingService = adminModelPricingService;
    }

    @GetMapping
    public List<ModelPricingResponse> list(@RequestParam(required = false) LlmProvider provider) {
        return adminModelPricingService.list(provider);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ModelPricingResponse create(@Valid @RequestBody CreateModelPricingRequest request) {
        return adminModelPricingService.create(request);
    }

    @PatchMapping("/{pricingId}")
    public ModelPricingResponse update(
            @PathVariable UUID pricingId, @RequestBody UpdateModelPricingRequest request) {
        return adminModelPricingService.update(pricingId, request);
    }
}
