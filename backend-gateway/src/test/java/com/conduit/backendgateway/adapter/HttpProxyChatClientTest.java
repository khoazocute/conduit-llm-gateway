package com.conduit.backendgateway.adapter;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import org.junit.jupiter.api.Test;

class HttpProxyChatClientTest {

    // Same order as proxy-configs/portkey/config.json.
    private static final List<String> PORTKEY_TARGETS =
            List.of("gpt-4o-mini", "gemini-flash", "claude-haiku", "gpt-4o", "claude-sonnet");

    @Test
    void portkeyTargetIndexHeaderMapsToTheTargetAlias() {
        assertThat(HttpProxyChatClient.portkeyTargetAlias("config.targets[0]", PORTKEY_TARGETS))
                .isEqualTo("gpt-4o-mini");
        assertThat(HttpProxyChatClient.portkeyTargetAlias("config.targets[2]", PORTKEY_TARGETS))
                .isEqualTo("claude-haiku");
        assertThat(HttpProxyChatClient.portkeyTargetAlias("config.targets[4]", PORTKEY_TARGETS))
                .isEqualTo("claude-sonnet");
    }

    @Test
    void portkeyTargetAliasIsNullWhenTheHeaderCannotBeTrusted() {
        assertThat(HttpProxyChatClient.portkeyTargetAlias(null, PORTKEY_TARGETS)).isNull();
        assertThat(HttpProxyChatClient.portkeyTargetAlias("garbage", PORTKEY_TARGETS)).isNull();
        assertThat(HttpProxyChatClient.portkeyTargetAlias("config.targets[9]", PORTKEY_TARGETS)).isNull();
    }

    @Test
    void promptLengthCountsOnlyTheLatestUserMessage() {
        List<ChatTurn> turns = List.of(
                new ChatTurn("user", "a much longer earlier question"),
                new ChatTurn("assistant", "an answer"),
                new ChatTurn("user", "short"));
        assertThat(HttpProxyChatClient.promptLength(turns)).isEqualTo(5);
    }

    @Test
    void promptLengthCountsCodePointsLikePythonLen() {
        // "😀" is 2 UTF-16 units but 1 code point; the thresholds were measured with Python len().
        assertThat(HttpProxyChatClient.promptLength(List.of(new ChatTurn("user", "ab😀")))).isEqualTo(3);
    }

    @Test
    void promptLengthIsZeroWithoutAUserMessage() {
        assertThat(HttpProxyChatClient.promptLength(List.of())).isZero();
        assertThat(HttpProxyChatClient.promptLength(List.of(new ChatTurn("assistant", "hi")))).isZero();
    }
}
