# Ghi chú nghiên cứu routing Bifrost (K4)

**Phương pháp:** dò trực tiếp API + UI của container `conduit-bifrost` đang chạy thật
(`localhost:8080`, remap sang `18080` do máy Khoa có tiến trình khác chiếm 8080 — xem
`docker-compose.override.yml`), không đọc tài liệu suông. Đã gửi 1 request thật qua
`POST /v1/chat/completions` và xác nhận `routing_info` trả về đúng provider/model/key đã chọn.

---

## 1. Cách nạp cấu hình — khác với comment cũ trong `config.json`

Comment cũ ghi "import qua API/UI sau khi container đã chạy" — **thực tế Bifrost tự động hơn
thế**: khởi động lên là **tự dò các biến `.env`** đặt tên đúng chuẩn `<PROVIDER>_API_KEY`
(`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) và tự tạo key với `weight: 1`, `models: ["*"]` — không
cần thao tác gì. Xác nhận qua `GET /api/keys`:
```json
{"name": "ANTHROPIC_API_KEY_auto_detected", "weight": 1, "models": ["*"], ...}
{"name": "OPENAI_API_KEY_auto_detected", "weight": 1, "models": ["*"], ...}
```
**Phát hiện quan trọng:** `GEMINI_API_KEY` trong `.env` **KHÔNG được tự nhận** — Bifrost chỉ
nhận diện tên biến theo pattern nó biết trước (openai/anthropic), Gemini/Google cần khai báo
thủ công qua UI (`Models > Model Providers > Add New Provider`), khác OpenAI/Anthropic.

Dashboard UI (`http://localhost:18080/workspace/dashboard`) **mặc định KHÔNG yêu cầu đăng nhập**
(có checklist "Set up dashboard auth — Skip" — auth là tuỳ chọn, phải tự bật). Không cần
`setup_token`/tài khoản admin để xem/sửa cấu hình cơ bản trong môi trường dev này.

---

## 2. Cơ chế "chọn model rẻ nhất đủ tốt" — CHỈ diễn đạt được MỘT PHẦN (bản OSS)

Bifrost có 3 lớp cơ chế liên quan, độ trưởng thành khác nhau:

| Cơ chế | Vị trí UI | Trạng thái (bản đang chạy) | Diễn đạt được gì |
|---|---|---|---|
| **Weighted key balancing** | `Models > Model Providers` | ✅ Hoạt động, đã xác nhận | Nhiều key **cùng 1 provider** chia tải theo `weight` — KHÔNG phải chọn model rẻ nhất giữa các provider khác nhau, chỉ cân bằng tải giữa nhiều key |
| **Routing Rules (CEL)** | `Models > Routing Rules` | ✅ Khả dụng (chưa cấu hình) | "Create CEL-based rules to route requests by model, provider, budget, or custom attributes" — viết luật **tĩnh** kiểu if/else (VD: budget > X → dùng model rẻ), không tự động so giá real-time |
| **Complexity Router** (Beta) | `Models > Complexity Router` | ✅ Khả dụng, **chưa cấu hình** ("Classifier not configured") | Có sẵn cơ chế **phân loại độ khó câu hỏi bằng embedding** — so khớp câu hỏi với ~150 câu mẫu tham chiếu (đã có sẵn 50 câu mẫu cho tier "Simple" — ghi chú UI: "Requests to route to your cheapest, fastest model"), tự gán tier Simple/Medium/Complex rồi định tuyến theo tier |
| **Adaptive Routing** (cost/latency tự động) | menu riêng "Adaptive Routing" | 🔒 **Enterprise license** — bị khoá, chỉ có nút "Book a demo" | **Không dùng được ở bản OSS/miễn phí** |

**Lưu ý về phạm vi khóa luận (CLAUDE.md mục 1):** Complexity Router tuy nghe giống "hướng V2
đã bị bác bỏ" (tự phân loại câu hỏi để chọn model), nhưng đây là **tính năng có sẵn của
Bifrost**, không phải tự nghiên cứu/train classifier riêng — dùng tính năng có sẵn của proxy
là đúng phạm vi đánh giá (mục 2 CLAUDE.md: "đánh giá 3 proxy có sẵn"), khác hẳn việc tự xây
thuật toán routing như V2.

---

## 3. Cơ chế "failover" — KHÔNG diễn đạt được ở bản OSS

**Circuit Breaker** ("Automatically redirect traffic to a fallback provider when your primary
endpoint shows signs of failure") — đúng định nghĩa failover cần tìm — nhưng menu này báo
**"part of the Bifrost enterprise license"**, chỉ có nút "Book a demo", **không cấu hình được**.

Cách duy nhất giả lập failover ở bản OSS: dùng **nhiều key cùng provider với weight khác nhau**
(Model Providers) — nhưng đây là load balancing chủ động (chia tải trước), KHÔNG phải failover
phản ứng (tự phát hiện lỗi rồi chuyển hướng) như LiteLLM/Portkey có thể làm.

---

## 4. Kết luận nhanh cho quyết định chọn proxy (input cho D-decision)

| | LiteLLM (ghi chú H4) | Bifrost |
|---|---|---|
| Failover thật (tự phát hiện lỗi) | Có (theo tài liệu, Hùng xác nhận thêm) | **Không — Enterprise only** |
| Chọn model theo cost/latency tự động | Có (`routing_strategy`) | **Không — Enterprise only** ("Adaptive Routing") |
| Chọn model theo độ phức tạp câu hỏi | Không có sẵn | Có (Complexity Router, Beta, cần cấu hình classifier) |
| Routing theo luật tĩnh (budget/attribute) | Có (routing_strategy khác) | Có (Routing Rules, CEL) |
| Tự nhận key qua biến môi trường | Không rõ, cần Hùng xác nhận | Có (openai/anthropic, KHÔNG có gemini) |

**Điểm quan trọng nhất cho báo cáo:** nếu quy tắc quyết định (CLAUDE.md mục 2) coi trọng
"failover" là tiêu chí bắt buộc, Bifrost bản OSS **không đáp ứng được** — đây là dữ liệu thực tế
cần đưa vào bảng so sánh, không phải suy đoán từ tài liệu marketing của Bifrost (vốn PR mạnh
tính năng failover nhưng không nói rõ nó thuộc gói trả phí).

---

## 5. Việc đã làm để xác nhận (đúng "Xong khi" của K4)

Gửi 1 request thật qua Bifrost:
```bash
curl -X POST http://localhost:18080/v1/chat/completions \
  -d '{"model":"anthropic/claude-3-5-haiku-20241022","messages":[{"role":"user","content":"Say hi in 3 words"}]}'
```
Response xác định rõ model/provider/key đã chọn qua `routing_info`:
```json
"routing_info":{"provider":"anthropic","model":"claude-3-5-haiku-20241022","key":"ANTHROPIC_API_KEY_auto_detected"}
```
(Lỗi 401 trong response là do key Anthropic trong `.env` là placeholder — không liên quan tới
cơ chế routing, đã xác nhận tách bạch 2 vấn đề.)
