package com.conduit.backendgateway.dto.conversation;

import com.conduit.backendgateway.domain.Message;
import com.conduit.backendgateway.dto.common.PageMetaDto;
import java.util.List;
import org.springframework.data.domain.Page;

public record MessageListResponse(List<MessageResponse> items, PageMetaDto page) {

    public static MessageListResponse from(Page<Message> page) {
        return new MessageListResponse(
                page.getContent().stream().map(MessageResponse::from).toList(),
                PageMetaDto.from(page));
    }
}
