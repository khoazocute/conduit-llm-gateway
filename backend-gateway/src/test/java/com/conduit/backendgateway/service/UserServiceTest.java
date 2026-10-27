package com.conduit.backendgateway.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserRole;
import com.conduit.backendgateway.dto.user.UpdateProfileRequest;
import com.conduit.backendgateway.dto.user.UserResponse;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.UserRepository;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

/** TASK-52. */
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock private UserRepository userRepository;

    private UserService userService;
    private User user;

    @BeforeEach
    void setUp() {
        userService = new UserService(userRepository);
        user = new User();
        user.setId(UUID.randomUUID());
        user.setEmail("me@conduit.dev");
        user.setFullName("Old Name");
        user.setAvatarUrl("https://old");
        user.setRole(UserRole.creator);
    }

    @Test
    void getCurrentUser_returnsProfile_withoutPasswordHash() {
        user.setPasswordHash("$2a$secret-hash");
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        UserResponse r = userService.getCurrentUser(user.getId());
        assertThat(r.email()).isEqualTo("me@conduit.dev");
        assertThat(r.role()).isEqualTo(UserRole.creator);
        assertThat(r.toString()).doesNotContain("secret-hash");
    }

    @Test
    void updateProfile_onlyChangesProvidedFields() {
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        when(userRepository.saveAndFlush(any(User.class))).thenAnswer(inv -> inv.getArgument(0));

        UserResponse r = userService.updateProfile(user.getId(), new UpdateProfileRequest("New Name", null));
        assertThat(r.fullName()).isEqualTo("New Name");
        assertThat(r.avatarUrl()).isEqualTo("https://old");
    }

    @Test
    void updateProfile_cannotChangeRole() {
        // UpdateProfileRequest khong co truong role: tu nang quyen qua ho so la khong the.
        when(userRepository.findById(user.getId())).thenReturn(Optional.of(user));
        when(userRepository.saveAndFlush(any(User.class))).thenAnswer(inv -> inv.getArgument(0));
        assertThat(userService.updateProfile(user.getId(), new UpdateProfileRequest(null, null)).role())
                .isEqualTo(UserRole.creator);
    }

    @Test
    void unknownUser_isNotFound() {
        UUID missing = UUID.randomUUID();
        when(userRepository.findById(missing)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> userService.getCurrentUser(missing)).isInstanceOf(ResourceNotFoundException.class);
    }
}
