package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserStatus;
import com.conduit.backendgateway.dto.admin.UpdateUserStatusRequest;
import com.conduit.backendgateway.dto.admin.UserListResponse;
import com.conduit.backendgateway.dto.user.UserResponse;
import com.conduit.backendgateway.exception.ForbiddenActionException;
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

    public UserListResponse listUsers(UserStatus status, String q, Pageable pageable) {
        String term = q == null ? "" : q.trim();
        if (term.isEmpty()) {
            return UserListResponse.from(
                    status == null
                            ? userRepository.findAll(pageable)
                            : userRepository.findByStatus(status, pageable));
        }
        return UserListResponse.from(
                status == null
                        ? userRepository.findByEmailContainingIgnoreCaseOrFullNameContainingIgnoreCase(
                                term, term, pageable)
                        : userRepository.findByStatusAndEmailContainingIgnoreCaseOrStatusAndFullNameContainingIgnoreCase(
                                status, term, status, term, pageable));
    }

    @Transactional
    public UserResponse updateStatus(UUID userId, UpdateUserStatusRequest request, UUID currentAdminId) {
        // An admin banning their own account would lock them out of the admin panel.
        if (userId.equals(currentAdminId) && request.status() == UserStatus.banned) {
            throw new ForbiddenActionException("You cannot ban your own account");
        }
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        user.setStatus(request.status());
        return UserResponse.from(userRepository.saveAndFlush(user));
    }
}
