package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.conduit.backendgateway.domain.CreditWallet;
import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserRole;
import com.conduit.backendgateway.domain.enums.UserStatus;
import com.conduit.backendgateway.dto.auth.LoginRequest;
import com.conduit.backendgateway.dto.auth.RegisterRequest;
import com.conduit.backendgateway.exception.EmailAlreadyExistsException;
import com.conduit.backendgateway.exception.InvalidCredentialsException;
import com.conduit.backendgateway.exception.InvalidOrExpiredTokenException;
import com.conduit.backendgateway.repository.CreditWalletRepository;
import com.conduit.backendgateway.repository.UserRepository;
import com.conduit.backendgateway.security.JwtProperties;
import com.conduit.backendgateway.security.JwtService;
import com.conduit.backendgateway.security.RefreshTokenStore;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.util.ReflectionTestUtils;

/**
 * TASK-52. JwtService that (token that duoc phat ra va doc lai), repository va Redis la mock.
 * BCrypt cost 4 cho nhanh; khong anh huong logic.
 */
@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    private static final String SECRET = "test-only-secret-key-must-be-at-least-32-bytes-long";

    @Mock private UserRepository userRepository;
    @Mock private CreditWalletRepository creditWalletRepository;
    @Mock private RefreshTokenStore refreshTokenStore;

    private final PasswordEncoder passwordEncoder = new BCryptPasswordEncoder(4);
    private JwtService jwtService;
    private AuthService authService;

    @BeforeEach
    void setUp() {
        jwtService = new JwtService(new JwtProperties(SECRET, 20, 7));
        ReflectionTestUtils.invokeMethod(jwtService, "init");
        authService = new AuthService(userRepository, creditWalletRepository, passwordEncoder, jwtService,
                refreshTokenStore);
    }

    /** saveAndFlush tra lai chinh user do, gan id nhu DB that. */
    private void stubSaveAssignsId() {
        when(userRepository.saveAndFlush(any(User.class))).thenAnswer(inv -> {
            User u = inv.getArgument(0);
            u.setId(UUID.randomUUID());
            return u;
        });
    }

    private User existingUser(String rawPassword, UserStatus status) {
        User u = new User();
        u.setId(UUID.randomUUID());
        u.setEmail("someone@conduit.dev");
        u.setPasswordHash(passwordEncoder.encode(rawPassword));
        u.setRole(UserRole.user);
        u.setStatus(status);
        return u;
    }

    // ------------------------------------------------------------------ register

    @Test
    void register_withoutRole_defaultsToUser_createsEmptyWallet_andStoresRefreshSession() {
        stubSaveAssignsId();
        AuthResult result = authService.register(
                new RegisterRequest("a@conduit.dev", "password123", "A", null));

        assertThat(result.response().user().role()).isEqualTo(UserRole.user);
        assertThat(result.response().accessToken()).isNotBlank();
        assertThat(result.refreshToken()).isNotBlank();

        ArgumentCaptor<CreditWallet> wallet = ArgumentCaptor.forClass(CreditWallet.class);
        verify(creditWalletRepository).save(wallet.capture());
        assertThat(wallet.getValue().getBalance()).isZero();
        assertThat(wallet.getValue().getUserId()).isEqualTo(result.response().user().id());

        verify(refreshTokenStore).store(eq(result.response().user().id()), anyString(), any());
    }

    @Test
    void register_withCreatorRole_createsCreator() {
        stubSaveAssignsId();
        AuthResult result = authService.register(
                new RegisterRequest("c@conduit.dev", "password123", "C", "creator"));
        assertThat(result.response().user().role()).isEqualTo(UserRole.creator);
    }

    @Test
    void register_neverStoresPlainPassword() {
        stubSaveAssignsId();
        authService.register(new RegisterRequest("p@conduit.dev", "password123", "P", null));
        ArgumentCaptor<User> saved = ArgumentCaptor.forClass(User.class);
        verify(userRepository).saveAndFlush(saved.capture());
        assertThat(saved.getValue().getPasswordHash()).isNotEqualTo("password123");
        assertThat(passwordEncoder.matches("password123", saved.getValue().getPasswordHash())).isTrue();
    }

    @Test
    void register_duplicateEmail_isRejected_andNothingIsSaved() {
        when(userRepository.existsByEmail("dup@conduit.dev")).thenReturn(true);
        assertThatThrownBy(() -> authService.register(
                new RegisterRequest("dup@conduit.dev", "password123", "D", null)))
                .isInstanceOf(EmailAlreadyExistsException.class);
        verify(userRepository, never()).saveAndFlush(any());
        verify(creditWalletRepository, never()).save(any());
    }

    // ------------------------------------------------------------------ login

    @Test
    void login_correctPassword_issuesTokens() {
        User u = existingUser("password123", UserStatus.active);
        when(userRepository.findByEmail(u.getEmail())).thenReturn(Optional.of(u));
        AuthResult result = authService.login(new LoginRequest(u.getEmail(), "password123"));
        assertThat(result.response().user().id()).isEqualTo(u.getId());
        verify(refreshTokenStore).store(eq(u.getId()), anyString(), any());
    }

    @Test
    void login_wrongPassword_unknownEmail_andBannedUser_allGiveTheSameError() {
        User u = existingUser("password123", UserStatus.active);
        when(userRepository.findByEmail(u.getEmail())).thenReturn(Optional.of(u));
        when(userRepository.findByEmail("ghost@conduit.dev")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authService.login(new LoginRequest(u.getEmail(), "wrong-password")))
                .isInstanceOf(InvalidCredentialsException.class)
                .hasMessage("Invalid email or password");
        assertThatThrownBy(() -> authService.login(new LoginRequest("ghost@conduit.dev", "password123")))
                .isInstanceOf(InvalidCredentialsException.class)
                .hasMessage("Invalid email or password");

        u.setStatus(UserStatus.banned);
        // Bi ban nhung dung mat khau: van cung thong diep, khong lo la tai khoan ton tai.
        assertThatThrownBy(() -> authService.login(new LoginRequest(u.getEmail(), "password123")))
                .isInstanceOf(InvalidCredentialsException.class)
                .hasMessage("Invalid email or password");
        verify(refreshTokenStore, never()).store(any(), any(), any());
    }

    // ------------------------------------------------------------------ refresh

    @Test
    void refresh_withRevokedSession_isRejected() {
        User u = existingUser("password123", UserStatus.active);
        String refresh = jwtService.generateRefreshToken(u);
        when(refreshTokenStore.isValid(eq(u.getId()), anyString())).thenReturn(false);

        assertThatThrownBy(() -> authService.refresh(refresh))
                .isInstanceOf(InvalidOrExpiredTokenException.class);
    }

    @Test
    void refresh_withAnAccessTokenInsteadOfRefresh_isRejected() {
        User u = existingUser("password123", UserStatus.active);
        String access = jwtService.generateAccessToken(u);
        assertThatThrownBy(() -> authService.refresh(access))
                .isInstanceOf(InvalidOrExpiredTokenException.class)
                .hasMessage("Not a refresh token");
    }

    @Test
    void refresh_missingToken_isRejected() {
        assertThatThrownBy(() -> authService.refresh(null)).isInstanceOf(InvalidOrExpiredTokenException.class);
        assertThatThrownBy(() -> authService.refresh("  ")).isInstanceOf(InvalidOrExpiredTokenException.class);
    }

    // ------------------------------------------------------------------ logout

    @Test
    void logout_withExpiredAccessToken_stillRevokesTheSessionFromTheRefreshCookie() {
        // Hoi quy: principal null (access token het han) tung gay NPE 500 va phien tu song lai.
        User u = existingUser("password123", UserStatus.active);
        String refresh = jwtService.generateRefreshToken(u);
        authService.logout(null, refresh);
        verify(refreshTokenStore).revoke(u.getId());
    }

    @Test
    void logout_isIdempotent_withGarbageOrMissingToken() {
        assertThatCode(() -> authService.logout(null, "not-a-jwt")).doesNotThrowAnyException();
        assertThatCode(() -> authService.logout(null, null)).doesNotThrowAnyException();
        verify(refreshTokenStore, never()).revoke(any());
    }

    @Test
    void logout_withAuthenticatedUser_revokesThatUser() {
        UUID id = UUID.randomUUID();
        authService.logout(id, null);
        verify(refreshTokenStore).revoke(id);
    }
}
