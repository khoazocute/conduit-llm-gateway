package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.dto.agent.AgentListResponse;
import com.conduit.backendgateway.dto.agent.AgentResponse;
import com.conduit.backendgateway.dto.agent.RejectAgentRequest;
import com.conduit.backendgateway.service.AdminAgentService;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/admin/agents")
public class AdminAgentController {

    private final AdminAgentService adminAgentService;

    public AdminAgentController(AdminAgentService adminAgentService) {
        this.adminAgentService = adminAgentService;
    }

    @GetMapping("/pending")
    public AgentListResponse listPending(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return adminAgentService.listPending(PageRequest.of(page, size));
    }

    @PostMapping("/{agentId}/approve")
    public AgentResponse approve(@PathVariable UUID agentId) {
        return adminAgentService.approve(agentId);
    }

    @PostMapping("/{agentId}/reject")
    public AgentResponse reject(@PathVariable UUID agentId, @Valid @RequestBody RejectAgentRequest request) {
        return adminAgentService.reject(agentId, request);
    }
}
