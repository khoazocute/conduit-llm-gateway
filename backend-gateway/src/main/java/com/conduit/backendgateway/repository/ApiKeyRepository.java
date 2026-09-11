package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.ApiKey;
import com.conduit.backendgateway.domain.enums.ApiKeyStatus;
import com.conduit.backendgateway.domain.enums.LlmProvider;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ApiKeyRepository extends JpaRepository<ApiKey, UUID> {

    List<ApiKey> findByProviderAndStatusOrderByPriorityAsc(LlmProvider provider, ApiKeyStatus status);
}
