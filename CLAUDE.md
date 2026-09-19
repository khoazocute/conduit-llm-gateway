# CLAUDE.md — Conduit: LLM Gateway Portal & AI Agent Marketplace

Khóa luận tốt nghiệp UIT. Sinh viên: Nguyễn Văn Lê Hùng (23520570), Võ Đăng Khoa (23520758). GVHD: TS. Nguyễn Thanh Bình, ThS. Trần Vĩnh Khiêm.

**Đọc file này TRƯỚC khi viết bất kỳ code nào.** Nó thay thế việc phải giải thích lại context mỗi phiên.

---

## 1. Đề tài là gì, và đóng góp chính là gì

Conduit là một LLM Gateway Portal kiêm sàn AI Agent Marketplace cho thị trường Việt Nam. Nhưng **hệ thống Conduit không phải là đóng góp khoa học** — nó là testbed. Đóng góp khoa học duy nhất của khóa luận là:

> **Đánh giá thực nghiệm và lựa chọn 1 trong 3 routing proxy mã nguồn mở (LiteLLM, Bifrost, Portkey AI Gateway) để tích hợp vào Conduit, dựa trên thí nghiệm có kiểm soát và một quy tắc quyết định đã khóa trước khi chạy.**

Mọi phần khác của hệ thống (marketplace, credit wallet, ABAC, RAG, thanh toán...) tồn tại **để phần đánh giá proxy có môi trường thật để chạy và kiểm chứng**, không phải để tự thân là đóng góp.

**Nguyên tắc kỷ luật scope quan trọng nhất:** nếu một task không giúp phần đánh giá proxy chạy được hoặc không thuộc vòng nghiệp vụ khép kín tối thiểu (tạo agent → mua agent → chat qua proxy → trừ credit), nó thuộc Should-have/Could-have, không phải việc làm ngay.

### Hướng đã bị BỎ — không được làm lại
Đề tài từng có 2 phiên bản trước:
1. V1: Marketplace/SaaS đa nhà cung cấp là đóng góp chính — bị đánh giá là dàn trải, không có điểm nhấn kỹ thuật.
2. V2 (đã bỏ hẳn): Tự nghiên cứu thuật toán routing, train Matrix Factorization + Classifier, so sánh với RouteLLM/RouterBench. **Thầy Bình đã bác bỏ hướng này vì quá sâu so với khóa luận đại học.**

Nếu thấy bất kỳ tài liệu/code cũ nào nhắc đến RouterBench, RouteLLM, Matrix Factorization, "Gap #1/#2", train classifier riêng — đó là tàn dư của hướng đã bỏ, KHÔNG đưa vào code.

---

## 2. Thiết kế thí nghiệm đánh giá proxy (phần quan trọng nhất, làm đúng ngay từ đầu)

- **3 proxy đánh giá:** LiteLLM (Python, cost/latency/usage-based routing), Bifrost — Maxim AI (Go, load balancing + automatic failover), Portkey AI Gateway bản OSS (TypeScript, conditional/rule-based routing).
- **LiteLLM dùng bản ≥ v1.83.0** (bản v1.82.7, v1.82.8 dính supply chain attack tháng 3/2026, đã bị gỡ). Pin cụ thể `v1.83.14-stable` (tag dạng `vX.Y.Z-stable`, không phải `vX.Y.Z` trần — GHCR không publish tag trần cho các bản gần đây).
- **Pool 5 model, chia 2 tầng chi phí** để tạo tình huống cost-quality thật sự phải đánh đổi (không chỉ dùng model rẻ ngang giá nhau):
  - Tầng rẻ: GPT-4o-mini, Gemini Flash
  - Tầng trung: Claude Haiku
  - Tầng đắt: GPT-4o, Claude Sonnet
- **Bộ 30 prompt cố định**, phân tầng 4 loại: 12 closed-QA (có đáp án đúng/sai — kiến thức, toán, logic), 6 code, 12 mở (email, tóm tắt, sáng tạo). **Đã chốt, xem `docs/eval-prompts.md`** (đủ nội dung prompt + đáp án đúng cho closed-QA) — không sửa nội dung file này nữa khi đã bắt đầu chạy thực nghiệm tuần 9–10.
- **Mỗi prompt chạy 3 lần trên mỗi proxy** → 30 × 3 proxy × 3 lần = 270 lượt gọi API thật. Mục đích: đo tỷ lệ nhất quán (consistency rate) của quyết định routing, không chỉ đo giá trị trung bình.
- **Chấm chất lượng:**
  - Closed-QA: đúng/sai khách quan, tự động hóa được (so đáp án).
  - Prompt mở: rubric 3 tiêu chí (on-task / độ dài phù hợp / không lỗi), mỗi tiêu chí 0–1 điểm, **chấm mù** (ẩn tên proxy), 30% mẫu được 2 người chấm độc lập để báo cáo % agreement.
- **Quy tắc quyết định chọn proxy (khóa trước khi chạy, thứ tự ưu tiên):**
  1. Loại proxy có tỷ lệ đúng closed-QA < 80%.
  2. Trong số còn lại, chọn proxy có chi phí trung bình/prompt thấp nhất.
  3. Nếu chênh lệch chi phí < 5%, ưu tiên proxy có p95 latency thấp hơn.
  4. Nếu vẫn hòa, ưu tiên proxy có consistency rate cao hơn qua 3 lần lặp.
- Mọi lượt gọi phải ghi vào bảng `routing_decisions` (xem ERD ở mục 4) để có dữ liệu phân tích sau này — đây là input trực tiếp cho báo cáo khóa luận, không được bỏ qua logging dù đang ở giai đoạn thử nghiệm nhanh.

---

## 3. Tech stack (đã chốt, không đổi trừ khi có lý do kỹ thuật rõ ràng)

| Thành phần | Công nghệ |
|---|---|
| Frontend Portal | Next.js + React + TailwindCSS |
| Backend Gateway | Spring Boot 3 (`3.5.6` cụ thể — `start.spring.io` đã ngừng hỗ trợ sinh project Boot 3.x, `backend-gateway/pom.xml` viết tay), Spring AI, Spring Security (JWT), Spring WebFlux (streaming SSE) |
| DB Migration | Flyway (`backend-gateway/src/main/resources/db/migration/`) — schema tạo qua migration, KHÔNG dùng `ddl-auto: update`/`create` |
| AI Service (Should-have — RAG) | Python + FastAPI |
| Database | PostgreSQL + pgvector |
| DB UI (dev) | pgAdmin (docker-compose service `pgadmin`, `localhost:5050`) — dùng để xem bảng/query nhanh, không phải thành phần deploy production |
| Cache | Redis (JWT session, rate limit counters) |
| Object Storage | S3-compatible |
| CI/CD | GitHub Actions |
| Containerization | Docker Compose (dev), Railway/Render hoặc AWS/GCP (deploy) |
| Load testing | k6 hoặc Locust |

**LLM providers (Must-have):** OpenAI, Anthropic. Google Gemini chỉ dùng cho fallback (Should-have).
**Payment:** Mock Payment Gateway tự dựng (Must-have, bắt buộc chạy được độc lập). VNPay sandbox (Should-have, nâng cấp qua cùng lớp Payment Adapter, không sửa code còn lại). **Không làm MoMo** (ngoài phạm vi — yêu cầu hồ sơ pháp nhân doanh nghiệp).

---

## 4. Data model — quy ước đặt tên (đọc kỹ, đây là chỗ hay lẫn)

**ERD chính thức:** `docs/erd.dbml` (bản gốc từ proposal). **API contract chính thức:** `docs/openapi.json` (OpenAPI 3.0.3, thống nhất giữa 2 người trước khi code — sai số cho phép ±3 endpoint). Bảng liệt kê dưới đây chỉ tóm tắt nhanh, `erd.dbml` mới là nguồn đúng khi có sai khác. JPA entity + repository cho toàn bộ bảng Must-have đã có sẵn ở `backend-gateway/src/main/java/com/conduit/backendgateway/domain/` — đừng viết lại, chỉ thêm service/controller lên trên.

- Đơn vị nội bộ luôn gọi là **`credit`**, KHÔNG bao giờ dùng `token` cho tên bảng/biến/API field. Lý do: tránh nhầm với token nghĩa kỹ thuật (token của LLM). Bảng: `credit_wallets`, `credit_transactions` — không phải `token_wallets`.
- Ba tầng hạch toán, phải giữ tách biệt trong code:
  1. **Usage thượng nguồn**: đơn vị thật nhà cung cấp trả về (token input/output cho text; số lượng+độ phân giải cho ảnh).
  2. **Credit nội bộ**: đơn vị hiển thị cho User trong ví.
  3. **Bảng tỷ giá quy đổi** (`model_pricing`): quy tắc chuyển usage → credit, riêng theo provider/model. Công thức text: `credit = ceil(token_upstream × 1.5)` — markup 50% trên chi phí thượng nguồn, **tương đương lợi nhuận biên 33.3% trên giá bán** (không phải 50% — hai đại lượng khác gốc, đừng viết nhầm trong báo cáo hay comment code).

### Các bảng chính (phạm vi Must-have)
```
users(id, email, password_hash, full_name, role, status, ...)
agents(id, creator_id, title, introduction, agent_type, price_vnd, default_credit_granted, status, ...)
knowledge_bases(id, agent_id, file_name, file_url, status)      -- Should-have (RAG)
kb_chunks(id, knowledge_base_id, agent_id, chunk_text, embedding vector(1536), ...)  -- Should-have
credit_wallets(id, user_id UNIQUE, balance, updated_at)
credit_transactions(id, wallet_id, type, amount, related_message_id, related_purchase_id, ...)
agent_purchases(id, user_id, agent_id, amount_vnd, payment_method, payment_status, transaction_ref UNIQUE, ...)
payment_webhook_logs(id, transaction_ref, result, raw_payload, received_at)
conversations(id, user_id, agent_id, ...)
messages(id, conversation_id, role, content, credit_charged, model_used, latency_ms, ...)
api_keys(id, provider, key_encrypted, status, priority, ...)
usage_logs(id, message_id, api_key_id, provider, model, token_input, token_output, cost_upstream, revenue_credit, latency_ms, status, ...)
model_pricing(id, provider, model, unit_type, price_usd_per_unit, credit_markup_multiplier, effective_from, ...)
routing_decisions(id, message_id, proxy_name, selected_model, predicted_cost, token_input, token_output, response_quality_score, latency_ms, ...)
```

Ràng buộc bắt buộc: `credit_wallets.user_id` UNIQUE; `agent_purchases.transaction_ref` UNIQUE; mọi deduction credit chạy trong transaction với row-level lock hoặc optimistic version (tránh số dư âm khi có concurrent request).

---

## 5. Quyết định kiến trúc đã chốt (đừng tự ý đổi)

- **Không chuyển đổi provider giữa chừng khi đang streaming** (SSE) — rủi ro ghép nội dung lỗi. Nếu provider chính lỗi giữa stream, kết thúc phiên đó là failed/partial theo policy đã định, không cố switch sang provider khác cùng lúc.
- **Mọi LLM API đều stateless** — Gateway phải tự resend toàn bộ mảng `messages` mỗi request; không có state phía provider.
- **Cross-provider fallback bắt buộc qua Provider Adapter** — không gọi thẳng SDK của từng provider trong business logic; mọi lời gọi LLM đi qua lớp adapter chuẩn hóa request/response.
- **Billing chỉ tính khi có usage thật từ provider trả về** — không tính credit cho lượt gọi lỗi/retry không thành công, dù vẫn phát sinh chi phí thượng nguồn (ghi log riêng, không cộng vào giao dịch của User).
- **ABAC, không chỉ RBAC:** mọi request thao tác agent phải kiểm tra đồng thời vai trò + quyền sở hữu (creator_id khớp) + trạng thái ví (đủ credit) khi cần.

---

## 6. Phạm vi (MoSCoW) — bám sát khi ước lượng effort

**Must-have:**
- Sàn agent dạng text (publish/unpublish, tìm kiếm cơ bản)
- Gateway kết nối tối thiểu OpenAI + Anthropic
- Credit wallet (ghi nhận/trừ theo giao dịch)
- **Triển khai + đánh giá 3 proxy theo thiết kế ở mục 2** — đây là việc không được trễ
- Kiểm duyệt agent từ Admin
- Mock Payment Gateway end-to-end (webhook giả lập, idempotent, cộng credit đúng)

**Should-have (chỉ làm sau khi Must-have ổn định):**
- RAG cơ bản (pgvector, chunking, retrieval)
- VNPay sandbox (nâng cấp từ Mock qua cùng Payment Adapter)
- Fallback sang Gemini
- Image generation (DALL-E 3) — kiến trúc Image Adapter thiết kế song song Text Adapter nhưng triển khai sau
- Widget iframe, dashboard doanh thu, rating/comment

**Could-have:** Re-ranking RAG bằng cross-encoder. (BYOK và semantic caching đã bị loại khỏi phạm vi hoàn toàn — không triển khai dưới bất kỳ hình thức nào.)

**Ngoài phạm vi:** video generation, MoMo, production-scale.

---

## 7. Bảo mật — các cơ chế bắt buộc có kèm test, không chỉ thiết kế trên giấy

- API key thượng nguồn: mã hóa AES-GCM, encryption key tách khỏi DB (biến môi trường), không log ra dạng rõ.
- Webhook thanh toán: xác thực chữ ký, idempotency theo `transaction_ref` UNIQUE, audit log mọi lần gọi kể cả bị từ chối.
- Prompt injection: đánh dấu rõ nội dung RAG là "ngữ cảnh tham khảo" trong prompt, không phải chỉ thị hệ thống; có bộ test case cơ bản.
- JWT: access token ngắn hạn (15–30 phút) + refresh token; ưu tiên HttpOnly cookie; kiểm tra thuật toán ký khi verify.
- SQL: chỉ dùng Spring Data JPA parameterized query; native query bắt buộc `@Param`.
- **Security acceptance test tối thiểu cần có:** tenant isolation (creator A không truy hồi được `kb_chunks` của B), webhook chữ ký sai bị từ chối, duplicate callback không cộng credit 2 lần, JWT hết hạn bị chặn.

---

## 8. Kế hoạch 16 tuần (mốc quan trọng nhất: Tuần 9–10 là thực nghiệm proxy — không được trễ)

**Phân công đã đổi so với bản gốc bên dưới:** thay vì chia theo mảng (1 người toàn bộ backend, 1 người toàn bộ frontend — sợ backend quá nặng cho 1 người), chia theo **vertical dọc theo tính năng**, mỗi người tự làm cả backend lẫn frontend cho phần của mình:
- **Hùng — Auth + Agent:** entity `users`/`agents`, JWT, CRUD agent + luồng duyệt draft→pending→published/rejected, admin quản lý user/agent; frontend: login/register, sàn agent, trang creator, trang admin duyệt agent. Tag OpenAPI: `Auth`, `Users`, `Agents`, `Admin - Agents`, `Admin - Users`.
- **Khoa — Credit + Chat + Payment:** entity `credit_wallets`/`credit_transactions`/`agent_purchases`/`payment_webhook_logs`/`conversations`/`messages`/`api_keys`/`model_pricing`, Provider Adapter (OpenAI/Anthropic), credit wallet (optimistic lock), webhook mock; frontend: ví credit, luồng mua agent, chat streaming SSE, admin API key/bảng giá. Tag OpenAPI: `Wallet`, `Purchases & Payment`, `Conversations & Chat`, `Admin - API Keys`, `Admin - Model Pricing`.

Đã dựng xong trước (không tính vào tuần của ai riêng): docker-compose 6 container (Postgres+pgvector, pgAdmin, Redis, 3 proxy) verify chạy được; Flyway migration full schema (`V1`, `V2`) verify Hibernate validate pass; JPA entity + repository cho toàn bộ 12 bảng Must-have (cả 2 vertical) — mỗi người chỉ cần viết service/controller/frontend. Hướng dẫn setup từng bước (bao gồm cách xem bảng qua pgAdmin) nằm ở README.md, không lặp lại ở đây.

**Vertical Auth+Agent (Hùng) — ĐÃ XONG cả backend lẫn frontend, đã push `main` (commit `52b42ff`):**
- Backend: JWT (access + refresh token revocable qua Redis, 1 session/user), `SecurityConfig`/`JwtService`/`JwtAuthenticationFilter`, Auth API, Agent API (ABAC + state machine `draft→pending→published/rejected→unpublished`, **`unpublished` submit lại được về `pending`** — fix gap ban đầu), Admin API. Test tự động: `backend-gateway/scripts/e2e_test.sh` (40 check, chạy pass) + `JwtServiceTest` unit test.
- Frontend: Next.js 16 (route group `(app)`/`(auth)`), login/register, marketplace, creator dashboard, admin (duyệt agent/user). Style dùng chung: theme dev-console dark, class CSS thuần (không dùng thư viện component nào — tránh lỗi `render`-prop từng gặp với shadcn/Base UI) — **xem `docs/design-system.md` trước khi làm UI mới, kể cả vertical Khoa**, nguồn thật nằm ở `frontend/app/globals.css`.
- Lưu ý hạ tầng: port host của Redis trong `docker-compose.yml` là `26379` (không phải 6379 mặc định, Windows/Hyper-V hay đổi dải cổng bị loại trừ theo thời gian — nếu lại đụng port, đổi sang port khác và cập nhật `application.yml` theo).
- Gap còn biết nhưng chưa xử lý: chưa có API cho user tự nâng cấp role → creator (phải sửa tay qua SQL/pgAdmin lúc test) — cân nhắc hỏi GVHD trước khi thêm field `role` vào `PATCH /admin/users/{id}/status` hay tạo cơ chế riêng.

**Vertical Credit+Chat+Payment (Khoa) — ĐÃ MERGE vào `main` (PR #1, `e8d2bfd`), Hùng đã pull về và test workflow xuyên 2 vertical (2026-09-19):**
- Có: ví credit + ledger, mua agent qua Mock Payment (webhook HMAC `X-Webhook-Signature`, idempotent), chat SSE qua proxy (`ChatService`/`HttpProxyChatClient`, proxy đang chọn tĩnh `app.chat.active-proxy: litellm` — routing thật là việc tuần 9–10), `AesGcmCipher` cho API key, admin API key + model pricing; frontend: `/wallet`, `/agents/[id]/chat`, `/admin/api-keys`, `/admin/model-pricing`, nút mua agent.
- Test workflow: `backend-gateway/scripts/e2e_workflow_test.sh` (34 check: creator tạo agent → admin duyệt → user mua → webhook sai/thiếu chữ ký bị 400 → webhook đúng cộng credit → **callback trùng không cộng lần 2** → mở chat → provider lỗi báo qua SSE và **không trừ credit**). Kèm `scripts/e2e_test.sh` (40 check, Auth+Agent) — cả hai phải pass trước khi merge.
- **Chưa test được chat thành công thật:** `.env` chỉ có API key placeholder (`sk-...changeme`) nên upstream trả "API key not valid" — nhánh lỗi đã test, nhánh thành công (có usage → trừ credit → ghi `usage_logs`/`routing_decisions`) cần key thật, chưa chạy.
- Logout phải chạy được **kể cả khi access token đã hết hạn** (`/auth/**` là permitAll nên `principal` có thể null → trước đây NPE 500 và cookie refresh còn sống, phiên tự sống lại khi tải lại trang). Nay `AuthService.logout(userId, refreshToken)` nhận diện phiên bằng refresh cookie, luôn thu hồi trên Redis, luôn xoá cookie, trả 204 idempotent; frontend `logout()` không ném lỗi và chuyển về `/login`. Có test hồi quy trong `e2e_test.sh`. `GlobalExceptionHandler.handleUnexpected` giờ log stack trace (trước đây 500 bị nuốt im lặng).
- 2 lỗi đã sửa khi test (thuộc tầng Auth của Hùng, ảnh hưởng SSE của Khoa): (1) `JwtAuthenticationFilter` phải chạy cả trên ASYNC dispatch (`shouldNotFilterAsyncDispatch()=false`) — nếu không, khi `SseEmitter` kết thúc, stream bị cắt/401; (2) `SecurityConfig` cho phép ERROR dispatch (`dispatcherTypeMatchers(DispatcherType.ERROR).permitAll()`) — nếu không, lỗi validation trên endpoint `text/event-stream` (vd. `content` rỗng) bị che thành 401 thay vì 400.

**Bẫy môi trường khi chạy local (đã gặp thật):**
- Spring Boot **không đọc file `.env`**. Backend chỉ thấy biến môi trường của shell chạy nó. Nếu không export `LITELLM_MASTER_KEY` (giá trị trong `.env`) trước khi `./mvnw spring-boot:run`, backend dùng default `sk-1234` ≠ key của container LiteLLM → chat lỗi `No connected db`. Chạy: `LITELLM_MASTER_KEY=<giá trị trong .env> ./mvnw spring-boot:run`.
- Trên Windows/git-bash, gửi body chứa tiếng Việt bằng `curl -d "..."` làm hỏng encoding → gửi qua file: `curl --data-binary @file.json -H "Content-Type: application/json; charset=utf-8"`.
- Docker Desktop phải chạy trước `docker compose up -d` (lỗi `dockerDesktopLinuxEngine` = chưa bật).
- Khi đổi cấu trúc route Next.js (route group) mà dev server báo 404 sai: `rm -rf frontend/.next` rồi chạy lại.
- Lint frontend có rule React Compiler mới (`react-hooks/set-state-in-effect`, `react-hooks/purity`) — với fetch-on-mount/nhãn theo giờ hiện tại hợp lệ, dùng `eslint-disable-next-line` kèm 1 dòng giải thích lý do.

**Quy ước làm việc với git:** Hùng làm trên branch **`lhung`**, Khoa trên `dangkhoa`; merge vào `main` qua PR. Không commit thẳng lên `main`. Chỉ push khi Hùng xác nhận. **Không thêm dòng `Co-Authored-By: Claude` (hay bất kỳ attribution/"Generated with Claude Code" nào) vào commit message hoặc mô tả PR** — quy tắc của Hùng, ưu tiên hơn gợi ý mặc định của công cụ.

| Tuần | Việc | Phụ trách |
|---|---|---|
| 1 | ERD (`docs/erd.dbml`) + OpenAPI contract (`docs/openapi.json`) | Hùng & Khoa (joint) — ✅ xong |
| 2–5 | Vertical Auth+Agent (backend + frontend) | Hùng — ✅ xong, đã push `main` |
| 2–5 | Vertical Credit+Chat+Payment (backend + frontend) | Khoa — ✅ đã merge `main`, workflow xuyên 2 vertical đã test (chat thành công thật còn chờ API key thật) |
| 6–7 | Chuẩn bị thực nghiệm: chốt 30 prompt, viết rubric, bảng chấm mù | Hùng & Khoa — 30 prompt ✅ đã chốt (`docs/eval-prompts.md`); rubric chấm mù & bảng chấm chi tiết còn cần dựng |
| 7–8 | Setup hạ tầng 3 proxy (deploy, cấu hình pool 5 model, logging vào `routing_decisions`) | Hùng (infra Docker đã xong, routing strategy thật + logging còn phụ thuộc backend) |
| **9–10** | **Chạy thực nghiệm: mỗi người 15 prompt × 3 proxy × 3 lần trên phần của mình. Tổng hợp, áp dụng quy tắc quyết định, chọn proxy chính thức.** | **Hùng & Khoa (JOINT)** |
| 11 | Mock Payment Gateway, webhook, dashboard ví credit | Hùng & Khoa |
| 12 | Admin panel (API key, markup, duyệt agent) | Hùng & Khoa |
| 13 | (Should-have nếu kịp) RAG / VNPay / image gen | Khoa |
| 14 | Testing: unit, integration, security acceptance, load test k6 | Hùng & Khoa |
| 15–16 | Deploy, viết báo cáo, demo | Hùng & Khoa |

---

## 9. Thuật ngữ chuẩn (dùng nhất quán trong code, comment, commit message)

| Dùng | Không dùng |
|---|---|
| credit, credit_wallets, credit_transactions | token (cho đơn vị nội bộ), token_wallets |
| Creator | Vendor/Vender |
| gói combo | packet |
| VNPay sandbox / Mock Payment Gateway | MoMo (không triển khai) |
| Proxy: litellm / bifrost / portkey (giá trị cột `proxy_name`) | tên viết hoa/khác không nhất quán |

---

## 10. Khi không chắc, hỏi lại theo thứ tự ưu tiên này
1. Việc này có phục vụ phần đánh giá proxy hoặc vòng nghiệp vụ Must-have tối thiểu không? Nếu không → khoan làm.
2. Có ràng buộc kiến trúc nào ở mục 5 bị vi phạm không?
3. Tên bảng/biến có theo đúng quy ước ở mục 9 không?
