package com.conduit.backendgateway.service;

import com.conduit.backendgateway.domain.Agent;
import com.conduit.backendgateway.domain.enums.AgentStatus;
import com.conduit.backendgateway.dto.agent.AgentListResponse;
import com.conduit.backendgateway.dto.agent.AgentResponse;
import com.conduit.backendgateway.dto.agent.CreateAgentRequest;
import com.conduit.backendgateway.dto.agent.UpdateAgentRequest;
import com.conduit.backendgateway.exception.ForbiddenActionException;
import com.conduit.backendgateway.exception.InvalidAgentStatusTransitionException;
import com.conduit.backendgateway.exception.ResourceNotFoundException;
import com.conduit.backendgateway.repository.AgentRepository;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AgentService {

    private final AgentRepository agentRepository;

    public AgentService(AgentRepository agentRepository) {
        this.agentRepository = agentRepository;
    }

    public AgentListResponse listPublished(String q, Pageable pageable) {
        Page<Agent> page = (q == null || q.isBlank())
                ? agentRepository.findByStatus(AgentStatus.published, pageable)
                : agentRepository.findByStatusAndTitleContainingIgnoreCase(AgentStatus.published, q, pageable);
        return AgentListResponse.from(page);
    }

    @Transactional
    public AgentResponse create(UUID creatorId, CreateAgentRequest request) {
        Agent agent = new Agent();
        agent.setCreatorId(creatorId);
        agent.setTitle(request.title());
        agent.setIntroduction(request.introduction());
        if (request.agentType() != null) {
            agent.setAgentType(request.agentType());
        }
        agent.setPriceVnd(request.priceVnd());
        agent.setDefaultCreditGranted(request.defaultCreditGranted());
        return AgentResponse.from(agentRepository.saveAndFlush(agent));
    }

    public AgentListResponse listMine(UUID creatorId, AgentStatus status, Pageable pageable) {
        Page<Agent> page = (status == null)
                ? agentRepository.findByCreatorId(creatorId, pageable)
                : agentRepository.findByCreatorIdAndStatus(creatorId, status, pageable);
        return AgentListResponse.from(page);
    }

    public AgentResponse getById(UUID agentId) {
        return AgentResponse.from(findAgentOrThrow(agentId));
    }

    @Transactional
    public AgentResponse update(UUID agentId, UUID currentUserId, UpdateAgentRequest request) {
        Agent agent = findAgentOrThrow(agentId);
        requireOwnership(agent, currentUserId);
        requireEditableStatus(agent);

        if (request.title() != null) {
            agent.setTitle(request.title());
        }
        if (request.introduction() != null) {
            agent.setIntroduction(request.introduction());
        }
        if (request.priceVnd() != null) {
            agent.setPriceVnd(request.priceVnd());
        }
        if (request.defaultCreditGranted() != null) {
            agent.setDefaultCreditGranted(request.defaultCreditGranted());
        }
        return AgentResponse.from(agentRepository.saveAndFlush(agent));
    }

    @Transactional
    public AgentResponse submit(UUID agentId, UUID currentUserId) {
        Agent agent = findAgentOrThrow(agentId);
        requireOwnership(agent, currentUserId);
        requireSubmittableStatus(agent);

        agent.setStatus(AgentStatus.pending);
        agent.setRejectReason(null);
        return AgentResponse.from(agentRepository.saveAndFlush(agent));
    }

    @Transactional
    public AgentResponse unpublish(UUID agentId, UUID currentUserId) {
        Agent agent = findAgentOrThrow(agentId);
        requireOwnership(agent, currentUserId);

        if (agent.getStatus() != AgentStatus.published) {
            throw new InvalidAgentStatusTransitionException("Only a published agent can be unpublished");
        }
        agent.setStatus(AgentStatus.unpublished);
        return AgentResponse.from(agentRepository.saveAndFlush(agent));
    }

    private Agent findAgentOrThrow(UUID agentId) {
        return agentRepository.findById(agentId)
                .orElseThrow(() -> new ResourceNotFoundException("Agent not found"));
    }

    private void requireOwnership(Agent agent, UUID currentUserId) {
        if (!agent.getCreatorId().equals(currentUserId)) {
            throw new ForbiddenActionException("You do not own this agent");
        }
    }

    private void requireEditableStatus(Agent agent) {
        if (agent.getStatus() != AgentStatus.draft && agent.getStatus() != AgentStatus.rejected) {
            throw new InvalidAgentStatusTransitionException(
                    "Agent must be in draft or rejected status for this action");
        }
    }

    // Submitting also accepts `unpublished` so a creator can send a previously
    // published (then unpublished) agent back through admin review, instead of
    // it being stuck forever with no path back to `published`.
    private void requireSubmittableStatus(Agent agent) {
        AgentStatus status = agent.getStatus();
        if (status != AgentStatus.draft && status != AgentStatus.rejected && status != AgentStatus.unpublished) {
            throw new InvalidAgentStatusTransitionException(
                    "Agent must be in draft, rejected, or unpublished status to submit for review");
        }
    }
}
