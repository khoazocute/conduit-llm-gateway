# Tuần 2026-10-19 → hạn 29/10 — việc được giao

**Phần đánh giá proxy đã đóng** (TASK-49 xong 20/10). Kết luận và số liệu ở
`docs/experiment-results.md` (đọc mục 1 và mục 13, 5 phút là đủ). Không chạy lại thí nghiệm 720 lượt,
không sửa số liệu hay luật đã áp.

**Tuần này dồn việc của 2 tuần:** toàn bộ Phase F (TASK-50 → 56, hạn gốc 30/10 → 08/11) kéo về
**hạn chung Thứ Năm 29/10**. Số task, chủ task và người review lấy theo tracker Notion. Task mới
đánh số tiếp: **TASK-64 → 68**.

Quy ước giữ nguyên: mỗi người ghi `log-hung.md` / `log-khoa.md` trong folder này, commit kèm sản
phẩm, không paste log vào chat. Review ghi vào cuối file log của người được review, dưới mục
`## Review — <người review> (<ngày>)`.

---

## 1. Ba quyết định đã chốt (22/10, nhóm tự quyết vì thầy bận) — đừng bàn lại

Nguồn đầy đủ: `docs/roadmap.md` mục 4, dòng **D8**. Đây là TASK-50, đã xong.

1. **Role chọn lúc đăng ký.** `RegisterRequest` thêm trường `role` **tùy chọn**: chỉ nhận `user` hoặc
   `creator`, mặc định `user`, gửi `admin` thì **400**. Admin vẫn chỉ tạo qua SQL. An toàn vì agent
   của creator vẫn phải qua admin duyệt. Không làm luồng thu phí hay nút nâng cấp sau.
2. **System prompt riêng của agent** theo mô hình *Claude Project*: cột mới **`agents.instructions`**
   (Flyway V3). `introduction` giữ vai trò mô tả công khai trên chợ. **`instructions` chỉ trả về cho
   chủ agent và admin**, không bao giờ trả cho người mua hay trang công khai.
3. **Đính kèm file vào agent = RAG** (TASK-57), Should-have, **không làm tuần này**. Bảng
   `knowledge_bases` / `kb_chunks` đã có sẵn trong V1, chưa có entity.

**Về phần đánh giá, đọc trước khi ai hỏi:** kết luận chọn LiteLLM **đổi theo ngưỡng chất lượng**
(đặt 85% thì ra Bifrost, 90% thì ra Portkey), nhưng ngưỡng 80% đã khóa từ commit đầu tiên `9d6dfd7`
(11/09), hơn 5 tuần trước kết quả. Bảng đầy đủ ở `docs/experiment-results.md` mục 7.6.

---

## 2. Bảng việc

| Task | Việc | Người | Review | Phụ thuộc | Hạn |
|---|---|---|---|---|---|
| TASK-50 | Chốt D8 | Cả hai | — | — | **xong 22/10** |
| TASK-65a | **Chỉ** migration V3 + trường `instructions` trong `Agent.java`, PR riêng vào `main` | Hùng | Khoa | — | **23/10** |
| TASK-64 | Role chọn lúc đăng ký | Hùng | Khoa | — | 23/10 |
| TASK-46 | (phần còn lại) đếm dòng `routing_decisions` 19–20/10 | Hùng | — | Docker | 23/10 |
| TASK-68 | Đối chiếu chi phí thực nghiệm với dashboard nhà cung cấp | Hùng | — | — | 23/10 |
| TASK-54 | Test trừ credit **đồng thời** | Khoa | Hùng | — | 24/10 |
| TASK-67 | Khoảng trống log lỗi | Khoa | Hùng | — | 24/10 |
| TASK-65b | Phần còn lại của `instructions`: DTO, chặn lộ, frontend, hợp đồng | Hùng | Khoa | 65a | 24/10 |
| TASK-51 | Tích hợp LiteLLM chính thức + `fallbacks` + chạy lại phép thử sự cố | Khoa | Hùng | — | 26/10 |
| TASK-66 | Chèn `instructions` thành lượt `system` trong chat | Khoa | Hùng | **65a** | 26/10 |
| TASK-52 | Test `AuthService`, `AgentService`, `UserService` | Hùng | Khoa | 64, 65b | 26/10 |
| TASK-53 | Test `PurchaseService`, `CreditService`, `ChatService` | Khoa | Hùng | 66 | 27/10 |
| TASK-55 | CI GitHub Actions | Hùng | Khoa | — (khung trước, test có sẵn tới đâu chạy tới đó) | khung 25/10, đủ 27/10 |
| TASK-56 | Load test bằng `grafana/k6`, **không gọi LLM có phí** | Cả hai | — | phần chat cần 51 | 28/10 |
| — | Review chéo, PR vào `main`, cập nhật Notion | Cả hai | — | tất cả | 29/10 |

Phase G (TASK-57 → 63) **giữ hạn cũ**, chỉ là được bắt đầu sớm hơn nếu Phase F xong sớm.

## 3. Hai người có phải chờ nhau không

**Chỉ một chỗ chờ thật:** TASK-66 (Khoa) cần cột `instructions` và trường trong entity `Agent`, nếu
không code không biên dịch. Gỡ bằng **TASK-65a**: Hùng đẩy riêng phần nhỏ này (~10 dòng) lên `main`
**trước tiên**, ngày 23/10. Phần lớn (65b) làm sau, Khoa không phải chờ.

Còn lại chạy song song được:
- **TASK-55 CI** không chờ test của ai: CI chạy test nào đang có, test viết thêm thì tự được chạy.
- **TASK-56 load test**: chỉ phần chat cần TASK-51. Đăng nhập, danh sách agent, ví làm được ngay.
- **Review chéo**: xong task nào review task đó, không đợi xong hết.
- **TASK-51** cần Hùng nhắn đồng ý trước khi chạy lại phép thử sự cố (tốn phí), không cần chờ Hùng làm gì.
- **Va chạm khi merge**: cả hai có thể sửa `docs/openapi.json`; ai merge sau xử lý xung đột.

---

## 4. Việc của Hùng (Auth + Agent + CI)

### TASK-65a — Mở đường cho Khoa (làm đầu tiên)
- `backend-gateway/src/main/resources/db/migration/V3__add_agent_instructions.sql`:
  `ALTER TABLE agents ADD COLUMN instructions text;`. **Không** dùng `ddl-auto`.
- `domain/Agent.java`: trường `instructions` + getter/setter. Không đụng DTO ở bước này.
- PR riêng, merge vào `main` ngay khi Khoa review xong (vài phút).
- **Đạt khi:** backend khởi động được, Flyway chạy V3, Hibernate validate pass.

### TASK-64 — Role lúc đăng ký
- **Backend:** `dto/auth/RegisterRequest.java` (thêm `role`, validate chỉ `user`/`creator`),
  `service/AuthService.register()`. `admin` → **400**, không âm thầm hạ về `user`.
- **Frontend:** `app/(auth)/register/page.tsx` + `context/auth-context.tsx` (hàm `register` nhận
  thêm `role`): lựa chọn "Mua agent" / "Tạo agent". Sau đăng ký vẫn đi qua `homePathForRole()`.
  Style theo `docs/design-system.md`.
- **Hợp đồng:** `docs/openapi.json` → `RegisterRequest` (`role` enum `user`/`creator`, không bắt buộc).
- **Test:** `backend-gateway/scripts/e2e_test.sh` — thay bước nâng creator bằng SQL (dòng ~120–127)
  bằng đăng ký `role=creator`; thêm ca `role=admin` → 400 và ca bỏ trống → `user`.
- **Tương thích:** script nâng role bằng SQL (`experiments/scripts/run_experiment.py:236`,
  `e2e_workflow_test.sh:56`) phải vẫn chạy được, đừng xóa.
- **Đạt khi:** `e2e_test.sh` pass, đăng ký creator vào thẳng `/dashboard`.

### TASK-65b — Phần còn lại của `instructions`
- **Backend:** `dto/agent/CreateAgentRequest`, `UpdateAgentRequest` (thêm `instructions`, tùy chọn),
  `AgentResponse`, `AgentService`.
- **ABAC, chỗ dễ sai nhất:** `GET /agents` và `GET /agents/{id}` là `permitAll`
  (`security/SecurityConfig.java:57`) và đang dùng chung `AgentResponse`. Chỉ điền `instructions`
  khi người gọi là **chủ agent hoặc admin** (`@JsonInclude(NON_NULL)` hoặc DTO riêng) →
  `AgentController.getById` nhận principal tùy chọn. Danh sách `GET /agents` **không bao giờ** trả.
- **Frontend:** `components/agent-form.tsx` (ô "Hướng dẫn cho agent"), trang edit,
  `app/(app)/admin/agents/page.tsx` (admin thấy để duyệt), `lib/api/types.ts`.
- **Hợp đồng:** `docs/openapi.json` (Agent, CreateAgentRequest, UpdateAgentRequest), `docs/erd.dbml`.
- **Test** (thêm vào `e2e_test.sh`): người mua gọi `GET /agents/{id}` **không** thấy `instructions`;
  chủ agent và admin thấy; người chưa đăng nhập không thấy.
- **Đạt khi:** `e2e_test.sh` + `e2e_workflow_test.sh` pass; không đường nào lộ `instructions`.

### TASK-46 (phần còn lại) và TASK-68 — Đối chiếu cuối cho phần đánh giá
- **TASK-46:** bật Docker + Postgres, đếm dòng `routing_decisions` theo `proxy_name` trong 19–20/10,
  so với 720 + 45. `CLAUDE.md` mục 2 bắt buộc mọi lượt ghi vào bảng này.
- **TASK-68:** tổng ~$0,36 của 19–20/10 với dashboard OpenAI và Anthropic.
- Lệch thì **ghi rõ vào `docs/experiment-results.md` mục 13**, không chạy lại gì. Chi phí lệch thì
  tính lại offline từ `model_pricing`; kết luận chỉ đổi nếu giá sai hơn ~4,5 lần.

### TASK-52 — Test service Auth / Agent / User
- Hiện `src/test` chỉ có 4 file (`JwtServiceTest`, 2 test adapter, 1 test khởi động context).
- Unit test `AuthService` (đăng ký có/không role, `admin` bị từ chối, email trùng, logout khi token
  hết hạn), `AgentService` (chuyển trạng thái draft→pending→published/rejected→unpublished,
  `requireOwnership`, ẩn `instructions`), `UserService`.
- **Đạt khi:** `./mvnw test` pass, chạy trong CI.

### TASK-55 — CI GitHub Actions
- `.github/workflows/` chưa tồn tại. Workflow: build backend + `./mvnw test` +
  `python -m unittest discover -s experiments/tests` + `npm run lint` ở `frontend/`.
- `BackendGatewayApplicationTests` là `@SpringBootTest` cần DB thật → khai **service Postgres
  (`pgvector/pgvector:pg16`) + Redis** trong workflow. Không có Testcontainers.
- Security acceptance (webhook sai chữ ký, callback trùng, JWT hết hạn): đưa vào CI phần chạy được
  không cần proxy; script e2e cần đủ proxy nên để ngoài CI.
- **Đạt khi:** CI xanh trên một PR thử.

---

## 5. Việc của Khoa (Credit + Chat + Payment)

### TASK-54 — Test trừ credit đồng thời (làm đầu, rủi ro cao nhất)
- Ràng buộc bắt buộc `CLAUDE.md` mục 4, hiện **chưa có test nào**. Cơ chế có sẵn: `@Version` ở
  `domain/CreditWallet.java:38`.
- Ví có N credit, bắn nhiều lượt trừ song song → **số dư không bao giờ âm**, tổng trừ đúng, lượt thua
  `@Version` được retry hoặc từ chối sạch, không trừ hụt.
- **Đạt khi:** chạy được bằng `./mvnw test`, và **fail** nếu cố tình bỏ `@Version` (chứng minh test
  có tác dụng).

### TASK-67 — Khoảng trống log lỗi
- **0/32 lượt lỗi ghi được thông điệp lỗi** (`experiment-results.md` mục 9 và phép thử sự cố D15).
  Truy nguyên nhân: `ChatService.emitError` / `recordFailedTurn` không lưu, hay
  `experiments/scripts/run_experiment.py` không ghi trường `error`. Sửa chỗ đúng.
- **Đạt khi:** một lượt lỗi giả lập (key sai) để lại thông điệp đọc được.

### TASK-51 — Tích hợp LiteLLM chính thức
- **Phát hiện quan trọng:** `application.yml:45` mặc định `default-model: gpt-4o-mini` → chat thường
  gọi thẳng alias `gpt-4o-mini`, **không qua `conduit-pool`**. Thí nghiệm dùng `conduit-pool` chỉ nhờ
  `dry_run.sh` đặt biến môi trường. Phải đổi mặc định sang `conduit-pool` khi `active-proxy=litellm`,
  **giữ biến `CHAT_DEFAULT_MODEL`** để `dry_run.sh` vẫn tái lập được thí nghiệm.
- Thêm `fallbacks` cho nhóm `conduit-pool` trong `proxy-configs/litellm/config.yaml` (log hiện báo
  `Available Model Group Fallbacks=None`).
- Chạy lại `bash experiments/scripts/fault_injection.sh` — **45 lượt, ~$0,01 → nhắn Hùng xin đồng ý
  trước** (CLAUDE.md mục 2: trên 10 lượt). Ghi kết quả **bổ sung** vào mục "Phép thử tiêm lỗi" của
  `docs/experiment-results.md`, không sửa số cũ. Vẫn 0/15 thì ghi nguyên văn (lỗi 401 có thể không
  kích hoạt fallback) và thử thêm một loại lỗi khác trước khi kết luận.
- **Đạt khi:** chat thường ghi `routing_decisions.proxy_name = litellm` qua `conduit-pool`; có kết
  quả phép thử sự cố mới.

### TASK-66 — `instructions` thành system prompt (sau TASK-65a)
- `service/ChatService.doSendMessage()` (dòng ~92): agent có `instructions` khác rỗng thì thêm
  `new ChatTurn("system", instructions)` **đầu danh sách**. Sửa chú thích `adapter/ChatTurn.java`.
- `HttpProxyChatClient.promptLength()` chỉ đếm tin nhắn user cuối, nên lượt `system` không làm lệch
  định tuyến. Giữ nguyên và có test.
- **Test:** rỗng/`null` → không có lượt system (request y hệt lúc đo); có → lượt đầu là system;
  `promptLength()` không đổi.
- Kiểm tay bằng model rẻ, **không quá 10 lượt**. Ghi nhận xét nếu chi phí mỗi lượt tăng đáng kể
  (`instructions` tốn token mỗi lượt và tính vào credit người dùng).

### TASK-53 — Test service Purchase / Credit / Chat
- Unit test `PurchaseService` (idempotent theo `transaction_ref`), `CreditService`, `ChatService`
  (lượt lỗi không trừ credit, có usage thì trừ đúng `ceil(token × 1.5)`). Provider dùng mock, không
  gọi LLM thật.
- **Đạt khi:** `./mvnw test` pass, chạy trong CI.

---

## 6. Việc chung — TASK-56 Load test (28/10)

- Không có k6 trên máy → chạy bằng image Docker `grafana/k6`.
- **Không gọi LLM có phí.** Phần chat dùng một alias giả trong LiteLLM (`mock_response` trong
  `litellm_params`) — **kiểm bằng 1 request trước**. Cần thêm dòng `model_pricing` giá 0 cho alias đó
  ở môi trường local, nếu không ChatService không tính được phí. Không làm được thì chỉ load test các
  endpoint không gọi LLM.
- Chia: **Hùng** kịch bản đăng nhập, danh sách agent, ví (làm được ngay). **Khoa** kịch bản chat
  (sau TASK-51).
- **Đạt khi:** có báo cáo ngắn (số người dùng ảo, thời gian phản hồi p95, tỷ lệ lỗi) trong
  `docs/load-test.md`.

## 7. Lịch theo ngày

| Ngày | Hùng | Khoa |
|---|---|---|
| 22–23/10 | **TASK-65a trước tiên**, 64, 46, 68, khung CI | TASK-54, 67 |
| 24–25/10 | TASK-65b, bắt đầu 52 | TASK-51, 66 |
| 26–27/10 | TASK-52, CI đủ | TASK-53 |
| 28–29/10 | TASK-56 (phần không chat), review, PR, Notion | TASK-56 (phần chat), review |

Chi phí thật dự kiến cả tuần: chỉ TASK-51 (~45 lượt, ~$0,01) và vài lượt kiểm tay TASK-66.
`e2e_workflow_test.sh` gọi LLM thật ít nhất 1 lượt mỗi lần chạy, **đừng chạy lặp**.

## 8. Bẫy môi trường

- **Docker Desktop phải bật trước.** Máy sập thì container tắt hết (đã gặp 20/10):
  `docker compose up -d`, rồi `python experiments/scripts/preflight.py` (miễn phí).
- Tắt bằng `docker compose stop`, **không** `down -v`: `bifrost-data` chứa cấu hình Complexity Router.
- Backend không đọc `.env`: export `LITELLM_MASTER_KEY` trước `./mvnw spring-boot:run`.
- Redis ở cổng host `26379`; backend ở `8081` với context-path `/api` (`8080` là Bifrost).

## 9. Checklist hạn 29/10

- [ ] TASK-65a merge vào `main` (23/10)
- [ ] TASK-64 role lúc đăng ký, `e2e_test.sh` pass
- [ ] TASK-65b `instructions`, có test chứng minh người mua không thấy
- [ ] TASK-46 + 68 kết quả đối chiếu ghi vào `experiment-results.md` mục 13
- [x] TASK-54 test đồng thời, fail khi bỏ `@Version` — Khoa 27/10
- [x] TASK-67 lượt lỗi có thông điệp — Khoa 27/10
- [x] TASK-51 chat thường qua `conduit-pool`, phép thử sự cố chạy lại — Khoa 27/10, LiteLLM 15/15
- [ ] TASK-66 system prompt vào chat, `promptLength()` không đổi — ⛔ chờ TASK-65a; phần helper + test xong 27/10
- [ ] TASK-52, 53 test service pass
- [ ] TASK-55 CI xanh
- [ ] TASK-56 báo cáo load test
- [ ] Review chéo ghi vào cuối `log-*.md`, PR vào `main`, Notion cập nhật
