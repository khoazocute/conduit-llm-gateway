# Báo cáo giá `model_pricing` (K2)

**Ngày lấy giá:** 2026-09-26 (tra lại toàn bộ trên trang giá chính thức, thay bản 2026-09-23).
Giá đổi thường xuyên — kiểm tra lại trước khi khoá thực nghiệm Tuần 9-10.

**Trạng thái:** DB có đúng 10 dòng (5 model × `token_input`/`token_output`), khớp model thật đang
chạy. Cả 5 model đã trả lời thật qua Bifrost ngày 2026-09-26 (xem `docs/bifrost-routing-notes.md`
mục 5).

---

## 1. Bảng giá — nguồn và giá trị đã nhập

| Alias (`model_pricing.model`) | Model thật / provider | Input (USD/MTok → USD/token) | Output (USD/MTok → USD/token) | Nguồn |
|---|---|---|---|---|
| `gpt-4o-mini` | gpt-4o-mini / openai | $0.15 → 0.00000015 | $0.60 → 0.0000006 | [OpenAI pricing](https://developers.openai.com/api/docs/pricing) |
| `gpt-4o` | gpt-4o / openai | $2.50 → 0.0000025 | $10.00 → 0.00001 | [OpenAI pricing](https://developers.openai.com/api/docs/pricing) |
| `claude-haiku` | claude-haiku-4-5-20251001 / anthropic | $1 → 0.000001 | $5 → 0.000005 | [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing) — dòng "Claude Haiku 4.5" |
| `claude-sonnet` | claude-sonnet-5 / anthropic | $2 → 0.000002 | $10 → 0.00001 | [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing) — dòng "Claude Sonnet 5" |
| `gemini-flash` | gemini-flash-latest → **gemini-3.8-flash** / google | $0.75 → 0.00000075 | $3.75 → 0.00000375 | [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing) — dòng "Gemini 3.8 Flash" |

`credit_markup_multiplier` = 1.5 cho cả 10 dòng (mặc định hệ thống, CLAUDE.md mục 4).

**Bắt buộc dùng alias, không dùng tên model đầy đủ:** `ChatService` tra giá bằng đúng chuỗi
`model_used` mà LiteLLM trả về, và LiteLLM trả về **alias** khai báo trong
`proxy-configs/litellm/config.yaml` (VD `gemini-flash`), không phải tên model thật. Nhập tên đầy
đủ → giá không khớp → rơi vào fallback `cost_upstream = 0`.

---

## 2. ⚠️ Giá này KHÔNG phải giá tính tiền user — chỉ để ghi log nghiên cứu

`price_usd_per_unit` **không ảnh hưởng** số credit trừ ví. Theo `ChatService.java:139-150`:

```java
costUpstream += inputPrice  × tokenInput       // price_usd_per_unit → usage_logs.cost_upstream,
                                               // routing_decisions.predicted_cost
credit       += ceil(tokenInput × inputMarkup)  // credit_markup_multiplier → credit trừ ví,
                                               // KHÔNG nhân với giá USD
```

Vì `credit_markup_multiplier` bằng nhau (1.5) ở cả 10 dòng, 100 token qua `gpt-4o` và qua
`gpt-4o-mini` trừ ví **y hệt nhau**, dù giá USD chênh ~17 lần. Bảng giá ở mục 1 chỉ quyết định
`cost_upstream` — dữ liệu dùng để so proxy nào rẻ hơn ở Phase D/E.

**Khi Hùng review:** đang kiểm tra độ chính xác của dữ liệu nghiên cứu, không phải "user trả đúng
tiền chưa".

---

## 3. Lưu ý riêng từng model

**`gemini-flash` — giá ưu đãi có hạn, và token "suy nghĩ" bị tính tiền**
- Model thật xác định từ response (`"model":"gemini-3.8-flash"`), không phải giả định từ tên alias.
  Bản 2026-09-23 nhập nhầm theo Gemini 2.5 Flash ($0.30/$2.50).
- $0.75/$3.75 là **giá ưu đãi tới 31/12/2026**; từ 01/01/2027 tăng gấp đôi lên **$1.50/$7.50**.
  Phase E (Tuần 9-10) nằm trong thời hạn ưu đãi — nếu chạy lại sau 01/01/2027 phải sửa 2 dòng này.
- Giá output **đã gồm thinking tokens**. Thực tế đo được: câu hỏi "1+1 bằng mấy?" trả lời "2"
  nhưng tốn 166 completion token, trong đó 165 là reasoning → chi phí thật của Gemini cao hơn nhiều
  so với độ dài câu trả lời. Cần ghi vào phần phân tích chi phí của báo cáo.
- D5 (giá Gemini khi dùng key miễn phí): dùng giá niêm yết ở trên, đúng quyết định tạm chốt 2026-09-23.

**`claude-haiku`, `claude-sonnet` — pool đã đổi model**
- Hùng đã đổi `claude-3-5-haiku/sonnet-20241022` (Anthropic đã retire) sang `claude-haiku-4-5-20251001`
  / `claude-sonnet-5` (commit H3, 2026-09-24). Giá ở mục 1 đã theo model mới.
- `claude-sonnet-5`: $2/$10 là **giá chuẩn chính thức** (ban đầu công bố là giá ưu đãi tới
  31/08/2026, nhưng Anthropic đã huỷ đợt tăng lên $3/$15).
- Claude 4.7 trở lên dùng tokenizer mới (~30% nhiều token hơn cho cùng văn bản); `claude-sonnet-5`
  thuộc nhóm này, `claude-haiku-4-5` thì không — ảnh hưởng khi so số token giữa 2 model.

**`gpt-4o-mini`, `gpt-4o`** — không đổi so với bản 2026-09-23.

---

## 4. Lịch sử sửa

| Ngày | Thay đổi |
|---|---|
| 2026-09-23 | Nhập 10 dòng lần đầu (theo config cũ: claude-3-5-*, Gemini 2.5 Flash); dọn 8 dòng rác còn đúng 10 |
| 2026-09-26 | Tra lại toàn bộ; sửa 6 dòng `claude-haiku`, `claude-sonnet`, `gemini-flash` theo model thật (sửa trực tiếp, không thêm dòng — thực nghiệm chưa chạy nên không cần giữ lịch sử giá cũ) |
