package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.enums.AgentStatus;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AgentRepository extends JpaRepository<Agent, UUID> {

    Page<Agent> findByCreatorId(UUID creatorId, Pageable pageable);

    Page<Agent> findByStatus(AgentStatus status, Pageable pageable);

    Page<Agent> findByStatusAndTitleContainingIgnoreCase(AgentStatus status, String title, Pageable pageable);
}
