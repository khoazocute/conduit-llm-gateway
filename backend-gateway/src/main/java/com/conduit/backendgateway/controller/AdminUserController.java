package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.domain.enums.UserStatus;
import com.conduit.backendgateway.dto.admin.UpdateUserStatusRequest;
import com.conduit.backendgateway.dto.admin.UserListResponse;
import com.conduit.backendgateway.dto.user.UserResponse;
import com.conduit.backendgateway.service.AdminUserService;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
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
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return adminUserService.listUsers(status, PageRequest.of(page, size));
    }

    @PatchMapping("/{userId}/status")
    public UserResponse updateStatus(
            @PathVariable UUID userId, @Valid @RequestBody UpdateUserStatusRequest request) {
        return adminUserService.updateStatus(userId, request);
    }
}
