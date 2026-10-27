# Log tuần 19/10 → hạn 29/10 — Khoa

Theo `docs/tasks/2026-10-19/tasks.md`. Pull `lhung` (beaa0da) ngày 27/10, làm ngày 27/10.
`./mvnw test` **51/51**, test Python **72/72**.

## Việc đã làm

| Task | Kết quả | File | Hùng review gì |
|---|---|---|---|
| **TASK-54** test trừ credit đồng thời | ✅ 24 luồng cùng trừ 1 ví trên **Postgres thật** (mock không tái hiện được khóa lạc quan). 2 ca: đủ tiền, và trừ nhiều hơn số dư. Bất biến: số dư cuối = số dư đầu + tổng giao dịch đã ghi, không bao giờ âm. **Có `@Version`: 2/2 pass. Tạm bỏ `@Version`: 2/2 FAIL** (ca đủ tiền: ví 1.000, mỗi lượt trừ 7 — **cả 24 giao dịch được ghi** (sổ −168) nhưng **số dư chỉ giảm 14 = như 2 lượt**, 22 lượt bị ghi đè — mất cập nhật; test báo `expected 832, was 986`), rồi khôi phục. Lần thử đầu FAIL **sai lý do** (cột `version` null lúc tạo ví) → đổi sang tạo ví bằng SQL để bỏ `@Version` chỉ tắt đúng cơ chế khóa | `CreditServiceConcurrencyTest.java` | Tự bỏ `@Version` chạy lại, thấy fail |
| **TASK-67** lượt lỗi không có thông điệp | ✅ **2 chỗ mất:** (1) runner gặp `event: error` là dừng, bỏ qua dòng `data:` ngay sau, và record **không có trường `error`**; (2) backend chỉ gửi thông điệp qua SSE, không log. Sửa: runner đọc `data:` **qua cùng iterator** (gọi `iter_lines()` lần hai tạo iterator mới, dòng `data:` đã nằm trong bộ đệm iterator cũ → mất — lỗi tôi gặp khi sửa, có test); record có `error`; `ChatService` log `WARN` kèm proxy/model/thông điệp. Kiểm 1 lượt lỗi thật (Portkey, key OpenAI sai, $0): record ghi `401 … Incorrect API key provided` | `run_experiment.py`, `test_runner_sse_error.py`, `ChatService.java` | Đọc diff runner |
| **TASK-51** LiteLLM chính thức | ✅ **Phép thử sự cố chạy lại 27/10 (Hùng đồng ý): LiteLLM phục hồi 15/15** (20/10: 0/15), Bifrost 14/15, Portkey 0/15; 45 lượt, $0,019; ghi bổ sung vào `experiment-results.md`, không sửa số cũ. (1) Mặc định theo proxy: `default-model` để trống, `proxy-default-models: {litellm: conduit-pool}`; `CHAT_DEFAULT_MODEL` vẫn thắng nên `dry_run.sh` tái lập được thí nghiệm; Bifrost/Portkey giữ `gpt-4o-mini`. e2e **43/43**. (2) `fallbacks: conduit-pool → [claude-haiku, gemini-flash]`. (3) Phát hiện A. (4) Backend đọc `x-litellm-model-group` sau fallback (phát hiện B) | `config.yaml`, `application.yml`, `ChatProxyProperties.java`, `HttpProxyChatClient.java`, 5 test mới, `fault_injection.sh` | Duyệt `retry_policy` (đụng D7, xem phát hiện A) |
| **TASK-53** test Purchase/Credit/Chat | ✅ 25 test, mock, không gọi LLM. Chat: lượt lỗi không trừ credit; trừ đúng `ceil` **theo từng dòng giá** (101 vào + 51 ra × 1,5 = 152 + 77 = **229**); không đủ credit thì không ghi usage/routing; model thiếu giá → `cost_upstream = 0` (ghi lại hành vi hiện tại); retry khi xung đột ví. Credit: 9 ca gồm retry 3 lần. Purchase: 10 ca gồm webhook gọi lại không cộng credit lần 2, chữ ký sai/thiếu/body bị sửa đều bị từ chối | `ChatServiceTest`, `CreditServiceTest`, `PurchaseServiceTest` | — |
| **TASK-56** load test, phần chat | ✅ k6 qua Docker, alias giả `conduit-mock` (`mock_response`, $0). **Nhiều người dùng: 23.640 lượt, 0 lỗi, p95 211 ms.** Tìm ra và sửa phát hiện C | `loadtest/chat.js`, `loadtest/mock-pricing.sql`, `loadtest/results/`, `docs/load-test.md` | Thêm phần của Hùng vào `docs/load-test.md` mục 2 |
| **TASK-66** system prompt | ⛔ **Chặn bởi TASK-65a** (chưa có trên GitHub tới 27/10). Đã làm phần không phụ thuộc: `ChatTurn.withSystemPrompt()` + 3 test (rỗng → request y hệt; có → lượt đầu là system; `promptLength()` không đổi kể cả instructions 5.000 ký tự). Còn 1 dòng nối vào `ChatService` + kiểm tay ≤ 10 lượt | `ChatTurn.java`, `ChatTurnTest.java` | Đẩy TASK-65a |

## Phát hiện quan trọng

**A. Bật `fallbacks` thôi chưa đủ — LiteLLM retry lỗi 401 tới hết timeout.** Kiểm với key OpenAI sai
trong container `litellm` (3 lượt, < $0,001):

| Cấu hình | Kết quả | Thời gian |
|---|---|---|
| chỉ `fallbacks` | `claude-haiku` trả lời (header `x-litellm-attempted-fallbacks: 1`) | **~46–49 s** (haiku chỉ 0,7 s) |
| `fallbacks` + `retry_policy` | `claude-haiku` trả lời | **3,1 s** |

46 s bị tiêu vào retry 401 cho tới timeout 45 s. Backend cũng cắt cả lượt ở 45 s → **qua app, người
dùng vẫn nhận lỗi** dù proxy "có fallback". `retry_policy`: lỗi vĩnh viễn (xác thực, yêu cầu sai, vi
phạm chính sách nội dung) **0 lần**; lỗi tạm thời (timeout, rate limit, 5xx) **giữ 2 lần như D7**.
⚠️ Đây là **lệch khỏi D7** ("retry 2 giống nhau cả 3 proxy") — nhưng D7 đặt cho thí nghiệm (đã đóng);
đây là cấu hình tích hợp chính thức. Cần Hùng đồng ý.

**B. Sau fallback, `x-litellm-model-id` có thể là hash** (deployment đứng riêng không đặt
`model_info.id`) → không khớp `model_pricing` → **cost = 0 trong im lặng**. Lần kiểm này header trả
đúng `claude-haiku`, nhưng backend giờ ưu tiên `x-litellm-model-group` khi nhóm khác `conduit-pool`,
để không phụ thuộc vào điều đó.

**C. ⛔→✅ Một người dùng chat song song: ~50% lượt lỗi, và lượt LLM đã gọi bị mất dấu (đã sửa).**
Load test 1 tài khoản / 25 luồng: 10.897/21.750 lượt nhận `Unexpected error: Row was updated or
deleted by another transaction … CreditWallet`.
- Nguyên nhân: việc trừ credit chạy **bên trong** transaction của `ChatService.recordSuccessfulTurn`,
  nên 3 lần retry của `CreditService` đều nằm trong **cùng một transaction** đã bị đánh dấu rollback và
  vẫn đọc số dư cũ → không thể thắng.
- Hậu quả khi chạy thật: LLM **đã được gọi** (tốn tiền nhà cung cấp) nhưng **không ghi `usage_logs`,
  không trừ credit** — rò rỉ chi phí không dấu vết.
- TASK-54 không bắt được vì test gọi thẳng `CreditService`. **Bài học: test đồng thời phải đi qua
  đúng đường gọi thật.**
- Sửa: `ChatService.recordSuccessfulTurnWithRetry` retry **cả** `recordSuccessfulTurn` trong
  transaction **mới**, tối đa 8 lần, chờ ngẫu nhiên tăng dần 10 → 400 ms. Không chờ: 20 luồng → 11/20
  vẫn thua; có chờ: **20/20 và 40/40**. Load test sau sửa: **50% → 11%** lượt thua (11% còn lại là
  1 tài khoản gửi ~60 tin/giây — cực đoan; ghi trong `docs/load-test.md` mục "Giới hạn").

**D. Bẫy cổng trong `fault_injection.sh`** (file của Hùng): bật/tắt lỗi bằng `-f docker-compose.yml`
→ **bỏ qua `docker-compose.override.yml`** → trên máy remap port (máy Khoa: Bifrost 18080, 8080 là
Tomcat) Bifrost được tạo lại ở 8080 và không lên. Đã sửa: tự ghép override nếu có.

## Chi phí API

| Việc | Lượt | Chi phí |
|---|---|---|
| TASK-67: lượt lỗi giả lập (key OpenAI sai) | 3 | $0 (OpenAI từ chối key, không tính phí) |
| TASK-51: kiểm fallback với key OpenAI sai (`claude-haiku`, 5 token) | 3 | < $0,001 |
| TASK-51: `e2e_workflow_test.sh` qua `conduit-pool` | 1 | ~$0,00001 |
| TASK-56: load test + các lượt dò | ~85.000 | **$0** (`conduit-mock`) |
| TASK-51: phép thử sự cố chạy lại (lần 1 dừng ở kiểm ví vì ví cạn sau load test → 0 lượt; lần 2 đủ 45) | 45 | **$0,01923** |
| **Tổng có phí** | **49** | **~$0,020** |

## Cần Hùng

1. **Đẩy TASK-65a** (V3 + `Agent.instructions`) — đang chặn TASK-66. Khi có, Khoa nối 1 dòng + kiểm tay.
2. **Duyệt `retry_policy`** (phát hiện A) — lệch D7 cho cấu hình chính thức, không đụng thí nghiệm.
3. Viết phần của Hùng vào `docs/load-test.md` mục 2.

## Còn thiếu

- TASK-66: nối `withSystemPrompt` vào `ChatService` + kiểm tay ≤ 10 lượt (sau 65a).
- Review chéo TASK-64/65/52/55 của Hùng: **chưa có gì để review** (không có commit nào sau 22/10).
- Lượt chat thua xung đột ví quá 8 lần vẫn mất dấu chi phí LLM (chỉ log `WARN`); khóa bi quan khi
  trừ credit sẽ chặn hẳn — để bàn, không làm trong tuần này.

## Bổ sung 27–28/10

- **TASK-51 xong:** phép thử sự cố chạy lại (Hùng đồng ý). LiteLLM **15/15** phục hồi qua `claude-haiku`,
  độ trễ TB 4,4 s (20/10: 0/15, thất bại sau ~40 s). Lần chạy đầu **dừng trước khi gọi** vì ví thí
  nghiệm cạn (load test chiều 27/10 dùng chung tài khoản) — cơ chế chặn của Hùng hoạt động đúng; xoá
  `.experiment_identity.json` rồi chạy lại. Bản sửa `fault_injection.sh` (giữ override) được kiểm luôn
  trong lần chạy này: Bifrost tạo lại đúng cổng 18080 cả lúc bật lỗi lẫn lúc khôi phục.
- **TASK-67 kiểm trên dữ liệu thật:** 16/16 lượt lỗi của đợt chạy lại có thông điệp (0/32 trước đây).
  ⚠️ Còn một chỗ sót: luồng SSE đứt giữa chừng (không `done`, không `error`) → lượt lỗi nhưng `error`
  trống. Hiếm; chưa sửa.
- **Thêm `ChatProxyPropertiesBindingTest`:** nạp `application.yml` thật, chứng minh `litellm → conduit-pool`
  được bind (unit test cũ chỉ kiểm logic; sai tên khoá thì Spring bỏ qua không báo, và DB không phân
  biệt được hai đường vì đều ghi `gpt-4o-mini`).
- **Đính chính:** số liệu TASK-54 khi bỏ `@Version` đã sửa trong bảng trên. Commit `f39e96a` vẫn ghi
  "22 transactions recorded, balance dropped by 14" — **sai**; đúng là 24 giao dịch được ghi, số dư chỉ
  giảm như 2 lượt.
