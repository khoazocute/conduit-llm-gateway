package com.conduit.backendgateway.repository;

import com.conduit.backendgateway.domain.RoutingDecision;
import com.conduit.backendgateway.domain.enums.RoutingProxy;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RoutingDecisionRepository extends JpaRepository<RoutingDecision, UUID> {

    List<RoutingDecision> findByProxyName(RoutingProxy proxyName);

    List<RoutingDecision> findByMessageId(UUID messageId);
}
