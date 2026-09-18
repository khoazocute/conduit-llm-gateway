package com.conduit.backendgateway.adapter;

import java.util.List;

/**
 * Provider Adapter (CLAUDE.md muc 5): moi loi goi LLM phai di qua lop nay,
 * KHONG goi thang SDK OpenAI/Anthropic trong business logic. Impl thuc te
 * goi qua 1 trong 3 proxy da danh gia (litellm/bifrost/portkey), vi ca 3 deu
 * expose API kieu OpenAI-compatible nen 1 client chung la du - khong can
 * adapter rieng cho tung provider.
 */
public interface ProxyChatClient {
    ChatCompletionResult complete(String model, List<ChatTurn> messages);
}
