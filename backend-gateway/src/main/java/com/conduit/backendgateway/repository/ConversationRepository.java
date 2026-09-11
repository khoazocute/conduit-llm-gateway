package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.Conversation;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ConversationRepository extends JpaRepository<Conversation, UUID> {

    Page<Conversation> findByUserId(UUID userId, Pageable pageable);
}
