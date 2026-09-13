package com.conduit.backendgateway.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserRole;
import com.conduit.backendgateway.domain.enums.UserStatus;
import com.conduit.backendgateway.exception.InvalidOrExpiredTokenException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;
import javax.crypto.SecretKey;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

class JwtServiceTest {

    private static final String SECRET = "test-only-secret-key-must-be-at-least-32-bytes-long";

    private JwtService jwtService;
    private User user;

    @BeforeEach
    void setUp() {
        JwtProperties properties = new JwtProperties(SECRET, 20, 7);
        jwtService = new JwtService(properties);
        ReflectionTestUtils.invokeMethod(jwtService, "init");

        user = new User();
        user.setId(UUID.randomUUID());
        user.setEmail("jwt-test@conduit.dev");
        user.setRole(UserRole.user);
        user.setStatus(UserStatus.active);
    }

    @Test
    void generatedAccessTokenParsesBackToSameUserAndRole() {
        String token = jwtService.generateAccessToken(user);

        var claims = jwtService.parseAndValidate(token);

        assertThat(jwtService.isAccessToken(claims)).isTrue();
        assertThat(jwtService.extractUserId(claims)).isEqualTo(user.getId());
        assertThat(jwtService.extractRole(claims)).isEqualTo(UserRole.user);
    }

    @Test
    void expiredTokenIsRejected() {
        SecretKey key = Keys.hmacShaKeyFor(SECRET.getBytes());
        Instant past = Instant.now().minusSeconds(3600);
        String expiredToken = Jwts.builder()
                .subject(user.getId().toString())
                .claim("type", "access")
                .issuedAt(Date.from(past.minusSeconds(60)))
                .expiration(Date.from(past))
                .signWith(key)
                .compact();

        assertThatThrownBy(() -> jwtService.parseAndValidate(expiredToken))
                .isInstanceOf(InvalidOrExpiredTokenException.class);
    }

    @Test
    void tokenWithTamperedSignatureIsRejected() {
        String token = jwtService.generateAccessToken(user);
        String tampered = token.substring(0, token.length() - 4) + "abcd";

        assertThatThrownBy(() -> jwtService.parseAndValidate(tampered))
                .isInstanceOf(InvalidOrExpiredTokenException.class);
    }

    @Test
    void refreshTokenIsNotAcceptedAsAccessToken() {
        String refreshToken = jwtService.generateRefreshToken(user);

        var claims = jwtService.parseAndValidate(refreshToken);

        assertThat(jwtService.isAccessToken(claims)).isFalse();
        assertThat(jwtService.isRefreshToken(claims)).isTrue();
    }
}
