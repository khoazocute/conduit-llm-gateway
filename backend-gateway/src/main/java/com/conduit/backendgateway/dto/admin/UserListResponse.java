package com.conduit.backendgateway.dto.admin;

import com.conduit.backendgateway.domain.User;
import com.conduit.backendgateway.dto.common.PageMetaDto;
import com.conduit.backendgateway.dto.user.UserResponse;
import java.util.List;
import org.springframework.data.domain.Page;

public record UserListResponse(List<UserResponse> items, PageMetaDto page) {

    public static UserListResponse from(Page<User> page) {
        return new UserListResponse(
                page.getContent().stream().map(UserResponse::from).toList(),
                PageMetaDto.from(page));
    }
}
