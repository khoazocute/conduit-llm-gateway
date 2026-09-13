package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserStatus;
import com.conduit.backendgateway.dto.admin.UpdateUserStatusRequest;
import com.conduit.backendgateway.dto.admin.UserListResponse;
import com.conduit.backendgateway.dto.user.UserResponse;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.UserRepository;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AdminUserService {

    private final UserRepository userRepository;

    public AdminUserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public UserListResponse listUsers(UserStatus status, Pageable pageable) {
        return UserListResponse.from(
                status == null
                        ? userRepository.findAll(pageable)
                        : userRepository.findByStatus(status, pageable));
    }

    @Transactional
    public UserResponse updateStatus(UUID userId, UpdateUserStatusRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        user.setStatus(request.status());
        return UserResponse.from(userRepository.saveAndFlush(user));
    }
}
