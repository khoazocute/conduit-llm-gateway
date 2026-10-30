# Log tuần 19/10 → hạn 29/10 — Khoa

Theo `docs/tasks/2026-10-19/tasks.md`. Pull `lhung` (beaa0da) ngày 27/10, làm ngày 27/10.
`./mvnw test` **51/51** (sau merge `lhung` + TASK-66: **89/89**), test Python **72/72**.

## Việc đã làm

| Task | Kết quả | File | Hùng review gì |
|---|---|---|---|
| **TASK-54** test trừ credit đồng thời | ✅ 24 luồng cùng trừ 1 ví trên **Postgres thật** (mock không tái hiện được khóa lạc quan). 2 ca: đủ tiền, và trừ nhiều hơn số dư. Bất biến: số dư cuối = số dư đầu + tổng giao dịch đã ghi, không bao giờ âm. **Có `@Version`: 2/2 pass. Tạm bỏ `@Version`: 2/2 FAIL** (ca đủ tiền: ví 1.000, mỗi lượt trừ 7 — **cả 24 giao dịch được ghi** (sổ −168) nhưng **số dư chỉ giảm 14 = như 2 lượt**, 22 lượt bị ghi đè — mất cập nhật; test báo `expected 832, was 986`), rồi khôi phục. Lần thử đầu FAIL **sai lý do** (cột `version` null lúc tạo ví) → đổi sang tạo ví bằng SQL để bỏ `@Version` chỉ tắt đúng cơ chế khóa | `CreditServiceConcurrencyTest.java` | Tự bỏ `@Version` chạy lại, thấy fail |
| **TASK-67** lượt lỗi không có thông điệp | ✅ **2 chỗ mất:** (1) runner gặp `event: error` là dừng, bỏ qua dòng `data:` ngay sau, và record **không có trường `error`**; (2) backend chỉ gửi thông điệp qua SSE, không log. Sửa: runner đọc `data:` **qua cùng iterator** (gọi `iter_lines()` lần hai tạo iterator mới, dòng `data:` đã nằm trong bộ đệm iterator cũ → mất — lỗi tôi gặp khi sửa, có test); record có `error`; `ChatService` log `WARN` kèm proxy/model/thông điệp. Kiểm 1 lượt lỗi thật (Portkey, key OpenAI sai, $0): record ghi `401 … Incorrect API key provided` | `run_experiment.py`, `test_runner_sse_error.py`, `ChatService.java` | Đọc diff runner |
| **TASK-51** LiteLLM chính thức | ✅ **Phép thử sự cố chạy lại 27/10 (Hùng đồng ý): LiteLLM phục hồi 15/15** (20/10: 0/15), Bifrost 14/15, Portkey 0/15; 45 lượt, $0,019; ghi bổ sung vào `experiment-results.md`, không sửa số cũ. (1) Mặc định theo proxy: `default-model` để trống, `proxy-default-models: {litellm: conduit-pool}`; `CHAT_DEFAULT_MODEL` vẫn thắng nên `dry_run.sh` tái lập được thí nghiệm; Bifrost/Portkey giữ `gpt-4o-mini`. e2e **43/43**. (2) `fallbacks: conduit-pool → [claude-haiku, gemini-flash]`. (3) Phát hiện A. (4) Backend đọc `x-litellm-model-group` sau fallback (phát hiện B) | `config.yaml`, `application.yml`, `ChatProxyProperties.java`, `HttpProxyChatClient.java`, 5 test mới, `fault_injection.sh` | Duyệt `retry_policy` (đụng D7, xem phát hiện A) |
| **TASK-53** test Purchase/Credit/Chat | ✅ 25 test, mock, không gọi LLM. Chat: lượt lỗi không trừ credit; trừ đúng `ceil` **theo từng dòng giá** (101 vào + 51 ra × 1,5 = 152 + 77 = **229**); không đủ credit thì không ghi usage/routing; model thiếu giá → `cost_upstream = 0` (ghi lại hành vi hiện tại); retry khi xung đột ví. Credit: 9 ca gồm retry 3 lần. Purchase: 10 ca gồm webhook gọi lại không cộng credit lần 2, chữ ký sai/thiếu/body bị sửa đều bị từ chối | `ChatServiceTest`, `CreditServiceTest`, `PurchaseServiceTest` | — |
| **TASK-56** load test, phần chat | ✅ k6 qua Docker, alias giả `conduit-mock` (`mock_response`, $0). **Nhiều người dùng: 23.640 lượt, 0 lỗi, p95 211 ms.** Tìm ra và sửa phát hiện C | `loadtest/chat.js`, `loadtest/mock-pricing.sql`, `loadtest/results/`, `docs/load-test.md` | Thêm phần của Hùng vào `docs/load-test.md` mục 2 |
| **TASK-66** system prompt | ✅ **Xong 29/10** sau khi merge TASK-65a của Hùng. `ChatService` lấy `instructions` của agent, đặt thành lượt `system` đầu danh sách qua `ChatTurn.withSystemPrompt`; rỗng/NULL → request y hệt lúc đo. 5 test (3 helper + 2 `ChatServiceTest`). **Kiểm tay qua app, 2 lượt `gpt-4o-mini`:** agent có `instructions` "Always answer with exactly one word, written in UPPERCASE Vietnamese." trả lời "What is 2 + 2?" bằng **`BỐN`**; agent không có → `2 + 2 equals 4.`. `instructions` tốn token **mỗi lượt**: 15 → 33 token vào, credit người dùng 35 → 55 | `ChatTurn.java`, `ChatTurnTest.java`, `ChatService.java`, `ChatServiceTest.java` | — |

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

_Hùng đã làm hết (28/10):_ duyệt `retry_policy` → **D16** trong `roadmap.md`; điền mục 2 của
`docs/load-test.md`; đẩy TASK-65a; đồng ý phép thử 45 lượt.

## Còn thiếu

- Lượt chat thua xung đột ví quá 8 lần vẫn mất dấu chi phí LLM (chỉ log `WARN`). **Hùng đề nghị (28/10):**
  khi bỏ cuộc vẫn ghi `usage_logs status=error` kèm `cost_upstream`; lâu dài: khóa bi quan. **Đồng ý, chưa làm.**
- `Thread.sleep` trong vòng retry trừ credit chạy trên luồng xử lý request (tối đa vài trăm ms/lần) — ghi
  nhận là giới hạn (Hùng nhắc).
- TASK-67 còn 2 chỗ: SSE đứt giữa chừng → `error` trống; lỗi phía runner → record thiếu `message_id`
  (2 lượt D14, Hùng ghi). Chưa sửa.

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

## Bổ sung 29/10

- **Merge `lhung`** (6766b32) vào `dangkhoa`: 2 xung đột tài liệu giải theo hướng dẫn của Hùng
  (`load-test.md` lấy bản `lhung` — mục 1 giống từng ký tự bản của Khoa; `experiment-results.md` mục 13
  giữ cả hai). Sau merge: `./mvnw test` 87/87, Python 72/72, Flyway áp V3.
- **TASK-66 xong** (xem bảng trên).
- **Đếm `routing_decisions` cho 180 lượt nửa Khoa 19/10** (Hùng nhờ): **180/180**, 60/60/60 theo proxy,
  đối chiếu từng `message_id` với DB máy Khoa. Ghi vào `experiment-results.md` mục 13 (bảng "Đã kiểm").
- **Review TASK-64/65/52/55 của Hùng:** đạt cả 4, ghi ở cuối `log-hung.md`.
- Chi phí có phí thêm: 2 lượt (TASK-66), ~$0,00001.

## Review — Hùng (28/10) — chép từ `log-hung.md`: TASK-51, 53, 54, 56 (chat), 66 (phần đã làm), 67 của Khoa

> Ghi ở đây thay vì cuối `log-khoa.md` vì file đó chỉ có trên `dangkhoa`; tạo nó bên `lhung` sẽ thêm
> một xung đột merge. Khoa chép sang log của mình khi merge nếu muốn.

**Cách review:** merge `lhung` + `origin/dangkhoa` trên nhánh tạm ở máy Hùng (đã xóa sau), **tự chạy lại**:

| Kiểm | Kết quả |
|---|---|
| `./mvnw test` trên code đã merge | **87/87** (50 của Hùng + 37 của Khoa) |
| `python -m unittest discover -s experiments/tests` | **72/72** |
| `e2e_test.sh` trên code đã merge | **66/66** — thay đổi chat của Khoa không làm hỏng Auth/Agent |
| **TASK-54, phép thử ngược:** tạm bỏ `@Version` ở `CreditWallet.java:38` | **2/2 FAIL, `expected 832, was 986`** — đúng số Khoa báo. Đã hoàn tác |
| TASK-51: `application.yml` bind `litellm → conduit-pool` | Có `ChatProxyPropertiesBindingTest` nạp file thật; `CHAT_DEFAULT_MODEL` vẫn thắng nên `dry_run.sh` tái lập được thí nghiệm |
| Merge thử 2 nhánh | Code sạch; chỉ 2 file tài liệu xung đột (xem cuối) |

**Kết luận: đạt cả 6 task.** Phát hiện C (lỗi tiền khi một người dùng chat song song) là phát hiện có
giá trị nhất tuần, và bài học "test đồng thời phải đi qua đúng đường gọi thật" nên đưa vào báo cáo.

**Nhận xét, không chặn merge:**

1. **Phát hiện C, phần còn hở (Khoa đã tự ghi):** quá 8 lần xung đột thì LLM đã gọi (tốn tiền nhà cung
   cấp) nhưng chỉ còn một dòng `WARN`. Đề nghị tối thiểu: khi bỏ cuộc, **vẫn ghi một dòng `usage_logs`
   `status=error` kèm `cost_upstream`** (CLAUDE.md mục 5: chi phí không tính cho user nhưng phải "ghi log
   riêng"), để chi phí không biến mất khỏi DB. Lâu dài: khóa bi quan (`PESSIMISTIC_WRITE`) trên ví ở
   đường trừ credit của chat sẽ bỏ hẳn vòng retry.
2. `Thread.sleep` trong luồng xử lý request: chấp nhận được ở quy mô khóa luận (tối đa vài trăm ms mỗi
   lần), nhưng nên ghi vào giới hạn.
3. Bảng "Chạy lại 27/10" trong `experiment-results.md`: đã đủ trung thực (ghi rõ P1 vẫn sai, chỉ đổi cấu
   hình LiteLLM). D16 giờ ghi thêm lần chạy lại **không phải** so sánh lại 3 proxy cùng điều kiện.
4. TASK-67: chỗ còn sót (SSE đứt giữa chừng, không `done` không `error` → `error` trống) — đồng ý để sau.
5. Commit `f39e96a` ghi sai số liệu khi bỏ `@Version`; Khoa đã đính chính trong log. Không cần sửa
   lịch sử git.

**Hướng dẫn merge cho Khoa (PR của Hùng merge trước):** sau khi merge `main` vào `dangkhoa`:
- `docs/load-test.md` (add/add): **lấy nguyên bản của `main`** — đó là file của Khoa với mục 2 đã điền,
  99 dòng đầu trùng khớp từng ký tự với bản của Khoa.
- `docs/experiment-results.md` mục 13: **giữ cả hai**. Lấy các dòng của Khoa (TASK-51, TASK-67 đã xong),
  dòng "585/585" (bảng "Đã kiểm") và dòng mới "Đếm … 180 lượt nửa của Khoa" của Hùng; **bỏ** dòng cũ
  "Đếm dòng `routing_decisions` theo `proxy_name` cho 19–20/10 … Hùng" vì phần của Hùng đã xong.
- Load test của Hùng đã chuyển sang `loadtest/` cho cùng chỗ với `chat.js`.
