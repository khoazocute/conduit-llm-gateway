package com.conduit.backendgateway.controller;

import com.conduit.backendgateway.dto.knowledgebase.KnowledgeBaseResponse;
import com.conduit.backendgateway.security.UserPrincipal;
import com.conduit.backendgateway.service.KnowledgeBaseService;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

// Tag OpenAPI "Knowledge Base (Should-have)". DELETE /knowledge-base/{kbId} chua lam (ngoai TASK-57a).
@RestController
public class KnowledgeBaseController {

    private final KnowledgeBaseService knowledgeBaseService;

    public KnowledgeBaseController(KnowledgeBaseService knowledgeBaseService) {
        this.knowledgeBaseService = knowledgeBaseService;
    }

    // 202: file da luu, chia doan + embedding chay nen (processing -> ready/failed).
    @PostMapping(path = "/agents/{agentId}/knowledge-base", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseStatus(HttpStatus.ACCEPTED)
    public KnowledgeBaseResponse upload(
            @AuthenticationPrincipal UserPrincipal principal,
            @PathVariable UUID agentId,
            @RequestParam("file") MultipartFile file) {
        return knowledgeBaseService.upload(agentId, principal.getId(), file);
    }

    @GetMapping("/agents/{agentId}/knowledge-base")
    public List<KnowledgeBaseResponse> list(
            @AuthenticationPrincipal UserPrincipal principal, @PathVariable UUID agentId) {
        return knowledgeBaseService.list(agentId, principal.getId());
    }
}
