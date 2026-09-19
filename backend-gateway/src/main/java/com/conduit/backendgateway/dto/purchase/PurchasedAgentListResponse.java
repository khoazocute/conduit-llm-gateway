package com.conduit.backendgateway.dto.purchase;

import com.conduit.backendgateway.dto.common.PageMetaDto;
import java.util.List;

public record PurchasedAgentListResponse(List<PurchasedAgentResponse> items, PageMetaDto page) {
}
