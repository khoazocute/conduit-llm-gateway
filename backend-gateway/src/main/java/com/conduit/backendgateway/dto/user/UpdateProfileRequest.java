package com.conduit.backendgateway.dto.user;

import com.fasterxml.jackson.annotation.JsonProperty;

public record UpdateProfileRequest(
        @JsonProperty("full_name") String fullName,
        @JsonProperty("avatar_url") String avatarUrl) {
}
