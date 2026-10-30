package com.conduit.backendgateway.adapter;

import java.util.ArrayList;
import java.util.List;

// role = "system" | "user" | "assistant", OpenAI-compatible chat format. "system" chi xuat hien o
// DAU danh sach, mang instructions cua agent (D8, TASK-66) - xem ChatTurn.withSystemPrompt.
public record ChatTurn(String role, String content) {

    public static final String SYSTEM = "system";

    /**
     * TASK-66: agent co instructions khac rong thi them 1 luot "system" o DAU danh sach. Rong/null
     * thi tra NGUYEN danh sach cu - request y het luc do thuc nghiem 720 luot (khong lam lech so lieu).
     */
    public static List<ChatTurn> withSystemPrompt(String instructions, List<ChatTurn> turns) {
        if (instructions == null || instructions.isBlank()) {
            return turns;
        }
        List<ChatTurn> withSystem = new ArrayList<>(turns.size() + 1);
        withSystem.add(new ChatTurn(SYSTEM, instructions));
        withSystem.addAll(turns);
        return List.copyOf(withSystem);
    }
}
