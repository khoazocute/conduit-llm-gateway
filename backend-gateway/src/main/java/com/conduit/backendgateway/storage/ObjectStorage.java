package com.conduit.backendgateway.storage;

// Kho file S3-compatible (CLAUDE.md muc 3). Tach interface de test khong can server that.
public interface ObjectStorage {

    // Luu file, tra ve dia chi luu tru dang s3://<bucket>/<key>.
    String put(String key, byte[] data, String contentType);
}
