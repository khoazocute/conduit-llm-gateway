package com.conduit.backendgateway.storage;

import java.net.URI;
import org.springframework.stereotype.Component;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.NoSuchBucketException;

@Component
public class S3ObjectStorage implements ObjectStorage {

    private final S3Client s3;
    private final String bucket;
    private volatile boolean bucketReady;

    public S3ObjectStorage(StorageProperties properties) {
        this.bucket = properties.getBucket();
        // Path-style (http://host:port/bucket/key): SeaweedFS/MinIO tu dung khong co DNS theo bucket.
        // Tao client khong mo ket noi nao - app van khoi dong duoc khi kho chua chay.
        this.s3 = S3Client.builder()
                .endpointOverride(URI.create(properties.getEndpoint()))
                .region(Region.of(properties.getRegion()))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(properties.getAccessKey(), properties.getSecretKey())))
                .forcePathStyle(true)
                .httpClientBuilder(UrlConnectionHttpClient.builder())
                .build();
    }

    @Override
    public String put(String key, byte[] data, String contentType) {
        ensureBucket();
        s3.putObject(b -> b.bucket(bucket).key(key).contentType(contentType), RequestBody.fromBytes(data));
        return "s3://" + bucket + "/" + key;
    }

    // Tao bucket lan dau can (khong lam luc khoi dong, de test/context khong phu thuoc kho file).
    private void ensureBucket() {
        if (bucketReady) {
            return;
        }
        synchronized (this) {
            if (bucketReady) {
                return;
            }
            try {
                s3.headBucket(b -> b.bucket(bucket));
            } catch (NoSuchBucketException e) {
                s3.createBucket(b -> b.bucket(bucket));
            }
            bucketReady = true;
        }
    }
}
