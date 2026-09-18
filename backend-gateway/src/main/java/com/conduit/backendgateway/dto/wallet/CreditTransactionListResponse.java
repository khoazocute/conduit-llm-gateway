package com.conduit.backendgateway.dto.wallet;

import com.conduit.backendgateway.domain.CreditTransaction;
import com.conduit.backendgateway.dto.common.PageMetaDto;
import java.util.List;
import org.springframework.data.domain.Page;

public record CreditTransactionListResponse(List<CreditTransactionResponse> items, PageMetaDto page) {

    public static CreditTransactionListResponse from(Page<CreditTransaction> page) {
        return new CreditTransactionListResponse(
                page.getContent().stream().map(CreditTransactionResponse::from).toList(),
                PageMetaDto.from(page));
    }
}
