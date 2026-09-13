package com.conduit.backendgateway.security;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserRole;
import com.conduit.backendgateway.exception.InvalidOrExpiredTokenException;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;
import javax.crypto.SecretKey;
import org.springframework.stereotype.Service;

@Service
public class JwtService {

    private static final String CLAIM_ROLE = "role";
    private static final String CLAIM_EMAIL = "email";
    private static final String CLAIM_TYPE = "type";
    private static final String TYPE_ACCESS = "access";
    private static final String TYPE_REFRESH = "refresh";

    private final JwtProperties properties;
    private SecretKey signingKey;

    public JwtService(JwtProperties properties) {
        this.properties = properties;
    }

    @PostConstruct
    void init() {
        byte[] secretBytes = properties.secret().getBytes(StandardCharsets.UTF_8);
        if (secretBytes.length < 32) {
            throw new IllegalStateException(
                    "app.jwt.secret must be at least 32 bytes (256 bits) for HS256 signing");
        }
        this.signingKey = Keys.hmacShaKeyFor(secretBytes);
    }

    public String generateAccessToken(User user) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(user.getId().toString())
                .claim(CLAIM_ROLE, user.getRole().name())
                .claim(CLAIM_EMAIL, user.getEmail())
                .claim(CLAIM_TYPE, TYPE_ACCESS)
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plus(getAccessTokenTtl())))
                .signWith(signingKey)
                .compact();
    }

    public String generateRefreshToken(User user) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(user.getId().toString())
                .id(UUID.randomUUID().toString())
                .claim(CLAIM_TYPE, TYPE_REFRESH)
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plus(getRefreshTokenTtl())))
                .signWith(signingKey)
                .compact();
    }

    public Jws<Claims> parseAndValidate(String token) {
        try {
            return Jwts.parser()
                    .verifyWith(signingKey)
                    .build()
                    .parseSignedClaims(token);
        } catch (JwtException | IllegalArgumentException ex) {
            throw new InvalidOrExpiredTokenException("Invalid or expired token");
        }
    }

    public UUID extractUserId(Jws<Claims> claims) {
        return UUID.fromString(claims.getPayload().getSubject());
    }

    public UserRole extractRole(Jws<Claims> claims) {
        return UserRole.valueOf(claims.getPayload().get(CLAIM_ROLE, String.class));
    }

    public String extractJti(Jws<Claims> claims) {
        return claims.getPayload().getId();
    }

    public String extractType(Jws<Claims> claims) {
        return claims.getPayload().get(CLAIM_TYPE, String.class);
    }

    public boolean isAccessToken(Jws<Claims> claims) {
        return TYPE_ACCESS.equals(extractType(claims));
    }

    public boolean isRefreshToken(Jws<Claims> claims) {
        return TYPE_REFRESH.equals(extractType(claims));
    }

    public Duration getAccessTokenTtl() {
        return Duration.ofMinutes(properties.accessTokenExpirationMinutes());
    }

    public Duration getRefreshTokenTtl() {
        return Duration.ofDays(properties.refreshTokenExpirationDays());
    }
}
