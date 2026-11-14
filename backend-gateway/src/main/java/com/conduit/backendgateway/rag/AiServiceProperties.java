package com.conduit.backendgateway.rag;

import java.time.Duration;
import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.ai-service")
@Getter
@Setter
public class AiServiceProperties {
    private String baseUrl = "http://localhost:8000";
    // Token noi bo: chi backend duoc goi ai-service (moi lan goi embedding la mot lan ton phi).
    private String token = "";
    private Duration connectTimeout = Duration.ofSeconds(5);
    private Duration readTimeout = Duration.ofSeconds(120);
}
