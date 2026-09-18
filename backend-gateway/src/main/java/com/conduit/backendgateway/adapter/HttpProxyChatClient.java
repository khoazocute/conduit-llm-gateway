package com.conduit.backendgateway.adapter;

import com.fasterxml.jackson.databind.JsonNode;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

@Component
public class HttpProxyChatClient implements ProxyChatClient {

    // Proxy/upstream provider can hang far longer than a user will wait (seen
    // with Gemini 503 "high demand" retries) - without an explicit timeout,
    // WebClient.block() waits indefinitely and the SSE response never
    // resolves client-side ("Assistant is typing..." forever, no error).
    private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(45);

    private final WebClient webClient;

    public HttpProxyChatClient(ChatProxyProperties properties) {
        this.webClient = WebClient.builder()
                .baseUrl(properties.activeBaseUrl())
                .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer " + properties.activeApiKey())
                .build();
    }

    @Override
    public ChatCompletionResult complete(String model, List<ChatTurn> messages) {
        Map<String, Object> body = Map.of(
                "model", model,
                "messages", messages.stream()
                        .map(t -> Map.of("role", t.role(), "content", t.content()))
                        .toList());

        long start = System.currentTimeMillis();
        JsonNode response;
        try {
            response = webClient.post()
                    .uri("/chat/completions")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(JsonNode.class)
                    .block(REQUEST_TIMEOUT);
        } catch (WebClientResponseException e) {
            throw new ProxyChatException(
                    "Proxy returned " + e.getStatusCode() + ": " + e.getResponseBodyAsString(), e);
        } catch (Exception e) {
            throw new ProxyChatException(
                    "Failed to call proxy (timed out after " + REQUEST_TIMEOUT.getSeconds() + "s or network error): "
                            + e.getMessage(),
                    e);
        }
        int latencyMs = (int) (System.currentTimeMillis() - start);

        if (response == null) {
            throw new ProxyChatException("Empty response from proxy", null);
        }

        JsonNode message = response.path("choices").path(0).path("message");
        String content = message.path("content").isMissingNode() ? null : message.path("content").asText();
        String returnedModel = response.path("model").isMissingNode() ? model : response.path("model").asText();
        JsonNode usage = response.path("usage");
        Integer tokenInput = usage.has("prompt_tokens") ? usage.get("prompt_tokens").asInt() : null;
        Integer tokenOutput = usage.has("completion_tokens") ? usage.get("completion_tokens").asInt() : null;

        return new ChatCompletionResult(content, returnedModel, tokenInput, tokenOutput, latencyMs);
    }
}
