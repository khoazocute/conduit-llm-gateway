# Nguồn giá `model_pricing` (K2)

**Ngày lấy giá:** 2026-09-23. Giá đổi thường xuyên (đặc biệt Anthropic/Google) — nếu chạy thực
nghiệm Tuần 9-10 cách xa ngày này, **kiểm tra lại giá trước khi khoá thực nghiệm**.

## ⚠️ Phát hiện quan trọng — dùng alias, KHÔNG dùng tên model đầy đủ

Test thật (`e2e_workflow_test.sh`) cho response `model_used: "gemini-flash"` — LiteLLM echo lại
đúng **alias `model_name`** khai báo trong `proxy-configs/litellm/config.yaml`, không phải tên
model thật của provider (VD không phải `gemini-flash-latest` hay `claude-3-5-haiku-20241022`).
`ChatService` tra `model_pricing` bằng đúng chuỗi này (`unitPrice`/`unitMarkup` so khớp
`p.getModel().equals(model)`) — nên **cột `model` trong `model_pricing` phải nhập đúng alias**,
không phải tên đầy đủ, nếu không giá sẽ không khớp (rơi vào fallback `cost_upstream=0`, xem
`log.md` mục về giới hạn đã biết trước đây).

| Alias trong `config.yaml` | Model thật đứng sau (để tra giá) | Provider (enum hệ thống) |
|---|---|---|
| `gpt-4o-mini` | gpt-4o-mini | openai |
| `gpt-4o` | gpt-4o | openai |
| `claude-haiku` | claude-3-5-haiku-20241022 | anthropic |
| `claude-sonnet` | claude-3-5-sonnet-20241022 | anthropic |
| `gemini-flash` | gemini-flash-latest (Google tự trỏ bản mới nhất) | google |

## Bảng giá (tra ngày 2026-09-23, đơn vị gốc: USD / 1 triệu token)

| Alias | Input ($/MTok) | Output ($/MTok) | Nguồn |
|---|---|---|---|
| `gpt-4o-mini` | $0.15 | $0.60 | [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) |
| `gpt-4o` | $2.50 | $10.00 | [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) |
| `claude-haiku` | $0.80 | $4.00 | [Claude Platform Docs — Pricing](https://platform.claude.com/docs/en/about-claude/pricing) — dòng "Claude Haiku 3.5" |
| `claude-sonnet` | $3.00 | $15.00 | ⚠️ **KHÔNG còn trên trang giá hiện tại** — model đã bị gỡ khỏi bảng (không như Haiku 3.5 vẫn còn ghi "retired, except Bedrock/GCP"). Giá tham khảo từ dữ liệu lịch sử lúc ra mắt ([Anthropic: Introducing Claude 3.5 Sonnet](https://www.anthropic.com/news/claude-3-5-sonnet)) — **cần Hùng xác nhận lại, có thể model này không còn gọi được qua API first-party nữa** |
| `gemini-flash` | $0.30 | $2.50 | [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) — dòng "Gemini 2.5 Flash" (gần nhất với "gemini-flash-latest" hiện dùng; Google có 3 tier Flash khác nhau giá chênh lệch lớn — xem ghi chú D5 bên dưới) |

## Đổi sang giá 1 token (nhập vào form `/admin/model-pricing`)

| Alias | unit_type | price_usd_per_unit (giá 1 token) |
|---|---|---|
| `gpt-4o-mini` | token_input | 0.00000015 |
| `gpt-4o-mini` | token_output | 0.0000006 |
| `gpt-4o` | token_input | 0.0000025 |
| `gpt-4o` | token_output | 0.00001 |
| `claude-haiku` | token_input | 0.0000008 |
| `claude-haiku` | token_output | 0.000004 |
| `claude-sonnet` | token_input | 0.000003 |
| `claude-sonnet` | token_output | 0.000015 |
| `gemini-flash` | token_input | 0.0000003 |
| `gemini-flash` | token_output | 0.0000025 |

`credit_markup_multiplier` = 1.5 cho cả 10 dòng (mặc định hệ thống, CLAUDE.md mục 4 — chưa có
quyết định D nào yêu cầu đổi khác cho model cụ thể).

## ⚠️ Cần D5 xác nhận (không đọc được `roadmap.md`)

Google hiện có **3 tier "Flash" giá chênh lệch tới 5 lần**:
- Gemini 2.5 Flash: $0.30 / $2.50 (đã dùng ở trên)
- Gemini 3.5 Flash: $1.50 / $9.00
- Gemini 3.8 Flash: $0.75 / $3.75 (giá ưu đãi tới 31/12/2026, sau đó $1.50/$7.50)

Đã chọn **2.5 Flash** vì gần nhất với dòng "Gemini Flash" gốc trong CLAUDE.md (tầng rẻ) và alias
`gemini-flash-latest` hiện dùng nhiều khả năng trỏ tới đây. **Nếu D5 chốt khác, chỉ cần sửa lại
2 dòng `gemini-flash` trong bảng trên, không ảnh hưởng 8 dòng còn lại.**

## ⚠️ Rủi ro cần báo Hùng: pool 5 model có thể đã lỗi thời

`claude-3-5-sonnet-20241022` (dùng trong `proxy-configs/litellm/config.yaml` và
`proxy-configs/bifrost/config.json`) **không còn xuất hiện trong bảng giá chính thức hiện tại
của Anthropic** — khác với Haiku 3.5 vẫn còn (đánh dấu "retired, except Bedrock/GCP"). Cần test
thật xem model này còn gọi được qua API first-party không trước khi chạy thực nghiệm Tuần 9-10 —
nếu không gọi được, phải đổi pool sang `claude-sonnet-4-5` hoặc bản mới hơn còn hỗ trợ.
