package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.ApiKey;
import com.conduit.backendgateway.domain.enums.ApiKeyStatus;
import com.conduit.backendgateway.dto.admin.apikey.ApiKeyResponse;
import com.conduit.backendgateway.dto.admin.apikey.CreateApiKeyRequest;
import com.conduit.backendgateway.dto.admin.apikey.UpdateApiKeyRequest;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.ApiKeyRepository;
import com.conduit.backendgateway.security.AesGcmCipher;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AdminApiKeyService {

    private final ApiKeyRepository apiKeyRepository;
    private final AesGcmCipher aesGcmCipher;

    public AdminApiKeyService(ApiKeyRepository apiKeyRepository, AesGcmCipher aesGcmCipher) {
        this.apiKeyRepository = apiKeyRepository;
        this.aesGcmCipher = aesGcmCipher;
    }

    public List<ApiKeyResponse> listApiKeys() {
        return apiKeyRepository.findAll(Sort.by(Sort.Direction.DESC, "createdAt")).stream()
                .map(ApiKeyResponse::from)
                .toList();
    }

    @Transactional
    public ApiKeyResponse create(CreateApiKeyRequest request) {
        ApiKey apiKey = new ApiKey();
        apiKey.setProvider(request.provider());
        apiKey.setKeyEncrypted(aesGcmCipher.encrypt(request.rawKey()));
        apiKey.setPriority(request.priority() != null ? request.priority() : 0);
        apiKey.setStatus(ApiKeyStatus.active);
        return ApiKeyResponse.from(apiKeyRepository.saveAndFlush(apiKey));
    }

    @Transactional
    public ApiKeyResponse update(UUID apiKeyId, UpdateApiKeyRequest request) {
        ApiKey apiKey = findOrThrow(apiKeyId);
        apiKey.setStatus(request.status());
        apiKey.setPriority(request.priority());
        return ApiKeyResponse.from(apiKeyRepository.saveAndFlush(apiKey));
    }

    @Transactional
    public void delete(UUID apiKeyId) {
        ApiKey apiKey = findOrThrow(apiKeyId);
        apiKeyRepository.delete(apiKey);
    }

    private ApiKey findOrThrow(UUID apiKeyId) {
        return apiKeyRepository.findById(apiKeyId)
                .orElseThrow(() -> new ResourceNotFoundException("API key not found"));
    }
}
