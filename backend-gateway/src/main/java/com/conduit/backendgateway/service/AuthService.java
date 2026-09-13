package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.CreditWallet;
import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserStatus;
import com.conduit.backendgateway.dto.auth.AuthResponse;
import com.conduit.backendgateway.dto.auth.LoginRequest;
import com.conduit.backendgateway.dto.auth.RegisterRequest;
import com.conduit.backendgateway.dto.user.UserResponse;
import com.conduit.backendgateway.exception.EmailAlreadyExistsException;
import com.conduit.backendgateway.exception.InvalidCredentialsException;
import com.conduit.backendgateway.exception.InvalidOrExpiredTokenException;
import com.conduit.backendgateway.repository.CreditWalletRepository;
import com.conduit.backendgateway.repository.UserRepository;
import com.conduit.backendgateway.security.JwtService;
import com.conduit.backendgateway.security.RefreshTokenStore;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import java.util.UUID;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final CreditWalletRepository creditWalletRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final RefreshTokenStore refreshTokenStore;

    public AuthService(
            UserRepository userRepository,
            CreditWalletRepository creditWalletRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            RefreshTokenStore refreshTokenStore) {
        this.userRepository = userRepository;
        this.creditWalletRepository = creditWalletRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.refreshTokenStore = refreshTokenStore;
    }

    @Transactional
    public AuthResult register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new EmailAlreadyExistsException("Email is already registered");
        }

        User user = new User();
        user.setEmail(request.email());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setFullName(request.fullName());
        user = userRepository.saveAndFlush(user);

        CreditWallet wallet = new CreditWallet();
        wallet.setUserId(user.getId());
        wallet.setBalance(0L);
        creditWalletRepository.save(wallet);

        return issueTokens(user);
    }

    public AuthResult login(LoginRequest request) {
        User user = userRepository.findByEmail(request.email())
                .orElseThrow(() -> new InvalidCredentialsException("Invalid email or password"));

        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new InvalidCredentialsException("Invalid email or password");
        }
        if (user.getStatus() == UserStatus.banned) {
            throw new InvalidCredentialsException("Invalid email or password");
        }

        return issueTokens(user);
    }

    public AuthResult refresh(String rawRefreshToken) {
        if (rawRefreshToken == null || rawRefreshToken.isBlank()) {
            throw new InvalidOrExpiredTokenException("Missing refresh token");
        }

        Jws<Claims> claims = jwtService.parseAndValidate(rawRefreshToken);
        if (!jwtService.isRefreshToken(claims)) {
            throw new InvalidOrExpiredTokenException("Not a refresh token");
        }

        UUID userId = jwtService.extractUserId(claims);
        String jti = jwtService.extractJti(claims);
        if (!refreshTokenStore.isValid(userId, jti)) {
            throw new InvalidOrExpiredTokenException("Refresh token has been revoked or superseded");
        }

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new InvalidOrExpiredTokenException("User no longer exists"));

        return issueTokens(user);
    }

    public void logout(UUID userId) {
        refreshTokenStore.revoke(userId);
    }

    private AuthResult issueTokens(User user) {
        String accessToken = jwtService.generateAccessToken(user);
        String refreshToken = jwtService.generateRefreshToken(user);

        Jws<Claims> refreshClaims = jwtService.parseAndValidate(refreshToken);
        refreshTokenStore.store(
                user.getId(), jwtService.extractJti(refreshClaims), jwtService.getRefreshTokenTtl());

        AuthResponse response = new AuthResponse(
                accessToken,
                (int) jwtService.getAccessTokenTtl().toSeconds(),
                UserResponse.from(user));
        return new AuthResult(response, refreshToken);
    }
}
