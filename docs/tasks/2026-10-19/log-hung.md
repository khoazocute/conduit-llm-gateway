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
