package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.domain.enums.UserStatus;
import com.conduit.backendgateway.dto.admin.UpdateUserStatusRequest;
import com.conduit.backendgateway.dto.admin.UserListResponse;
import com.conduit.backendgateway.dto.user.UserResponse;
import com.conduit.backendgateway.security.UserPrincipal;
import com.conduit.backendgateway.service.AdminUserService;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/admin/users")
public class AdminUserController {

    private final AdminUserService adminUserService;

    public AdminUserController(AdminUserService adminUserService) {
        this.adminUserService = adminUserService;
    }

    @GetMapping
    public UserListResponse listUsers(
            @RequestParam(required = false) UserStatus status,
            @RequestParam(required = false) String q,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        // Newest first, so a just-registered account is on page 0 (an unsorted page is arbitrary).
        PageRequest pageable = PageRequest.of(
                Math.max(page, 0), Math.min(Math.max(size, 1), 100), Sort.by(Sort.Direction.DESC, "createdAt"));
        return adminUserService.listUsers(status, q, pageable);
    }

    @PatchMapping("/{userId}/status")
    public UserResponse updateStatus(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID userId,
            @Valid @RequestBody UpdateUserStatusRequest request) {
        return adminUserService.updateStatus(userId, request, principal.getId());
    }
}
