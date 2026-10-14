# Upstream issue draft — LiteLLM

**Trạng thái:** chưa đăng. Hùng đăng bằng tài khoản GitHub của mình, rồi điền số issue vào đây.
**Repo:** https://github.com/BerriAI/litellm/issues
**Phát hiện:** 2026-10-14, trong lúc thử khả thi Auto Router v2 cho khóa luận (H3).
**Dữ liệu thô:** `experiments/results/litellm-autorouter-smoke-20261014/`

---

## Title

`auto_router/complexity_router` silently drops `max_tokens` and `max_completion_tokens`

## Body

### What happened

When a request is routed through an `auto_router/complexity_router` model, the generation limit
in the request (`max_tokens`, and also `max_completion_tokens`) is not applied. The upstream
call runs to natural completion and the response reports `finish_reason: "stop"`, so a caller
cannot detect that its limit was dropped.

Calling the *same* underlying deployment directly on the *same* proxy instance applies the limit
correctly, so this looks specific to the auto-router code path rather than to the deployment or
the provider.

### Version

Reproduced on both of the newest published images (Docker, self-hosted proxy):

- `ghcr.io/berriai/litellm:v1.105.0`
- `ghcr.io/berriai/litellm:v1.106.0-rc.1`

### Config to reproduce

```yaml
model_list:
  - model_name: gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude-haiku
    litellm_params:
      model: anthropic/claude-haiku-4-5-20251001
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: smart-router
    litellm_params:
      model: auto_router/complexity_router
      complexity_router_config:
        tiers:
          SIMPLE: gpt-4o-mini
          MEDIUM: claude-haiku
          COMPLEX: claude-haiku
          REASONING: claude-haiku
        return_raw_model_name: true
      complexity_router_default_model: gpt-4o-mini
```

### Steps to reproduce

```bash
# A) through the auto router -> limit dropped
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"smart-router","max_tokens":16,
       "messages":[{"role":"user","content":"Write a short, engaging blog post about a recent trip to Hawaii, highlighting cultural experiences and must-see attractions."}]}' \
  | jq '{served: .model, completion_tokens: .usage.completion_tokens, finish_reason: .choices[0].finish_reason}'

# B) same proxy, same deployment, called directly -> limit applied
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","max_tokens":16,
       "messages":[{"role":"user","content":"Write a short, engaging blog post about a recent trip to Hawaii, highlighting cultural experiences and must-see attractions."}]}' \
  | jq '{served: .model, completion_tokens: .usage.completion_tokens, finish_reason: .choices[0].finish_reason}'
```

### Observed

| Request | Served model | `completion_tokens` | `finish_reason` |
|---|---|---|---|
| A) `smart-router`, `max_tokens: 16` in request | `gpt-4o-mini-2024-07-18` | **627** | `stop` |
| B) `smart-router`, `max_completion_tokens: 16` in request | `gpt-4o-mini-2024-07-18` | **524** | `stop` |
| C) `smart-router`, `max_tokens: 16` set per deployment in config | `gpt-4o-mini-2024-07-18` | **520** | `stop` |
| D) `gpt-4o-mini` called directly, `max_tokens: 16` | `gpt-4o-mini` | **16** | `length` |

Same on `v1.106.0-rc.1`: `smart-router` with `max_tokens: 16` returned **615** completion tokens with
`finish_reason: "stop"`, while a direct call to `gpt-4o-mini` on the same instance returned 16 with
`finish_reason: "length"`.

In case C the limit was placed on each tier deployment's `litellm_params` and no limit was sent in
the request, so the router had a configured limit available for the deployment it selected and still
did not apply it.

Across a 9-request run through `smart-router` with `max_tokens: 16`, completion token counts were
141, 616, 568, 1855, 1233, 3400, 101, 80 and 1 — i.e. the limit had no effect in any of them.

All three documented ways of expressing a generation limit are ignored on the auto-router path,
while the same limit works when the deployment is called directly on the same proxy.

### Expected

Requests routed through an auto router should forward generation parameters (`max_tokens`,
`max_completion_tokens`) to the selected deployment, exactly as a direct call to that deployment
does.

### Why it matters

1. **Cost control.** A gateway is the layer operators rely on to bound per-request spend. Silently
   unbounded generation on the auto-router path removes that bound. In our case one request
   produced 3400 completion tokens where 16 were requested.
2. **Not detectable by the caller.** `finish_reason` is `stop`, not `length`, so there is no signal
   that the limit was ignored.
3. **Benchmarking.** We are comparing routing proxies under identical generation limits. The limit
   being enforced on one code path but not another makes cost and latency incomparable.
