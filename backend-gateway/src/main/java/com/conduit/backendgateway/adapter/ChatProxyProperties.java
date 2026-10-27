package com.conduit.backendgateway.adapter;

import java.util.List;
import java.util.Map;
import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

// Cau hinh Chat MVP: proxy nao dang "active" la config tinh, KHONG phai
// logic routing thong minh - routing that la viec cua Tuan 9-10 (xem
// proxy-configs/litellm/config.yaml, routing_strategy: simple-shuffle).
@Component
@ConfigurationProperties(prefix = "app.chat")
@Getter
@Setter
public class ChatProxyProperties {
    private String activeProxy = "litellm";
    // TASK-51: rong = dung mac dinh theo proxy (proxyDefaultModels). Dat CHAT_DEFAULT_MODEL thi
    // gia tri do thang moi proxy - dry_run.sh dung de tai lap dung thi nghiem.
    private String defaultModel = "";
    // TASK-51: chat thuong qua LiteLLM phai vao nhom conduit-pool (cost-based-routing +
    // fallbacks). Bifrost/Portkey khong co alias do -> khong khai thi roi ve FALLBACK_MODEL.
    private Map<String, String> proxyDefaultModels = Map.of();
    static final String FALLBACK_MODEL = "gpt-4o-mini";
    // D7: gioi han sinh token, gui kem moi request. <= 0 thi khong gui.
    private int maxTokens = 1024;
    // D7: greedy decoding - protocol pass@1 cua HumanEval yeu cau temperature 0, va
    // khong co no thi cung 1 proxy + 1 model + 1 cau hoi co the dat/truot khac nhau giua
    // cac lan lap (thay that o dry-run 16/10: litellm ifeval_01 dat/truot/dat).
    // Am thi khong gui (de nha cung cap tu quyet) - dung khi can tat co y.
    // LUU Y: claude-sonnet-5 TU CHOI tham so nay (HTTP 400 "temperature is deprecated for
    // this model"), nen no da bi bo khoi moi duong dinh tuyen - xem proxy-configs/.
    private double temperature = 0.0;
    private Map<String, String> proxyBaseUrls = Map.of();
    private Map<String, String> proxyApiKeys = Map.of();
    private Map<String, Map<String, String>> proxyModelNames = Map.of();
    private Map<String, List<String>> proxyFallbackChains = Map.of();
    // H2/H3: chi doc khi activeProxy=portkey - xem HttpProxyChatClient.
    private String portkeyConfigPath = "../proxy-configs/portkey/config.json";

    public String effectiveDefaultModel() {
        if (defaultModel != null && !defaultModel.isBlank()) {
            return defaultModel;
        }
        return proxyDefaultModels.getOrDefault(activeProxy, FALLBACK_MODEL);
    }

    public String activeBaseUrl() {
        return proxyBaseUrls.get(activeProxy);
    }

    public String activeApiKey() {
        return proxyApiKeys.getOrDefault(activeProxy, "");
    }

    public String upstreamModel(String alias) {
        return proxyModelNames.getOrDefault(activeProxy, Map.of()).getOrDefault(alias, alias);
    }

    public List<String> fallbacksFor(String alias) {
        return proxyFallbackChains.getOrDefault(activeProxy, List.of()).stream()
                .filter(a -> !a.equals(alias))
                .map(this::upstreamModel)
                .toList();
    }

    public String aliasOf(String upstreamModel) {
        return proxyModelNames.getOrDefault(activeProxy, Map.of()).entrySet().stream()
                .filter(e -> e.getValue().equals(upstreamModel))
                .map(Map.Entry::getKey)
                .findFirst()
                .orElse(upstreamModel);
    }
}
