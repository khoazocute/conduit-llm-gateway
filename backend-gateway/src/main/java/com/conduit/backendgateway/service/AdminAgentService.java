package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.enums.AgentStatus;
import com.conduit.backendgateway.dto.agent.AgentListResponse;
import com.conduit.backendgateway.dto.agent.AgentResponse;
import com.conduit.backendgateway.dto.agent.RejectAgentRequest;
import com.conduit.backendgateway.exception.InvalidAgentStatusTransitionException;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.AgentRepository;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AdminAgentService {

    private final AgentRepository agentRepository;

    public AdminAgentService(AgentRepository agentRepository) {
        this.agentRepository = agentRepository;
    }

    public AgentListResponse listPending(Pageable pageable) {
        return AgentListResponse.from(agentRepository.findByStatus(AgentStatus.pending, pageable));
    }

    @Transactional
    public AgentResponse approve(UUID agentId) {
        Agent agent = findPendingOrThrow(agentId);
        agent.setStatus(AgentStatus.published);
        return AgentResponse.from(agentRepository.saveAndFlush(agent));
    }

    @Transactional
    public AgentResponse reject(UUID agentId, RejectAgentRequest request) {
        Agent agent = findPendingOrThrow(agentId);
        agent.setStatus(AgentStatus.rejected);
        agent.setRejectReason(request.rejectReason());
        return AgentResponse.from(agentRepository.saveAndFlush(agent));
    }

    private Agent findPendingOrThrow(UUID agentId) {
        Agent agent = agentRepository.findById(agentId)
                .orElseThrow(() -> new ResourceNotFoundException("Agent not found"));
        if (agent.getStatus() != AgentStatus.pending) {
            throw new InvalidAgentStatusTransitionException("Only a pending agent can be approved or rejected");
        }
        return agent;
    }
}
