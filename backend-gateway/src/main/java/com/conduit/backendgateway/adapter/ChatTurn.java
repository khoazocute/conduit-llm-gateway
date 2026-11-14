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

    /**
     * TASK-57b: chen khoi "ngu canh tham khao" (RAG) thanh mot luot "user" RIENG, ngay TRUOC tin
     * nhan user cuoi. Khong dat vao "system" (CLAUDE.md muc 7: khong phai chi thi he thong), va cau
     * hoi that van la luot cuoi nen promptLength() (dinh tuyen Portkey) khong doi. Khong luu DB.
     * null/rong thi tra NGUYEN danh sach cu.
     */
    public static List<ChatTurn> withReferenceContext(String referenceContext, List<ChatTurn> turns) {
        if (referenceContext == null || referenceContext.isBlank()) {
            return turns;
        }
        int lastUser = -1;
        for (int i = turns.size() - 1; i >= 0; i--) {
            if ("user".equals(turns.get(i).role())) {
                lastUser = i;
                break;
            }
        }
        if (lastUser < 0) {
            return turns;
        }
        List<ChatTurn> withContext = new ArrayList<>(turns.size() + 1);
        withContext.addAll(turns.subList(0, lastUser));
        withContext.add(new ChatTurn("user", referenceContext));
        withContext.addAll(turns.subList(lastUser, turns.size()));
        return List.copyOf(withContext);
    }
}
