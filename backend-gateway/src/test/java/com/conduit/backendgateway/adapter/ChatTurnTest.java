package com.conduit.backendgateway.adapter;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import org.junit.jupiter.api.Test;

/** TASK-66: instructions cua agent thanh luot system o dau danh sach. */
class ChatTurnTest {

    private static final List<ChatTurn> HISTORY = List.of(
            new ChatTurn("user", "first question"),
            new ChatTurn("assistant", "first answer"),
            new ChatTurn("user", "short"));

    @Test
    void noInstructionsLeavesTheRequestExactlyAsMeasured() {
        assertThat(ChatTurn.withSystemPrompt(null, HISTORY)).isSameAs(HISTORY);
        assertThat(ChatTurn.withSystemPrompt("", HISTORY)).isSameAs(HISTORY);
        assertThat(ChatTurn.withSystemPrompt("   ", HISTORY)).isSameAs(HISTORY);
    }

    @Test
    void instructionsBecomeTheFirstTurnAsSystem() {
        List<ChatTurn> turns = ChatTurn.withSystemPrompt("You are a terse tutor.", HISTORY);

        assertThat(turns).hasSize(4);
        assertThat(turns.get(0)).isEqualTo(new ChatTurn("system", "You are a terse tutor."));
        assertThat(turns.subList(1, 4)).isEqualTo(HISTORY);
    }

    @Test
    void systemTurnDoesNotChangePortkeyPromptLength() {
        // Portkey dinh tuyen theo do dai tin nhan user CUOI (Design Y); instructions dai cung khong
        // duoc day cau hoi sang tier dat.
        String longInstructions = "x".repeat(5_000);
        assertThat(HttpProxyChatClient.promptLength(ChatTurn.withSystemPrompt(longInstructions, HISTORY)))
                .isEqualTo(HttpProxyChatClient.promptLength(HISTORY))
                .isEqualTo(5);
    }
}
