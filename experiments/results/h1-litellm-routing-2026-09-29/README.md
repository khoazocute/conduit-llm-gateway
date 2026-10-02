# H1 — Bằng chứng verify LiteLLM cost-based-routing (2026-09-29)

Gọi trực tiếp `POST /v1/chat/completions` với `model: "conduit-pool"` (5 deployment gom chung
alias, `routing_strategy: cost-based-routing`, xem `proxy-configs/litellm/config.yaml`).

## Lần 1 — trước khi khai giá tường minh (5 lượt)

Model thật đọc từ header `x-litellm-model-id` (JSON body chỉ trả `"model": "conduit-pool"`).

| Lượt | Model chọn | Cost (USD) |
|---|---|---|
| 1 | gpt-4o-mini | 0.0000027 |
| 2 | gpt-4o-mini | 0.0000027 |
| 3 | gpt-4o-mini | 0.0000027 |
| 4 | **gemini-flash** | 0.0000248 |
| 5 | (lỗi 503, Gemini quá tải, hết retry — cùng nguyên nhân đã gặp trước đây) | — |

**Vấn đề:** lượt 4 chọn `gemini-flash` dù đắt hơn `gpt-4o-mini` gần 10 lần. Nguyên nhân: chưa khai
`input_cost_per_token`/`output_cost_per_token`, LiteLLM dùng bảng giá nội bộ của nó — không có giá
đúng cho `gemini/gemini-flash-latest` (dùng fallback không chuẩn theo docs: "not in cost map -> $1"),
khiến quyết định "rẻ nhất" không đáng tin.

## Lần 2 — sau khi khai giá tường minh (5 lượt, khớp `docs/model-pricing-sources.md`)

| Lượt | Model chọn | Cost (USD) |
|---|---|---|
| 1 | gpt-4o-mini | 0.0000027 |
| 2 | gpt-4o-mini | 0.0000027 |
| 3 | gpt-4o-mini | 0.0000027 |
| 4 | gpt-4o-mini | 0.0000027 |
| 5 | gpt-4o-mini | 0.0000027 |

**Kết luận:** 10/10 lượt (2 lần chạy) chọn đúng `gpt-4o-mini` sau khi sửa. Header
`x-litellm-max-retries: 2`/`x-litellm-attempted-retries` xác nhận D7 (`num_retries=2`) đã áp dụng.
Ghi chú đầy đủ: `docs/litellm-routing-notes.md`.
