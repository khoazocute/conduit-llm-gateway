package com.conduit.backendgateway.dto.agent;

import com.conduit.backendgateway.dto.common.PageMetaDto;
import java.util.List;
import org.springframework.data.domain.Page;

public record AgentListResponse(List<AgentResponse> items, PageMetaDto page) {

    public static AgentListResponse from(Page<com.conduit.backendgateway.domain.Agent> page) {
        return new AgentListResponse(
                page.getContent().stream().map(AgentResponse::from).toList(),
                PageMetaDto.from(page));
    }
}
