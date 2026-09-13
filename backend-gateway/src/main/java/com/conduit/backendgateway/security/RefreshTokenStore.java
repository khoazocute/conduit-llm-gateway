package com.conduit.backendgateway.security;

import java.time.Duration;
import java.util.Objects;
import java.util.UUID;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

/**
 * Tracks a single active refresh-token session per user in Redis, so logout and re-login
 * can actually revoke a previously issued refresh token (plain JWTs cannot be revoked).
 */
@Component
public class RefreshTokenStore {

    private static final String KEY_PREFIX = "refresh:";

    private final StringRedisTemplate redisTemplate;

    public RefreshTokenStore(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public void store(UUID userId, String jti, Duration ttl) {
        redisTemplate.opsForValue().set(key(userId), jti, ttl);
    }

    public boolean isValid(UUID userId, String jti) {
        String stored = redisTemplate.opsForValue().get(key(userId));
        return Objects.equals(stored, jti);
    }

    public void revoke(UUID userId) {
        redisTemplate.delete(key(userId));
    }

    private String key(UUID userId) {
        return KEY_PREFIX + userId;
    }
}
