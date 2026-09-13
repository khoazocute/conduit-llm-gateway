package com.conduit.backendgateway.dto.admin;

import com.conduit.backendgateway.domain.enums.UserStatus;
import jakarta.validation.constraints.NotNull;

public record UpdateUserStatusRequest(@NotNull UserStatus status) {
}
