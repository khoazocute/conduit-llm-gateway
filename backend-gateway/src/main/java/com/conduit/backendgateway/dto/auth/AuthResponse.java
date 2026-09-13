package com.conduit.backendgateway.dto.auth;

import com.conduit.backendgateway.dto.user.UserResponse;
import com.fasterxml.jackson.annotation.JsonProperty;

public record AuthResponse(
        @JsonProperty("access_token") String accessToken,
        @JsonProperty("expires_in") int expiresIn,
        UserResponse user) {
}
