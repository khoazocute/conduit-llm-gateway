package com.conduit.backendgateway.adapter;

import java.util.Map;
import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

// Cau hinh Chat MVP: proxy nao dang "active" la config tinh, KHONG phai
// logic routing thong minh - routing that la viec cua Tuan 9-10 (xem
// proxy-configs/litellm/config.yaml, routing_strategy: simple-shuffle).
@Component
@ConfigurationProperties(prefix = "app.chat")
@Getter
@Setter
public class ChatProxyProperties {
    private String activeProxy = "litellm";
    private String defaultModel = "gpt-4o-mini";
    private Map<String, String> proxyBaseUrls = Map.of();
    private Map<String, String> proxyApiKeys = Map.of();

    public String activeBaseUrl() {
        return proxyBaseUrls.get(activeProxy);
    }

    public String activeApiKey() {
        return proxyApiKeys.getOrDefault(activeProxy, "");
    }
}
