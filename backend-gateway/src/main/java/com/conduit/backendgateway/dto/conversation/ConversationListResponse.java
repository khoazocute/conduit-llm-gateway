package com.conduit.backendgateway.dto.conversation;

import com.conduit.backendgateway.domain.Conversation;
import com.conduit.backendgateway.dto.common.PageMetaDto;
import java.util.List;
import org.springframework.data.domain.Page;

public record ConversationListResponse(List<ConversationResponse> items, PageMetaDto page) {

    public static ConversationListResponse from(Page<Conversation> page) {
        return new ConversationListResponse(
                page.getContent().stream().map(ConversationResponse::from).toList(),
                PageMetaDto.from(page));
    }
}
