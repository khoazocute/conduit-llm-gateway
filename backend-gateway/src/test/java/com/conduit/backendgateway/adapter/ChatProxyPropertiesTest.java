package com.conduit.backendgateway.adapter;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class ChatProxyPropertiesTest {

    private ChatProxyProperties properties;

    @BeforeEach
    void setUp() {
        properties = new ChatProxyProperties();
        properties.setProxyModelNames(Map.of("bifrost", Map.of(
                "gpt-4o-mini", "openai/gpt-4o-mini",
                "gemini-flash", "gemini/gemini-flash-latest",
                "claude-haiku", "anthropic/claude-haiku-4-5-20251001",
                "claude-sonnet", "anthropic/claude-sonnet-5",
                "gpt-4o", "openai/gpt-4o")));
        properties.setProxyFallbackChains(Map.of("bifrost",
                List.of("gpt-4o-mini", "gemini-flash", "claude-haiku", "claude-sonnet", "gpt-4o")));
    }

    @Test
    void bifrostFallbacksCoverTheOtherFourModelsCheapestFirst() {
        properties.setActiveProxy("bifrost");

        assertThat(properties.fallbacksFor("gpt-4o-mini")).containsExactly(
                "gemini/gemini-flash-latest",
                "anthropic/claude-haiku-4-5-20251001",
                "anthropic/claude-sonnet-5",
                "openai/gpt-4o");
    }

    @Test
    void primaryModelIsNeverRepeatedInItsOwnFallbacks() {
        properties.setActiveProxy("bifrost");

        assertThat(properties.fallbacksFor("claude-haiku"))
                .hasSize(4)
                .doesNotContain("anthropic/claude-haiku-4-5-20251001")
                .startsWith("openai/gpt-4o-mini");
    }

    @Test
    void proxiesWithoutAChainSendNoFallbacks() {
        properties.setActiveProxy("litellm");
        assertThat(properties.fallbacksFor("gpt-4o-mini")).isEmpty();

        properties.setActiveProxy("portkey");
        assertThat(properties.fallbacksFor("gpt-4o-mini")).isEmpty();
    }

    @Test
    void fallbackAliasesMapBackForPricing() {
        properties.setActiveProxy("bifrost");

        assertThat(properties.aliasOf("anthropic/claude-sonnet-5")).isEqualTo("claude-sonnet");
    }
}
