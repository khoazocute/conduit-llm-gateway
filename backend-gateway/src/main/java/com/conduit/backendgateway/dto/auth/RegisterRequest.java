package com.conduit.backendgateway.dto.auth;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * {@code role} (D8, 2026-10-22): nguoi dang ky tu chon "mua agent" ({@code user}) hay "tao agent"
 * ({@code creator}). Bo trong = {@code user}. {@code admin} KHONG duoc tu chon -> 400 qua
 * {@code @Pattern}, cung dinh dang loi validation voi cac truong khac. Admin chi tao qua SQL.
 * An toan vi agent cua creator van phai qua admin duyet truoc khi len cho.
 */
public record RegisterRequest(
        @NotBlank @Email String email,
        @NotBlank @Size(min = 8) String password,
        @NotBlank @JsonProperty("full_name") String fullName,
        @Pattern(regexp = "user|creator", message = "must be 'user' or 'creator'") String role) {
}
