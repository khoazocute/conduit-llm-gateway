package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.domain.enums.UserStatus;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, UUID> {

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    Page<User> findByStatus(UserStatus status, Pageable pageable);

    // Search by email or full name. Derived queries (not string-built JPQL) so LIKE wildcards in the input are escaped.
    Page<User> findByEmailContainingIgnoreCaseOrFullNameContainingIgnoreCase(
            String email, String fullName, Pageable pageable);

    Page<User> findByStatusAndEmailContainingIgnoreCaseOrStatusAndFullNameContainingIgnoreCase(
            UserStatus statusForEmail, String email, UserStatus statusForName, String fullName, Pageable pageable);
}
