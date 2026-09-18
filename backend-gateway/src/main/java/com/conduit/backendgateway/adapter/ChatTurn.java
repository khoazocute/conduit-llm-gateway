package com.conduit.backendgateway.adapter;

// role = "user" | "assistant", matching MessageRole/OpenAI-compatible chat format.
public record ChatTurn(String role, String content) {
}
