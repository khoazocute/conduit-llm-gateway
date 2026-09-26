# Ghi chú nghiên cứu routing Bifrost (K4)

**Phương pháp:** dò trực tiếp API + UI của container `conduit-bifrost` (`maximhq/bifrost:latest`)
đang chạy thật (`localhost:8080`, remap sang `18080` trên máy Khoa — xem
`docker-compose.override.yml`), không chỉ đọc tài liệu. Mọi kết luận dưới đây đều có request thật
kèm theo (mục 5). Lần test: 2026-09-23 và 2026-09-26.

---

## 1. Cách nạp cấu hình

- **OpenAI/Anthropic: tự động.** Khởi động lên là Bifrost tự dò biến `.env` đặt tên đúng chuẩn
  `<PROVIDER>_API_KEY` và tạo key `*_auto_detected` với `weight: 1`, `models: ["*"]`.
- **Gemini: KHÔNG tự nhận** `GEMINI_API_KEY` — phải khai báo thủ công, 2 bước qua API (tương đương
  UI `Models > Model Providers > Add New Provider`):
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
  (file đó chỉ là tài liệu tham khảo). Máy khác (Hùng) phải chạy lại 2 lệnh trên.
- Dashboard `http://localhost:18080` mặc định **không yêu cầu đăng nhập**.

---

## 2. "Chọn model rẻ nhất đủ tốt" — chỉ diễn đạt được MỘT PHẦN ở bản OSS

| Cơ chế | Trạng thái | Diễn đạt được gì |
|---|---|---|
| **Weighted routing** | ✅ Có | Chia tải theo `weight` giữa nhiều key/provider phục vụ **cùng 1 model** — không chọn giữa 5 model khác nhau (khớp ghi chú H5 của Hùng) |
| **Routing Rules (CEL)** | ✅ Có, chưa cấu hình | Luật **tĩnh** if/else theo model/provider/budget — không tự so giá real-time |
| **Complexity Router** (Beta) | ✅ Có, chưa cấu hình | Phân loại độ khó câu hỏi bằng embedding (tier Simple/Medium/Complex) rồi định tuyến theo tier. Là tính năng có sẵn của proxy, không phải tự train classifier (không vi phạm phạm vi CLAUDE.md mục 1) |
| **Adaptive Routing** (cost/latency tự động) | 🔒 Enterprise | Không dùng được ở bản OSS |

---

## 3. Failover — CÓ ở bản OSS, nhưng chỉ dạng tĩnh

Bifrost có **2 cơ chế failover khác nhau**, trạng thái khác nhau:

| Cơ chế | Trạng thái | Cách hoạt động |
|---|---|---|
| **`fallbacks` trong request** | ✅ **Chạy được, đã test sống** | Khai báo danh sách model dự phòng ngay trong request: `"fallbacks": ["gemini/gemini-flash-latest"]`. Provider chính lỗi → thử lần lượt theo **thứ tự cố định**, không theo cost/latency |
| **Circuit Breaker** | 🔒 Enterprise | Tự dò provider hỏng qua health-check rồi chuyển hướng trước khi request lỗi |

**Bằng chứng (2026-09-26):** primary `anthropic/claude-haiku-4-5-20251001` (key trả 401) +
`"fallbacks": ["gemini/gemini-flash-latest"]` → trả lời thành công, `routing_info` ghi rõ:
```json
{"provider":"gemini","model":"gemini-flash-latest","is_fallback":true,
 "primary_provider":"anthropic","primary_model":"claude-haiku-4-5-20251001"}
```
→ **Xác nhận đúng phát hiện H5 của Hùng** (bản đó đọc từ tài liệu, chưa test).

**Điều kiện kích hoạt (quan sát được):**
- Lỗi 401 từ provider chính → **có** fallback.
- Provider chưa cấu hình (`failed to get config for provider`) → **không** fallback, trả lỗi luôn.
- `fallbacks` phải là mảng string `"provider/model"`; dạng object → `400 Invalid request payload`.

**Đính chính:** bản trước của mục này kết luận "failover không có ở bản OSS" — **sai**. Lần test
đầu (26/09) chọn đích fallback là `openai`, nhưng key OpenAI trên máy Khoa cũng đang 401, nên cả 2
đều lỗi và không thấy được fallback. Test lại với đích chạy được (gemini) thì fallback hoạt động.

**Hệ quả cho thí nghiệm:** failover của Bifrost là **chuỗi tĩnh do người gọi khai báo**, không tự
dò lỗi trước. Cấu hình công bằng khi so 3 proxy: cùng 1 chuỗi fallback, cùng `max_retries`
(mặc định Bifrost hiện là `max_retries: 0` cho mọi provider — cần chốt ở D7).

---

## 4. So sánh nhanh (input cho `routing-policy.md` / D2)

| | LiteLLM (ghi chú H4) | Bifrost (test sống) |
|---|---|---|
| Failover khi lỗi | Có | **Có — chuỗi tĩnh theo thứ tự** (`fallbacks`); tự dò lỗi (Circuit Breaker) = Enterprise |
| Chọn model theo cost/latency tự động | Có (`routing_strategy`) | **Không** — Adaptive Routing = Enterprise |
| Gom nhiều model thành 1 alias để proxy tự chọn | Có | **Không** — weight chỉ giữa các provider của cùng 1 model |
| Chọn model theo độ khó câu hỏi | Không | Có (Complexity Router, Beta, chưa cấu hình) |
| Luật tĩnh (budget/attribute) | Có | Có (Routing Rules, CEL) |
| Tự nhận key từ `.env` | — | Có với openai/anthropic, **không** với gemini |

**Điểm chính cho báo cáo:** Bifrost OSS diễn đạt được "failover" nhưng **không** diễn đạt được
"chọn model rẻ nhất" tự động — đây là giới hạn cần ghi rõ trong `routing-policy.md`.

---

## 5. Request thật đã chạy (đúng "Xong khi" của K4)

**Luồng thành công qua Bifrost (2026-09-26):**
```bash
curl -X POST http://localhost:18080/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"gemini/gemini-flash-latest","messages":[{"role":"user","content":"Trả lời ngắn: 1+1 bằng mấy?"}]}'
```
→ `"content":"2"`, `routing_info: {"provider":"gemini","model":"gemini-flash-latest","key":"gemini-key-1"}`,
latency ~3.8s, `usage: prompt 21 / completion 166 (trong đó reasoning 165)`.

**Phát hiện phụ ảnh hưởng K2 (giá):**
- `gemini-flash-latest` thực tế trỏ tới **`gemini-3.8-flash`** (field `model` trong response),
  **không phải 2.5 Flash** như giả định khi nhập giá — giá `gemini-flash` trong `model_pricing` cần
  xem lại (xem `docs/model-pricing-sources.md` mục 3).
- Gần như toàn bộ `completion_tokens` là **reasoning tokens** (165/166) — token "suy nghĩ" ẩn vẫn
  được tính vào output, làm chi phí thật của Gemini cao hơn nhiều so với độ dài câu trả lời.

---

## 6. Chạy app Conduit qua Bifrost (D3: thí nghiệm đi qua app)

Bifrost không có alias như LiteLLM, nên backend phải tự đổi tên model:
- **Gửi đi:** alias → tên thật theo `app.chat.proxy-model-names.bifrost` trong `application.yml`
  (VD `gemini-flash` → `gemini/gemini-flash-latest`). Bảng này phải khớp `proxy-configs/litellm/config.yaml`.
- **Nhận về:** đọc `extra_fields.routing_info` (`provider/model` đã thật sự trả lời, kể cả khi
  fallback) rồi đổi ngược về alias — `model` ở ngoài cùng của response là tên nội bộ của provider
  (VD `gemini-3.8-flash`), không tra được `model_pricing`.

Chạy backend với Bifrost (máy Khoa, Bifrost ở cổng 18080):
```bash
export CHAT_ACTIVE_PROXY=bifrost
export BIFROST_BASE_URL=http://localhost:18080/v1   # máy Hùng: bỏ qua, mặc định 8080
./mvnw spring-boot:run
CHAT_ACTIVE_PROXY=bifrost bash scripts/e2e_workflow_test.sh
```
Kết quả 2026-09-26: **43/43 PASS** qua Bifrost (`routing_decisions.proxy_name = bifrost`,
`cost_upstream > 0`); chạy lại với LiteLLM vẫn 43/43, `e2e_test.sh` 48/48.

**Chưa làm (Phase C):** backend chưa gửi `fallbacks` — cấu hình chuỗi fallback cho thí nghiệm chờ
D2 (mục tiêu routing chung) và D7 (`max_retries`/timeout) chốt, rồi ghi vào `routing-policy.md`.

**Trạng thái key trên máy Khoa (2026-09-26):** đã có đủ key OpenAI, Anthropic, Gemini; cả 5 model
trả lời qua Bifrost (gpt-4o-mini 0.7s, gpt-4o 1.5s, claude-haiku-4-5 0.9s, claude-sonnet-5 1.8s,
gemini-flash 4.5s). Lưu ý khi dán key vào `.env`: tắt bộ gõ tiếng Việt — lần đầu key OpenAI bị
Unikey biến vài ký tự cuối thành "ờ" và bị từ chối 401.
