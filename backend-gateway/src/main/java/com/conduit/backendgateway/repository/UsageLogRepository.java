package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.UsageLog;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UsageLogRepository extends JpaRepository<UsageLog, UUID> {

    List<UsageLog> findByMessageId(UUID messageId);
}
