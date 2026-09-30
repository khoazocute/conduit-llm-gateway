package com.conduit.backendgateway.adapter;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.File;
import java.io.IOException;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
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

    // LiteLLM's grouped model_name (e.g. "conduit-pool", H1 - proxy-configs/litellm/config.yaml)
    // echoes the GROUP name back in the JSON body's "model" field, not the deployment actually
    // chosen by routing_strategy - the real one is only in this response header, and it already
    // matches our alias (model_info.id in config.yaml was set to equal it), no aliasOf() needed.
    private static final String LITELLM_MODEL_ID_HEADER = "x-litellm-model-id";

    // Portkey OSS reads its Config object from THIS request header, not from an Authorization
    // bearer token (H2, docs/portkey-routing-notes.md) - and, unlike LiteLLM's os.environ/VAR, it
    // does NOT interpolate "$VAR" placeholders itself, so the caller must substitute real key
    // values before sending it (also found in H2).
    private static final String PORTKEY_CONFIG_HEADER = "x-portkey-config";

    private final WebClient webClient;
    private final ChatProxyProperties properties;

    public HttpProxyChatClient(ChatProxyProperties properties) {
        this.properties = properties;
        WebClient.Builder builder = WebClient.builder()
                .baseUrl(properties.activeBaseUrl())
                .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer " + properties.activeApiKey());
        if ("portkey".equals(properties.getActiveProxy())) {
            builder.defaultHeader(PORTKEY_CONFIG_HEADER, loadPortkeyConfigHeader(properties.getPortkeyConfigPath()));
        }
        this.webClient = builder.build();
    }

    private static String loadPortkeyConfigHeader(String configPath) {
        ObjectMapper mapper = new ObjectMapper();
        JsonNode root;
        try {
            root = mapper.readTree(new File(configPath));
        } catch (IOException e) {
            throw new IllegalStateException(
                    "Cannot read Portkey config at " + configPath + " (app.chat.portkey-config-path)", e);
        }
        substituteEnvVars(root);
        try {
            return mapper.writeValueAsString(root);
        } catch (IOException e) {
            throw new IllegalStateException("Cannot serialize Portkey config", e);
        }
    }

    // Walks the whole config tree replacing any string value like "$OPENAI_API_KEY" with the
    // real environment variable's value - generic (not hardcoded to "targets"/"api_key") so it
    // still works if proxy-configs/portkey/config.json's shape changes later.
    private static void substituteEnvVars(JsonNode node) {
        if (node.isObject()) {
            ObjectNode obj = (ObjectNode) node;
            obj.fieldNames().forEachRemaining(field -> {
                JsonNode child = obj.get(field);
                if (child.isTextual() && child.asText().startsWith("$")) {
                    obj.put(field, System.getenv().getOrDefault(child.asText().substring(1), ""));
                } else {
                    substituteEnvVars(child);
                }
            });
        } else if (node.isArray()) {
            node.forEach(HttpProxyChatClient::substituteEnvVars);
        }
    }

    @Override
    public ChatCompletionResult complete(String model, List<ChatTurn> messages) {
        Map<String, Object> body = Map.of(
                "model", properties.upstreamModel(model),
                "messages", messages.stream()
                        .map(t -> Map.of("role", t.role(), "content", t.content()))
                        .toList());

        long start = System.currentTimeMillis();
        ResponseEntity<JsonNode> entity;
        try {
            entity = webClient.post()
                    .uri("/chat/completions")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toEntity(JsonNode.class)
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

        JsonNode response = entity == null ? null : entity.getBody();
        if (response == null) {
            throw new ProxyChatException("Empty response from proxy", null);
        }

        JsonNode message = response.path("choices").path(0).path("message");
        String content = message.path("content").isMissingNode() ? null : message.path("content").asText();
        String returnedModel = resolveReturnedModel(response, entity.getHeaders(), model);
        JsonNode usage = response.path("usage");
        Integer tokenInput = usage.has("prompt_tokens") ? usage.get("prompt_tokens").asInt() : null;
        Integer tokenOutput = usage.has("completion_tokens") ? usage.get("completion_tokens").asInt() : null;

        return new ChatCompletionResult(content, returnedModel, tokenInput, tokenOutput, latencyMs);
    }

    // Bifrost's top-level "model" is the provider's resolved id (e.g. gemini-3.8-flash), which
    // matches nothing in model_pricing; routing_info names the deployment that actually answered,
    // including after a fallback. LiteLLM's grouped alias (H1) needs the header instead - see
    // LITELLM_MODEL_ID_HEADER above.
    private String resolveReturnedModel(JsonNode response, HttpHeaders headers, String requestedAlias) {
        String litellmModelId = headers.getFirst(LITELLM_MODEL_ID_HEADER);
        if (litellmModelId != null && !litellmModelId.isBlank()) {
            return litellmModelId;
        }
        JsonNode routing = response.path("extra_fields").path("routing_info");
        if (routing.hasNonNull("provider") && routing.hasNonNull("model")) {
            return properties.aliasOf(routing.get("provider").asText() + "/" + routing.get("model").asText());
        }
        if ("portkey".equals(properties.getActiveProxy())) {
            // Portkey's conditional routing (H2) is a static 1:1 alias->target mapping - it never
            // dynamically picks a different model the way LiteLLM/Bifrost can, so the requested
            // alias IS the model actually used. Its top-level "model" is the provider's dated
            // snapshot id (e.g. "gpt-4o-mini-2024-07-18"), which matches nothing in model_pricing.
            return requestedAlias;
        }
        return response.hasNonNull("model") ? properties.aliasOf(response.get("model").asText()) : requestedAlias;
    }
}
