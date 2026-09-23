# Bifrost routing — làm được / không làm được (nháp H5-style, chưa chạy thử)

Nguồn: https://docs.getbifrost.ai (mục `features/fallbacks`, `features/governance/routing`,
`features/keys-management`) — đọc 2026-09-23. Chưa chạy thử — VERIFY khi cấu hình thật.

## 1. Gom nhiều model thành 1 "pool" — khác LiteLLM
LiteLLM cho nhiều deployment dùng chung 1 `model_name` để router tự chọn. **Bifrost không có khái niệm
đó.** Weighted routing của Bifrost phân phối request cho **một model cụ thể** (vd. `gpt-4o`) qua nhiều
**provider** cùng hỗ trợ model đó, không tự chọn giữa 5 model khác nhau. Muốn Bifrost "chọn giữa 5 model" thì
phải tự làm ở tầng gọi (runner/backend chọn model trước khi gửi) — bản thân Bifrost không có
"cost-based/latency-based routing giữa các model" như LiteLLM.
→ **Hệ quả cho thí nghiệm:** Bifrost không so sánh được ngang hàng với `cost-based-routing` của LiteLLM ở
cùng một cơ chế. Cấu hình "tương đương" khả dĩ nhất: dùng **fallback chain cố định theo thứ tự** (vd. thử
model rẻ trước, hết retry thì fallback sang model đắt hơn) — đây là dạng gần nhất Bifrost có.

## 2. Weighted routing (theo provider, không theo model)
```json
{
  "provider_configs": [
    { "provider": "openai", "allowed_models": ["gpt-4o", "gpt-4o-mini"], "key_ids": ["*"], "weight": 0.2 },
    { "provider": "azure",  "allowed_models": ["gpt-4o"], "key_ids": ["*"], "weight": 0.8 }
  ]
}
```
- Weight là tỉ lệ lưu lượng, tự chuẩn hóa về tổng 1.0 theo các provider có sẵn cho **cùng 1 model**.
- Không có lựa chọn theo cost hay latency — chỉ theo weight tĩnh do người cấu hình đặt + model có sẵn ở
  provider đó. Bỏ trống `weight` = loại khỏi lựa chọn theo trọng số (vẫn gọi trực tiếp/fallback được).
- Với Conduit: OpenAI/Anthropic/Gemini là 3 provider riêng biệt cho 3 model khác nhau, không phải nhiều
  provider cùng phục vụ 1 model → **weighted routing gần như vô dụng** cho pool 5 model của thí nghiệm này
  (nó được thiết kế cho multi-cloud cùng 1 model, vd. GPT-4o qua cả OpenAI lẫn Azure).

## 3. Fallback / failover
```json
{
  "model": "openai/gpt-4o-mini",
  "messages": [...],
  "fallbacks": ["anthropic/claude-3-5-sonnet-20241022", "bedrock/anthropic.claude-3-sonnet-20240229-v1:0"]
}
```
- Kích hoạt khi provider chính **hết budget retry** của nó (mỗi fallback có budget retry riêng — không
  dùng chung). "First success wins", **theo đúng thứ tự khai báo, không có tiêu chí cost/latency**.
- Trigger: lỗi mạng, 5xx, 429 (rate limit), 401/403 (auth), 402 (billing) → coi là retryable.
  Lỗi 400/404/422 hoặc bị plugin chặn → **không** kích hoạt fallback.
- Retry mỗi provider cấu hình riêng trong `network_config`:
  ```json
  { "providers": { "openai": { "network_config": {
        "max_retries": 3, "retry_backoff_initial": 500, "retry_backoff_max": 5000 } } } }
  ```
- **Không có cooldown/health-check ở bản OSS** (cooldown/predictive load balancing chỉ có ở
  `/enterprise/adaptive-load-balancing` — bản trả phí, ngoài phạm vi thí nghiệm này).

## 4. Bifrost KHÔNG làm được (so với LiteLLM)
- Không có routing "chọn model rẻ nhất/nhanh nhất" giữa nhiều model khác nhau — chỉ có weighted routing
  **giữa các provider cho cùng 1 model**, và fallback **theo thứ tự cố định** giữa các model/provider.
- Không chọn theo độ khó/loại prompt (giống LiteLLM — không proxy nào trong 3 cái làm được việc này, đúng
  với thiết kế đã khóa: không tự train classifier).
- Không có latency-based hay cost-based tự động ở bản OSS.

## 5. Hệ quả cho thiết kế thí nghiệm (đề xuất, cần Khoa phản biện)
1. Vì Bifrost không có "1 alias nhiều model" như LiteLLM, cấu hình công bằng nhất là: khai báo **cùng 1
   chuỗi fallback cố định** cho cả 5 model (vd. thử theo thứ tự tầng rẻ → trung → đắt) — mô phỏng gần nhất
   với ý tưởng "load balancing + automatic failover" mà CLAUDE.md mục 2 gán cho Bifrost.
2. Vì thứ tự fallback là tĩnh, Bifrost gần như chắc chắn có **consistency rate cao nhất** trong 3 proxy (ít
   ngẫu nhiên nhất) — cần lưu ý khi diễn giải quy tắc quyết định bước 4, tránh hiểu nhầm "ổn định hơn" nghĩa
   là "định tuyến thông minh hơn".
3. Cùng đặt `max_retries`/backoff giống LiteLLM (`num_retries`/`timeout`) để công bằng khi đo latency/cost.

## Câu hỏi mở
- Chuỗi fallback cố định theo thứ tự tầng chi phí (rẻ → trung → đắt), hay theo thứ tự khác (vd. random mỗi
  proxy) để phản ánh "load balancing" đúng nghĩa hơn "failover"?
- Có cần bật `weight` giữa 2 model tầng rẻ (GPT-4o-mini/Gemini Flash) để mô phỏng load balancing thật không,
  hay chỉ test failover (đơn giản hơn, sát với những gì Bifrost quảng cáo là thế mạnh)?
