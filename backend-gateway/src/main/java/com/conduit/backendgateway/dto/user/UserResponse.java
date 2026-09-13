package com.conduit.backendgateway.dto.user;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserRole;
import com.conduit.backendgateway.domain.enums.UserStatus;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public record UserResponse(
        UUID id,
        String email,
        @JsonProperty("full_name") String fullName,
        @JsonProperty("avatar_url") String avatarUrl,
        UserRole role,
        UserStatus status,
        @JsonProperty("email_verified") Boolean emailVerified,
        @JsonProperty("created_at") Instant createdAt) {

    public static UserResponse from(User user) {
        return new UserResponse(
                user.getId(),
                user.getEmail(),
                user.getFullName(),
                user.getAvatarUrl(),
                user.getRole(),
                user.getStatus(),
                user.getEmailVerified(),
                user.getCreatedAt());
    }
}
