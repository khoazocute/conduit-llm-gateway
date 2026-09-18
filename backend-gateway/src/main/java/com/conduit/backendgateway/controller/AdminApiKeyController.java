package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.dto.admin.apikey.ApiKeyResponse;
import com.conduit.backendgateway.dto.admin.apikey.CreateApiKeyRequest;
import com.conduit.backendgateway.dto.admin.apikey.UpdateApiKeyRequest;
import com.conduit.backendgateway.service.AdminApiKeyService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/admin/api-keys")
public class AdminApiKeyController {

    private final AdminApiKeyService adminApiKeyService;

    public AdminApiKeyController(AdminApiKeyService adminApiKeyService) {
        this.adminApiKeyService = adminApiKeyService;
    }

    @GetMapping
    public List<ApiKeyResponse> list() {
        return adminApiKeyService.listApiKeys();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApiKeyResponse create(@Valid @RequestBody CreateApiKeyRequest request) {
        return adminApiKeyService.create(request);
    }

    @PatchMapping("/{apiKeyId}")
    public ApiKeyResponse update(
            @PathVariable UUID apiKeyId, @Valid @RequestBody UpdateApiKeyRequest request) {
        return adminApiKeyService.update(apiKeyId, request);
    }

    @DeleteMapping("/{apiKeyId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable UUID apiKeyId) {
        adminApiKeyService.delete(apiKeyId);
    }
}
