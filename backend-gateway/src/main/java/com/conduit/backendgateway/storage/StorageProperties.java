package com.conduit.backendgateway.storage;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.storage")
@Getter
@Setter
public class StorageProperties {
    // Dev: SeaweedFS trong docker-compose (S3 API o cong 8333). Deploy: doi sang dich vu S3 that.
    private String endpoint = "http://localhost:8333";
    private String region = "us-east-1";
    private String bucket = "conduit-kb";
    private String accessKey = "";
    private String secretKey = "";
}
