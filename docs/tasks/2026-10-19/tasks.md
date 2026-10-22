# Tuần 2026-10-19 → 2026-10-25 — việc được giao

**Phần đánh giá proxy đã đóng.** Kết luận và số liệu ở `docs/experiment-results.md` (đọc mục 1 và mục
13, 5 phút là đủ). Tuần này chuyển sang **Phase F**: tích hợp proxy đã chọn và hoàn thiện Must-have.
Không chạy lại thí nghiệm 720 lượt, không sửa số liệu hay luật đã áp.

Quy ước giữ nguyên: mỗi người ghi `log-hung.md` / `log-khoa.md` trong folder này, commit kèm sản
phẩm, không paste log vào chat. Review ghi vào cuối file log của người được review, dưới mục
`## Review — <người review> (<ngày>)`.

---

## 1. Ba quyết định đã chốt (22/10, nhóm tự quyết vì thầy bận) — đừng bàn lại

Nguồn đầy đủ: `docs/roadmap.md` mục 4, dòng **D8**.

1. **Role chọn lúc đăng ký.** `RegisterRequest` thêm trường `role` **tùy chọn**: chỉ nhận `user` hoặc
   `creator`, mặc định `user`, gửi `admin` thì **400**. Admin vẫn chỉ tạo qua SQL. An toàn vì agent
   của creator vẫn phải qua admin duyệt. Không làm luồng thu phí hay nút nâng cấp sau: user muốn
   thành creator thì tạo tài khoản mới.
2. **System prompt riêng của agent** theo mô hình *Claude Project*: cột mới **`agents.instructions`**
   (Flyway V3). `introduction` giữ vai trò mô tả công khai trên chợ. **`instructions` chỉ trả về cho
   chủ agent và admin**, không bao giờ trả cho người mua hay trang công khai.
3. **Đính kèm file vào agent = RAG**, Should-have, **không làm tuần này**. Bảng
   `knowledge_bases` / `kb_chunks` đã có sẵn trong V1, chưa có entity.

**Về phần đánh giá, đọc một chỗ trước khi ai hỏi:** kết luận chọn LiteLLM **đổi theo ngưỡng chất
lượng** (đặt 85% thì ra Bifrost, 90% thì ra Portkey), nhưng ngưỡng 80% đã khóa từ commit đầu tiên
`9d6dfd7` (11/09), hơn 5 tuần trước kết quả. Bảng đầy đủ ở `docs/experiment-results.md` mục 7.6.

---

## 2. Việc của Hùng (Auth + Agent + cấu hình proxy)

### H1 — Role lúc đăng ký (làm trước, nhỏ)
- **Backend:** `dto/auth/RegisterRequest.java` (thêm `role`, validate chỉ `user`/`creator`),
  `service/AuthService.register()` (gán role; nhớ `admin` → 400 chứ không âm thầm hạ về `user`).
- **Frontend:** `app/(auth)/register/page.tsx` + `context/auth-context.tsx` (hàm `register` nhận
  thêm `role`): lựa chọn "Mua agent" / "Tạo agent". Sau đăng ký vẫn đi qua `homePathForRole()`.
  Style theo `docs/design-system.md`, class CSS thuần.
- **Hợp đồng:** `docs/openapi.json` → `RegisterRequest` (thêm `role`, enum `user`/`creator`, không
  bắt buộc).
- **Test:** `backend-gateway/scripts/e2e_test.sh` — thay bước nâng creator bằng SQL (dòng ~120–127)
  bằng đăng ký `role=creator`; thêm ca `role=admin` → 400 và ca bỏ trống → `user`.
- **Tương thích:** script nâng role bằng SQL (`run_experiment.py:236`, `e2e_workflow_test.sh:56`)
  vẫn chạy được, đừng xóa.
- **Đạt khi:** `e2e_test.sh` pass (số check tăng lên), đăng ký creator vào được `/dashboard`.

### H2 — Trường `instructions` của agent (sau H1; Khoa đợi cái này cho K1)
- **DB:** `db/migration/V3__add_agent_instructions.sql` (`ALTER TABLE agents ADD COLUMN instructions
  text`). **Không** dùng `ddl-auto`. Cập nhật `docs/erd.dbml`.
- **Backend:** `domain/Agent.java`; `dto/agent/CreateAgentRequest`, `UpdateAgentRequest` (thêm
  `instructions`, tùy chọn); `AgentResponse`.
- **ABAC — chỗ dễ sai nhất:** `GET /agents` và `GET /agents/{id}` là `permitAll`
  (`SecurityConfig.java:57`) và hiện dùng chung `AgentResponse`. Phải **không điền `instructions`**
  (`@JsonInclude(NON_NULL)` hoặc DTO riêng) trừ khi người gọi là chủ agent hoặc admin →
  `AgentController.getById` cần nhận principal tùy chọn. Danh sách `GET /agents` (chợ công khai)
  **không bao giờ** trả `instructions`.
- **Frontend:** `components/agent-form.tsx` (ô "Hướng dẫn cho agent", `textarea`), trang edit,
  `app/(app)/admin/agents/page.tsx` (admin thấy để duyệt), `lib/api/types.ts`.
- **Hợp đồng:** `docs/openapi.json` (Agent, CreateAgentRequest, UpdateAgentRequest).
- **Test:** người mua gọi `GET /agents/{id}` **không** thấy `instructions`; chủ agent và admin thấy;
  người lạ không đăng nhập không thấy. Thêm vào `e2e_test.sh`.
- **Đạt khi:** `e2e_test.sh` và `e2e_workflow_test.sh` pass; không có đường nào lộ `instructions`.

### H3 — Bật `fallbacks` cho LiteLLM và chạy lại phép thử sự cố
- **Cấu hình:** `proxy-configs/litellm/config.yaml`, thêm fallback cho nhóm `conduit-pool` sang
  Anthropic/Gemini. Log hiện còn báo `Available Model Group Fallbacks=None`.
- **Kiểm hồi quy (đã đăng ký trong D15):** `bash experiments/scripts/fault_injection.sh` — **45 lượt,
  ~$0,01, dùng model rẻ → vẫn phải xin Hùng xác nhận trước khi chạy** (CLAUDE.md mục 2: trên 10 lượt).
  Kết quả ghi **bổ sung** vào mục "Phép thử tiêm lỗi" của `docs/experiment-results.md`, không sửa số cũ.
- **Cảnh giác:** chưa chắc LiteLLM failover khi lỗi là 401 (key sai) chứ không phải 5xx. Nếu vẫn
  0/15 thì ghi nguyên văn, đó là một kết quả, và thử thêm loại lỗi khác (vd. timeout) trước khi kết luận.
- **Đạt khi:** có kết quả mới, dù tốt hay không, kèm nhận xét.

### H4 — Hai việc đối chiếu cuối cho phần đánh giá (cần máy Hùng)
- **Đếm `routing_decisions`:** bật Docker + Postgres, đếm dòng theo `proxy_name` trong 19–20/10, so
  với 720 + 45. `CLAUDE.md` mục 2 bắt buộc mọi lượt ghi vào bảng này. Lệch thì **ghi rõ vào
  `experiment-results.md` mục 13**, không chạy lại gì.
- **Đối chiếu chi phí:** tổng ~$0,36 của 19–20/10 với dashboard OpenAI và Anthropic. Lệch thì tính
  lại offline từ `model_pricing`; kết luận chỉ đổi nếu giá sai lệch hơn ~4,5 lần.

---

## 3. Việc của Khoa (Credit + Chat + Payment)

### K1 — Chèn `instructions` làm system prompt (làm **sau H2**)
- `service/ChatService.doSendMessage()` (dòng ~92): nếu agent có `instructions` khác rỗng thì thêm
  `new ChatTurn("system", instructions)` **đầu danh sách** `turns`. Cập nhật chú thích
  `adapter/ChatTurn.java` (role hiện chỉ ghi `user | assistant`).
- **Không được làm lệch định tuyến Portkey:** `HttpProxyChatClient.promptLength()` chỉ đếm tin nhắn
  `user` cuối, nên lượt `system` không ảnh hưởng. Giữ nguyên hành vi đó và có test.
- **Test:** rỗng/`null` → không có lượt system; có → lượt đầu là system; `promptLength()` không đổi.
- **Cảnh giác:** `instructions` tốn token mỗi lượt và tính vào credit của người dùng. Ghi nhận xét
  vào log nếu thấy chi phí/lượt tăng đáng kể.
- **Đạt khi:** agent có `instructions` trả lời theo vai; agent không có thì request y hệt trước.

### K2 — Lấp khoảng trống ghi log lỗi
- Thực nghiệm cho thấy **0/32 lượt lỗi ghi được thông điệp lỗi** (`experiment-results.md` mục 9, và
  phép thử D15). Truy nguyên nhân: `ChatService.emitError` / `recordFailedTurn` không lưu, hay
  `run_experiment.py` không ghi trường `error` vào file kết quả. Sửa chỗ đúng.
- **Đạt khi:** một lượt lỗi giả lập (key sai) để lại thông điệp đọc được trong `usage_logs` hoặc file
  kết quả.

### K3 — Test trừ credit đồng thời (Must-have, hiện chưa có gì bảo vệ)
- Ràng buộc bắt buộc ở `CLAUDE.md` mục 4: *mọi deduction chạy trong transaction với row-level lock
  hoặc optimistic version*. Cơ chế có (`@Version` ở `domain/CreditWallet.java:38`) nhưng **chưa có
  test nào chứng minh**; hiện `src/test` chỉ có 4 file, không file nào về credit.
- Viết test: ví có N credit, bắn nhiều lượt trừ song song → **số dư không bao giờ âm**, tổng trừ
  đúng, lượt thua `@Version` được retry hoặc từ chối sạch, không trừ hụt.
- **Đạt khi:** test tự động chạy được bằng `./mvnw test`, và **fail** nếu cố tình bỏ `@Version`
  (chứng minh test có tác dụng).

### K4 — CI GitHub Actions
- `.github/workflows/` chưa tồn tại. Workflow: build backend + `./mvnw test` +
  `python -m unittest discover -s experiments/tests`. Lint frontend nếu chạy được trong thời gian
  hợp lý. Script e2e cần Docker nên để sau.
- **Đạt khi:** CI xanh trên một PR thử.

---

## 4. Thứ tự và phụ thuộc

```
H1 ──► H2 ──► K1          (K1 cần cột V3 của H2)
H3, H4, K2, K3, K4        (độc lập, làm song song)
```

Việc tốn token thật: **chỉ H3** (~45 lượt). `e2e_workflow_test.sh` gọi LLM thật ít nhất 1 lượt mỗi
lần chạy, **đừng chạy lặp**. Kiểm thử chức năng dùng model rẻ hoặc mock.

## 5. Review chéo

- **Khoa review H1–H2** (H2 đổi API agent mà chat phụ thuộc; riêng điểm ABAC về `instructions` cần
  mắt thứ hai).
- **Hùng review K1–K3** (riêng K3: tự tay thử phá `@Version` xem test có fail không).

## 6. Bẫy môi trường (bổ sung cho `CLAUDE.md`)

- **Docker Desktop phải bật trước** khi chạy bất cứ script nào dùng Postgres/proxy. Máy sập thì
  container tắt hết (đã gặp 20/10): `docker compose up -d`, rồi
  `python experiments/scripts/preflight.py` (miễn phí) để chắc cấu hình proxy còn nguyên.
- `docker compose stop` (không `down -v`): `bifrost-data` chứa cấu hình Complexity Router, mất thì
  phải chạy lại `proxy-configs/bifrost/complexity-setup.sh`.
- Backend không đọc `.env`: export `LITELLM_MASTER_KEY` trước `./mvnw spring-boot:run`.
- Port host Redis là `26379`; backend ở `8081` với context-path `/api` (`8080` là Bifrost).

## 7. Checklist cuối tuần

- [ ] H1: đăng ký chọn được role, `e2e_test.sh` pass
- [ ] H2: `instructions` hoạt động, test chứng minh người mua không thấy
- [ ] H3: fallbacks bật, đã chạy lại D15 và ghi kết quả (tốt hay không)
- [ ] H4: số dòng `routing_decisions` và đối chiếu chi phí đã ghi vào `experiment-results.md` mục 13
- [ ] K1: system prompt vào chat, không lệch `promptLength()`
- [ ] K2: lượt lỗi để lại thông điệp
- [ ] K3: test trừ credit đồng thời, fail khi bỏ `@Version`
- [ ] K4: CI xanh
- [ ] Hai bên review chéo xong, ghi vào cuối `log-*.md`

## 8. Nhật ký cuối tuần (điền Chủ nhật 25/10)

_(Mỗi người ghi vào `log-hung.md` / `log-khoa.md`; mục này chỉ để tổng kết.)_
