package com.conduit.backendgateway.service;

import com.conduit.backendgateway.dto.auth.AuthResponse;

/**
 * Carries the AuthResponse body plus the raw refresh token value, which the controller
 * (not the service, to keep it framework-agnostic) sets as an HttpOnly cookie.
 */
public record AuthResult(AuthResponse response, String refreshToken) {
}
