# Bifrost routing — làm được / không làm được (K4 + H5)

**Nguồn và phương pháp** (bản gộp 2026-09-26):
- **Khoa (K4):** dò trực tiếp API + UI của container `conduit-bifrost` (`maximhq/bifrost:latest`) đang chạy
  thật (`localhost:8080`, remap sang `18080` trên máy Khoa — xem `docker-compose.override.yml`). Mọi kết
  luận đánh dấu ✅ **test sống** đều có request thật (mục 6). Lần test: 2026-09-23 và 2026-09-26.
- **Hùng (H5):** đọc https://docs.getbifrost.ai (`features/fallbacks`, `features/governance/routing`,
  `features/keys-management`), 2026-09-23. Ý nào chỉ có từ tài liệu được ghi 📄 **theo tài liệu**.

---

## 1. Cách nạp cấu hình

- **OpenAI/Anthropic: tự động.** Khởi động lên là Bifrost tự dò biến `.env` đặt tên đúng chuẩn
  `<PROVIDER>_API_KEY` và tạo key `*_auto_detected` với `weight: 1`, `models: ["*"]`. ✅ test sống
- **Gemini: KHÔNG tự nhận** `GEMINI_API_KEY` — phải khai báo thủ công, 2 bước qua API (tương đương
  UI `Models > Model Providers > Add New Provider`). ✅ test sống
  ```bash
  # 1. Tạo provider
  curl -X POST http://localhost:18080/api/providers -H "Content-Type: application/json" \
    -d '{"provider":"gemini"}'
  # 2. Thêm key — PHẢI qua endpoint /keys riêng, và models phải là ["*"]
  #    (models: [] = không cho model nào, request sẽ lỗi "no keys found")
  curl -X POST http://localhost:18080/api/providers/gemini/keys -H "Content-Type: application/json" \
    -d '{"name":"gemini-key-1","value":"env.GEMINI_API_KEY","models":["*"],"weight":1.0}'
  ```
  `"value":"env.GEMINI_API_KEY"` = tham chiếu biến môi trường, Bifrost không lưu giá trị key thật.
- Cấu hình nằm trong SQLite của volume `bifrost/data`, không nằm trong `proxy-configs/bifrost/config.json`
  (file đó chỉ là tài liệu tham khảo). **Máy khác (Hùng) phải chạy lại 2 lệnh trên.**
- Dashboard `http://localhost:18080` mặc định **không yêu cầu đăng nhập**.

---

## 2. "Chọn model rẻ nhất đủ tốt" — chỉ diễn đạt được MỘT PHẦN ở bản OSS

**Bifrost không có khái niệm "1 alias gom nhiều model"** như LiteLLM (nhiều deployment chung 1
`model_name` để router tự chọn). Muốn "chọn giữa 5 model" thì tầng gọi (backend/runner) phải tự chọn
model trước khi gửi. ✅ test sống: app gửi alias `gemini-flash` → Bifrost trả 404; backend phải đổi sang
`gemini/gemini-flash-latest` (mục 7).

| Cơ chế | Trạng thái | Diễn đạt được gì |
|---|---|---|
| **Weighted routing** | ✅ Có | Chia tải theo `weight` giữa nhiều provider/key phục vụ **cùng 1 model** — không chọn giữa 5 model khác nhau |
| **Routing Rules (CEL)** | ✅ Có (thấy trên UI), chưa cấu hình | Luật **tĩnh** if/else theo model/provider/budget — không tự so giá real-time |
| **Complexity Router** (Beta) | ✅ Có (thấy trên UI), chưa cấu hình, **chưa test chạy** | Phân loại độ khó câu hỏi bằng embedding (tier Simple/Medium/Complex) rồi định tuyến theo tier — xem mục 5, câu hỏi mở 3 |
| **Adaptive Routing** (cost/latency tự động) | 🔒 Enterprise | Không dùng được ở bản OSS |

**Weighted routing — chi tiết** 📄 theo tài liệu (chưa test chia tải thật):
```json
{
  "provider_configs": [
    { "provider": "openai", "allowed_models": ["gpt-4o", "gpt-4o-mini"], "key_ids": ["*"], "weight": 0.2 },
    { "provider": "azure",  "allowed_models": ["gpt-4o"], "key_ids": ["*"], "weight": 0.8 }
  ]
}
```
- Weight là tỉ lệ lưu lượng, tự chuẩn hoá về tổng 1.0 theo các provider có sẵn cho **cùng 1 model**.
  Bỏ trống `weight` = loại khỏi lựa chọn theo trọng số (vẫn gọi trực tiếp/fallback được).
- Với Conduit: OpenAI/Anthropic/Gemini là 3 provider riêng cho các model khác nhau, không phải nhiều
  provider cùng phục vụ 1 model → **weighted routing gần như vô dụng cho pool 5 model** (nó được thiết kế
  cho multi-cloud cùng 1 model, VD GPT-4o qua cả OpenAI lẫn Azure).

**Về phạm vi (CLAUDE.md mục 1):** Complexity Router nghe giống "hướng V2 đã bị bác bỏ" (tự phân loại câu
hỏi), nhưng là tính năng **có sẵn** của proxy, không phải tự train classifier — dùng nó vẫn nằm trong
phạm vi "đánh giá 3 proxy có sẵn". Có dùng hay không là quyết định D2.

---

## 3. Failover — CÓ ở bản OSS, nhưng chỉ dạng tĩnh

| Cơ chế | Trạng thái | Cách hoạt động |
|---|---|---|
| **`fallbacks` trong request** | ✅ **Chạy được — test sống** | Khai báo danh sách model dự phòng ngay trong request. Provider chính lỗi → thử lần lượt **theo đúng thứ tự khai báo**, "first success wins", không theo cost/latency |
| **Circuit Breaker** / cooldown / health-check | 🔒 Enterprise | Tự dò provider hỏng rồi chuyển hướng trước khi request lỗi (`/enterprise/adaptive-load-balancing`) |

Cơ chế `fallbacks` do Hùng tìm ra từ tài liệu (H5), Khoa test xác nhận ngày 2026-09-26:
primary `anthropic/claude-haiku-4-5-20251001` (key trả 401) + `"fallbacks": ["gemini/gemini-flash-latest"]`
→ trả lời thành công, `routing_info`:
```json
{"provider":"gemini","model":"gemini-flash-latest","is_fallback":true,
 "primary_provider":"anthropic","primary_model":"claude-haiku-4-5-20251001"}
```

**Điều kiện kích hoạt:**

| Loại lỗi của provider chính | Theo tài liệu 📄 | Test sống ✅ |
|---|---|---|
| 401 (auth) | Kích hoạt | **Kích hoạt** |
| Lỗi mạng, 5xx, 429, 403, 402 | Kích hoạt | Chưa test |
| 400/404/422, bị plugin chặn | Không kích hoạt | Chưa test |
| Provider chưa cấu hình (`failed to get config for provider`) | — | **Không kích hoạt** |

- `fallbacks` phải là mảng string `"provider/model"`; dạng object → `400 Invalid request payload`. ✅
- Mỗi fallback có budget retry riêng; fallback kích hoạt khi provider chính **hết** retry. 📄
- Retry cấu hình theo từng provider trong `network_config`. ✅ có thật — **mặc định hiện là
  `max_retries: 0` cho mọi provider** (xem qua `GET /api/providers`):
  ```json
  { "providers": { "openai": { "network_config": {
        "max_retries": 3, "retry_backoff_initial": 500, "retry_backoff_max": 5000 } } } }
  ```

**Đính chính:** bản K4 trước (2026-09-26, sáng) kết luận "failover không có ở bản OSS" — **sai**. Lần
test đó chọn đích fallback là `openai`, nhưng key OpenAI trên máy Khoa lúc đó cũng 401, nên cả 2 cùng lỗi
và không thấy được fallback. Test lại với đích chạy được thì fallback hoạt động — đúng như H5 mô tả.

---

## 4. So sánh nhanh (input cho `routing-policy.md` / D2)

| | LiteLLM (ghi chú H4) | Bifrost |
|---|---|---|
| Failover khi lỗi | Có | **Có — chuỗi tĩnh theo thứ tự** (`fallbacks`); tự dò lỗi (Circuit Breaker) = Enterprise |
| Chọn model theo cost/latency tự động | Có (`routing_strategy`) | **Không** — Adaptive Routing = Enterprise |
| Gom nhiều model thành 1 alias để proxy tự chọn | Có | **Không** — weight chỉ giữa các provider của cùng 1 model |
| Chọn model theo độ khó câu hỏi | Không | **Có trên UI** (Complexity Router, Beta) — chưa test |
| Luật tĩnh (budget/attribute) | Có | Có (Routing Rules, CEL) |
| Tự nhận key từ `.env` | — | Có với openai/anthropic, **không** với gemini |

**Điểm chính cho báo cáo:** Bifrost OSS diễn đạt được "failover" nhưng **không** diễn đạt được "chọn
model rẻ nhất" tự động — giới hạn cần ghi rõ trong `routing-policy.md`.

---

## 5. Hệ quả cho thiết kế thí nghiệm (đề xuất của Hùng, Khoa đồng ý)

1. Vì Bifrost không có "1 alias nhiều model", cấu hình công bằng nhất là khai báo **cùng 1 chuỗi fallback
   cố định** cho cả 5 model (VD tầng rẻ → trung → đắt) — gần nhất với "load balancing + automatic
   failover" mà CLAUDE.md mục 2 gán cho Bifrost.
2. Vì thứ tự fallback là tĩnh, Bifrost gần như chắc chắn có **consistency rate cao nhất** trong 3 proxy —
   cần lưu ý khi áp bước 4 của quy tắc quyết định: "ổn định hơn" không có nghĩa là "định tuyến thông minh
   hơn".
3. Đặt `max_retries`/backoff giống LiteLLM (`num_retries`/`timeout`) để công bằng khi đo latency/cost
   (chốt ở D7). Lưu ý mặc định của Bifrost là `max_retries: 0`.

### Câu hỏi mở (cho D2)
1. Chuỗi fallback theo thứ tự tầng chi phí (rẻ → trung → đắt), hay thứ tự khác (VD random mỗi proxy) để
   phản ánh "load balancing" đúng nghĩa hơn "failover"?
2. Có bật `weight` giữa 2 model tầng rẻ (GPT-4o-mini / Gemini Flash) để mô phỏng load balancing không, hay
   chỉ test failover (đơn giản hơn, sát điểm mạnh Bifrost quảng cáo)?
3. **Có dùng Complexity Router không?** Nếu có, Bifrost có thêm 1 cơ chế tự chọn model theo độ khó mà
   LiteLLM không có — cần test chạy thật trước, và cân nhắc có còn so sánh công bằng không.

---

## 6. Request thật đã chạy

**Luồng thành công qua Bifrost (2026-09-26):**
```bash
curl -X POST http://localhost:18080/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"gemini/gemini-flash-latest","messages":[{"role":"user","content":"Trả lời ngắn: 1+1 bằng mấy?"}]}'
```
→ `"content":"2"`, `routing_info: {"provider":"gemini","model":"gemini-flash-latest","key":"gemini-key-1"}`,
latency ~3.8s, `usage: prompt 21 / completion 166 (trong đó reasoning 165)`.

**Cả 5 model trả lời qua Bifrost:** gpt-4o-mini 0.7s, gpt-4o 1.5s, claude-haiku-4-5 0.9s,
claude-sonnet-5 1.8s, gemini-flash 4.5s.

**Phát hiện phụ ảnh hưởng K2 (giá):**
- `gemini-flash-latest` thực tế trỏ tới **`gemini-3.8-flash`** (field `model` trong response) — đã sửa giá
  trong `model_pricing` (xem `docs/model-pricing-sources.md`).
- Phần lớn `completion_tokens` là **reasoning tokens** — token "suy nghĩ" vẫn tính vào output. Cùng 1
  câu hỏi, LiteLLM và Bifrost đều tính reasoning (11/217 và 11/166 token), nên so chi phí giữa 2 proxy
  vẫn công bằng; chênh lệch là do Gemini suy nghĩ khác nhau mỗi lần.

**Lưu ý khi dán key vào `.env`:** tắt bộ gõ tiếng Việt — lần đầu key OpenAI bị Unikey biến vài ký tự cuối
thành "ờ" và bị từ chối 401.

---

## 7. Chạy app Conduit qua Bifrost (D3: thí nghiệm đi qua app)

Bifrost không có alias, nên backend tự đổi tên model:
- **Gửi đi:** alias → tên thật theo `app.chat.proxy-model-names.bifrost` trong `application.yml`
  (VD `gemini-flash` → `gemini/gemini-flash-latest`). Bảng này phải khớp `proxy-configs/litellm/config.yaml`.
- **Nhận về:** đọc `extra_fields.routing_info` (`provider/model` đã thật sự trả lời, kể cả khi fallback)
  rồi đổi ngược về alias — `model` ngoài cùng của response là tên nội bộ của provider (VD
  `gemini-3.8-flash`), không tra được `model_pricing`.

Chạy backend với Bifrost (máy Khoa, Bifrost ở cổng 18080):
```bash
export CHAT_ACTIVE_PROXY=bifrost
export BIFROST_BASE_URL=http://localhost:18080/v1   # máy Hùng: bỏ qua, mặc định 8080
./mvnw spring-boot:run
CHAT_ACTIVE_PROXY=bifrost bash scripts/e2e_workflow_test.sh
```
Kết quả 2026-09-26: **43/43 PASS** qua Bifrost (`routing_decisions.proxy_name = bifrost`,
`cost_upstream > 0`); chạy lại với LiteLLM vẫn 43/43, `e2e_test.sh` 48/48. Lượt lỗi thật (Gemini 503
"high demand") được ghi `status = error`, không trừ credit.

**Chưa làm (Phase C):** backend chưa gửi `fallbacks`, và Bifrost đang `max_retries: 0` — nên lỗi 503 của
Gemini làm hỏng luôn lượt chat thay vì chuyển model. Cấu hình chuỗi fallback chờ D2 + D7, rồi ghi vào
`routing-policy.md`.
