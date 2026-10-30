# Log Hùng — tuần 2026-10-19 (hạn 29/10)

## 27/10

| Task | Kết quả | Commit | File chính | Khoa cần làm |
|---|---|---|---|---|
| **TASK-65a** | Migration V3 `agents.instructions text` + trường trong `Agent.java`. Flyway chạy V3, Hibernate validate pass | `8d44491` | `db/migration/V3__add_agent_instructions.sql`, `domain/Agent.java` | **Bỏ chặn TASK-66** — pull về là có `agent.getInstructions()` |
| **TASK-64** | Chọn role lúc đăng ký (`user`/`creator`, `admin` và giá trị lạ → 400 với `details.role`). UI: `.seg` "Buy agents / Create agents" | `912707e` | `RegisterRequest`, `AuthService`, `register/page.tsx`, `auth-context.tsx`, `openapi.json` | Review |
| **TASK-65b** | `instructions` chỉ chủ agent + admin thấy; form + trang admin duyệt; sửa lỗi mất dữ liệu ở trang sửa agent | `52b3e11` | `AgentResponse`, `AgentService`, `AgentController`, `AdminAgentService`, `agent-form.tsx`, `edit/page.tsx`, `admin/agents/page.tsx` | Review, **riêng chỗ ABAC** |
| **TASK-46** | `routing_decisions` đủ **585/585** lượt chạy trên máy Hùng | `9f461f2` | `experiment-results.md` mục 13 | **Đếm 180 lượt nửa của bạn (19/10) trên DB máy bạn** — kỳ vọng 60 dòng/proxy |
| **TASK-52** | 36 unit test (Auth 12, Agent + AdminAgent 20, User 4). Backend tổng **50/50** | `99d2635` | `src/test/.../service/*Test.java` | Review |
| **TASK-55** | CI 3 job: backend (unit + `e2e_test.sh`), công cụ thí nghiệm, frontend. Không gọi LLM | `84edfa6` | `.github/workflows/ci.yml` | Review; test của bạn (TASK-53/54) tự được chạy khi thêm vào `src/test` |
| **TASK-56** (phần Hùng) | k6 endpoint không gọi LLM: 20 và 100 người dùng ảo, **0% lỗi** cả hai | `edd791e` | `scripts/load-test/browse.js`, `docs/load-test.md` | Điền mục B (chat) sau TASK-51 |
| **TASK-68** | **Chưa làm** — cần Hùng tự đọc dashboard OpenAI/Anthropic | — | — | — |

`e2e_test.sh`: 48 → **66 check**, pass hết (thêm 7 ca role, 11 ca `instructions`, đổi `psql` sang biến `PSQL` để chạy được trong CI).

## Phát hiện quan trọng

1. **Lỗi mất dữ liệu đã chặn trước khi xảy ra (TASK-65b).** Trang sửa agent cũ tải `GET /agents/{id}`
   **không kèm token** → backend coi là khách → trả bản công khai không có `instructions` → ô trống →
   chủ agent bấm Lưu là **ghi đè system prompt thành rỗng**. Sửa hai lớp: chỉ tải khi có token và gửi
   kèm token; và bản cho chủ/admin **luôn có** trường `instructions` (`""` khi chưa đặt) còn bản công
   khai **không có** trường đó, frontend thấy thiếu thì không gửi trường khi lưu.
2. **Test bảo mật có tác dụng thật.** Cố tình cho `AgentResponse.from()` trả `instructions` → **4 test
   fail đúng chỗ** (khách, người mua/creator khác, chợ, JSON công khai). Đã hoàn tác.
3. **CI: `mvnw` không có quyền chạy trong git** (`100644`) → Linux sẽ báo Permission denied. Đã đặt
   `100755`.
4. **Load test 100 người dùng ảo:** p95 danh sách agent 438 ms, sát ngưỡng 500 ms. Đo trên laptop nên
   chỉ để so sánh tương đối, không đại diện môi trường deploy.
5. Hai lượt lỗi Bifrost của đợt mở rộng có dòng `routing_decisions` trong DB nhưng **thiếu `message_id`
   trong file kết quả** → thêm một mặt của khoảng trống log lỗi (TASK-67 của bạn).

## Cần bàn cùng nhau

- **Thứ tự merge:** PR của mình có migration V3. Bạn làm TASK-66 thì pull `main` sau khi PR này merge,
  để không ai tạo một `V3` khác trùng số.
- **CI chưa chạy thật trên GitHub** — chỉ kiểm cục bộ (YAML hợp lệ, `e2e_test.sh` 66/66 qua đúng đường
  `PSQL` của CI, lint/tsc sạch, unittest thí nghiệm pass). Lần push đầu sẽ biết.

## 28/10

| Việc | Kết quả | Commit |
|---|---|---|
| Push `lhung` (10 commit hôm qua) | Khoa bỏ chặn được TASK-66 khi PR merge | — |
| **D16** | Duyệt `retry_policy` của Khoa, ghi vào `roadmap.md` mục 4 | `834ecc7` |
| CI chạy thật lần đầu | Backend ✅ (gồm `e2e_test.sh` 66/66 trên Linux), công cụ thí nghiệm ✅, **frontend ❌** ở `tsc` | — |
| Sửa CI frontend | `LayoutProps` là kiểu Next.js sinh trong `.next/types`; CI clone mới nên thiếu. Thêm `npx next typegen` trước `tsc`. Đã tái hiện lỗi và kiểm bản sửa trong điều kiện không có `.next`/`next-env.d.ts` | (commit này) |
| Gom load test về một thư mục | `scripts/load-test/` → `loadtest/` (cùng chỗ với `chat.js` của Khoa). `docs/load-test.md` = file của Khoa, mục 2 điền phần của Hùng | (commit này) |

## Review — Hùng (28/10): TASK-51, 53, 54, 56 (chat), 66 (phần đã làm), 67 của Khoa

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
