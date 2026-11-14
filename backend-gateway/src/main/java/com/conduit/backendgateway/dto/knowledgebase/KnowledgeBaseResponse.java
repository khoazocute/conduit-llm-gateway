package com.conduit.backendgateway.dto.knowledgebase;

import com.conduit.backendgateway.domain.KnowledgeBase;
import com.conduit.backendgateway.domain.enums.KbStatus;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public record KnowledgeBaseResponse(
        UUID id,
        @JsonProperty("agent_id") UUID agentId,
        @JsonProperty("file_name") String fileName,
        @JsonProperty("file_url") String fileUrl,
        KbStatus status,
        @JsonProperty("created_at") Instant createdAt) {

    public static KnowledgeBaseResponse from(KnowledgeBase kb) {
        return new KnowledgeBaseResponse(
                kb.getId(), kb.getAgentId(), kb.getFileName(), kb.getFileUrl(), kb.getStatus(),
                kb.getCreatedAt());
    }
}
