package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.domain.enums.AgentStatus;
import com.conduit.backendgateway.dto.agent.AgentListResponse;
import com.conduit.backendgateway.dto.agent.AgentResponse;
import com.conduit.backendgateway.dto.agent.CreateAgentRequest;
import com.conduit.backendgateway.dto.agent.UpdateAgentRequest;
import com.conduit.backendgateway.security.UserPrincipal;
import com.conduit.backendgateway.service.AgentService;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/agents")
public class AgentController {

    private final AgentService agentService;

    public AgentController(AgentService agentService) {
        this.agentService = agentService;
    }

    @GetMapping
    public AgentListResponse listPublished(
            @RequestParam(required = false) String q,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return agentService.listPublished(q, PageRequest.of(page, size));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public AgentResponse create(
            @AuthenticationPrincipal UserPrincipal principal,
            @Valid @RequestBody CreateAgentRequest request) {
        return agentService.create(principal.getId(), request);
    }

    @GetMapping("/mine")
    public AgentListResponse listMine(
            @AuthenticationPrincipal UserPrincipal principal,
            @RequestParam(required = false) AgentStatus status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size);
        return agentService.listMine(principal.getId(), status, pageable);
    }

    @GetMapping("/{agentId}")
    public AgentResponse getById(@PathVariable UUID agentId) {
        return agentService.getById(agentId);
    }

    @PatchMapping("/{agentId}")
    public AgentResponse update(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID agentId,
            @Valid @RequestBody UpdateAgentRequest request) {
        return agentService.update(agentId, principal.getId(), request);
    }

    @PostMapping("/{agentId}/submit")
    public AgentResponse submit(
            @AuthenticationPrincipal UserPrincipal principal, @PathVariable UUID agentId) {
        return agentService.submit(agentId, principal.getId());
    }

    @PostMapping("/{agentId}/unpublish")
    public AgentResponse unpublish(
            @AuthenticationPrincipal UserPrincipal principal, @PathVariable UUID agentId) {
        return agentService.unpublish(agentId, principal.getId());
    }
}
