package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.Message;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MessageRepository extends JpaRepository<Message, UUID> {

    Page<Message> findByConversationId(UUID conversationId, Pageable pageable);

    // Full, unpaginated history in chronological order - needed to resend the
    // whole conversation to the LLM each time (LLM API is stateless).
    List<Message> findByConversationIdOrderByCreatedAtAsc(UUID conversationId);
}
