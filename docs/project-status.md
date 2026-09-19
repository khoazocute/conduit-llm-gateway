# Conduit — Tổng kết tiến độ (Hùng & Khoa)

Cập nhật: **2026-09-19**. Trạng thái code: `main` = `e8d2bfd` (đã gồm PR #1 của Khoa); branch `lhung` = `78de497` (làm thêm sau khi pull, **chưa push**).

Tài liệu này chỉ ghi những gì đã kiểm chứng được trong repo (git, contract, code, kết quả chạy test). Chỗ nào chưa kiểm chứng hoặc chưa làm thì nói rõ là chưa.

---

## 1. Tóm tắt một đoạn

Hai vertical Must-have (Hùng: Auth+Agent, Khoa: Credit+Chat+Payment) đều đã có backend + frontend chạy được và ghép được với nhau: creator tạo agent → admin duyệt → user mua bằng Mock Payment → webhook cộng credit → chat qua LiteLLM với Gemini thật → trừ credit và ghi `usage_logs`/`routing_decisions`. Toàn bộ luồng này có test tự động (48 + 42 check) và đã được test tay trên UI.

**Chưa làm — và là phần quyết định của khóa luận:** thực nghiệm đánh giá 3 proxy. Hệ thống (testbed) đã sẵn sàng, nhưng bộ chạy thực nghiệm mới là khung rỗng, chưa cấu hình routing thật cho từng proxy, chưa có API key cho đủ 5 model, và bảng giá `model_pricing` đang trống nên chưa tính được chi phí thật.

---

## 2. Tiến độ theo phạm vi (MoSCoW trong `CLAUDE.md` mục 6)

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Sàn agent dạng text (publish/unpublish, tìm kiếm cơ bản) | ✅ Xong | Tìm theo `q`; unpublish → resubmit được |
| Kiểm duyệt agent từ Admin | ✅ Xong | approve / reject kèm lý do |
| Gateway kết nối OpenAI + Anthropic | ⚠️ Một phần | Gọi qua LiteLLM; **mới chạy thật với Gemini** (key OpenAI/Anthropic trong `.env` vẫn là placeholder) |
| Credit wallet (ghi nhận/trừ theo giao dịch) | ✅ Xong | Optimistic lock, ledger `credit_transactions` |
| Mock Payment Gateway end-to-end | ✅ Xong | Webhook ký HMAC, idempotent; test chữ ký sai + callback trùng |
| **Triển khai + đánh giá 3 proxy** | ❌ **Chưa bắt đầu phần thực nghiệm** | Xem mục 5 — đây là việc không được trễ |
| RAG cơ bản | ❌ Chưa (Should-have) | `ai-service` mới là khung FastAPI 8 dòng; contract có 3 endpoint Knowledge Base |
| VNPay sandbox | ❌ Chưa (Should-have) | `payment_method=vnpay` hiện bị từ chối có chủ đích |
| Fallback sang Gemini / Image generation / Widget / Rating | ❌ Chưa (Should-have) | — |

So với kế hoạch 16 tuần: cả hai vertical của tuần 2–5 đã xong. Phần lớn hạng mục ghi ở tuần 11–12 (Mock Payment, ví credit, admin API key/markup/duyệt agent) đã có bản dùng được từ sớm. Các mốc tuần 6–8 (chuẩn bị + setup proxy) đang dở, tuần 9–10 chưa bắt đầu.

---

## 3. Đã làm được gì

### 3.1 Nền tảng chung (làm trước khi chia vertical)
- Monorepo: `backend-gateway` (Spring Boot 3.5.6, Java 21), `frontend` (Next.js 16 + React 19 + Tailwind v4), `ai-service` (khung), `proxy-configs`, `experiments`, `docs`.
- `docker-compose`: 6 container — Postgres+pgvector, pgAdmin, Redis, LiteLLM (`v1.83.14-stable`, đã tránh bản dính supply chain attack), Bifrost, Portkey.
- Flyway migration `V1` (14 bảng, gồm cả bảng RAG) + `V2`; JPA entity/repository cho toàn bộ bảng Must-have.
- **Contract `docs/openapi.json`: 40 endpoint** (Auth 4, Users 2, Agents 7, Admin-Agents 3, Admin-Users 2, Wallet 2, Purchases & Payment 5, Chat 5, Admin API Keys 4, Admin Model Pricing 3, Knowledge Base 3 — nhóm cuối là Should-have).

### 3.2 Hùng — vertical Auth + Agent
**Backend**
- JWT: access token 20 phút + refresh token trong HttpOnly cookie; refresh token **thu hồi được qua Redis** (1 phiên/user), verify chặn sai thuật toán/sai loại token.
- Auth API (register/login/refresh/logout) — register tạo cả `User` lẫn `CreditWallet` trong 1 transaction. Logout chạy được kể cả khi access token đã hết hạn.
- Agent API với ABAC (kiểm tra `creator_id`) và state machine `draft → pending → published/rejected → unpublished`, `unpublished` gửi lại duyệt được.
- Admin API: duyệt/từ chối agent; quản lý user có **tìm kiếm, phân trang, sắp xếp mới nhất trước**, admin không tự ban chính mình.
- `GET /purchases` (thư viện agent đã mua) — thêm sau khi test tay, nằm trong vùng của Khoa nên cần báo Khoa.

**Frontend** (theme dev-console tối, class CSS thuần; xem `docs/design-system.md`)
- Login/register, marketplace (tìm kiếm, phân trang), chi tiết agent, dashboard creator (tạo/sửa/submit/unpublish/resubmit), admin (duyệt agent, người dùng), My library. UI đổi theo role: buyer chỉ thấy agent đã mua, `/dashboard` chỉ cho creator/admin.

### 3.3 Khoa — vertical Credit + Chat + Payment (đã merge qua PR #1)
- Ví credit + ledger; mua agent qua Mock Payment với webhook HMAC `X-Webhook-Signature`, idempotent theo `transaction_ref`; agent miễn phí cộng credit ngay.
- Lớp adapter gọi proxy (`ProxyChatClient`, `HttpProxyChatClient`); chat **streaming SSE** với ABAC (chỉ chủ sở hữu hội thoại/người đã mua).
- Billing đúng nguyên tắc: chỉ tính khi có usage thật; lượt lỗi ghi `usage_logs.status=error`, **không trừ credit**; trừ credit + ghi `usage_logs` + `routing_decisions` trong cùng 1 transaction.
- `AesGcmCipher` cho API key thượng nguồn; admin API key + model pricing (có kiểm soát chuyển trạng thái).
- Frontend: ví, trang chat, mua agent + nút giả lập thanh toán, admin API key, admin model pricing.

### 3.4 Làm chung / tích hợp (2026-09-19)
- Pull code Khoa, chạy workflow xuyên 2 vertical và **sửa 2 lỗi tầng Auth ảnh hưởng SSE** của Khoa: filter JWT phải chạy cả trên ASYNC dispatch (nếu không stream bị cắt/401) và không re-authorize ERROR dispatch (nếu không lỗi validation bị che thành 401).
- Test tay theo checklist trên UI → phát hiện và sửa: lỗi logout khi token hết hạn, buyer nhìn thấy giao diện creator, `/admin/users` không hiện hết user, thiếu trang thư viện.
- Chốt bộ 30 prompt đánh giá (`docs/eval-prompts.md`).

---

## 4. Kiểm thử và chất lượng

| Loại | Số liệu | Ở đâu |
|---|---|---|
| E2E Auth + Agent + Admin | **48 check, pass** | `backend-gateway/scripts/e2e_test.sh` |
| E2E workflow xuyên 2 vertical (mua → webhook → chat) | **42 check, pass** | `backend-gateway/scripts/e2e_workflow_test.sh` |
| Unit test | `JwtServiceTest` 4 test + 1 test nạp context, pass | `backend-gateway/src/test` |
| Frontend | `tsc`, `eslint`, `next build` sạch (14 route) | `frontend/` |

**Security acceptance test tối thiểu (`CLAUDE.md` mục 7):**

| Yêu cầu | Trạng thái |
|---|---|
| Webhook sai chữ ký bị từ chối (400) | ✅ có test |
| Duplicate callback không cộng credit 2 lần | ✅ có test (ledger chỉ 1 dòng `purchase_grant`) |
| JWT hết hạn / bị giả mạo bị chặn | ✅ có unit test |
| Refresh token bị thu hồi sau logout | ✅ có test |
| Chat lỗi provider không bị trừ credit | ✅ có test |
| Tenant isolation `kb_chunks` (creator A không thấy của B) | ⬜ chưa — phụ thuộc RAG |
| Prompt injection qua nội dung RAG | ⬜ chưa — phụ thuộc RAG |

Còn thiếu ở mảng test: chưa có unit/integration test cho các service (`AuthService`, `AgentService`, `PurchaseService`, `ChatService`…), chưa có load test (k6/Locust), **chưa có CI** (không có `.github/`).

---

## 5. Chưa làm — theo thứ tự ưu tiên

### 5.1 Đường găng: thực nghiệm đánh giá 3 proxy (tuần 6–10)
Bộ 30 prompt đã chốt nhưng **các hạ tầng để chạy nó còn thiếu**:

1. **Chuyển bộ prompt sang dạng máy đọc được.** `experiments/prompts/prompts.json` hiện là 3 mảng rỗng; nội dung thật đang nằm ở `docs/eval-prompts.md`. Cần chuyển sang đúng schema trong `experiments/prompts/SCHEMA.md` (kèm `expected_answer` + `match_type`).
2. **Viết runner thật.** `experiments/scripts/run_experiment.py` mới là khung "chưa gọi API thật"; `analysis/decision_rule.py` (124 dòng) cần được kiểm chứng với dữ liệu thật.
3. **Cấu hình routing thật cho từng proxy** (hiện đều là khung): LiteLLM đang `simple-shuffle`, Bifrost/Portkey chỉ có file tham khảo. Portkey cần rule conditional routing; Bifrost cần cấu hình import qua API/UI; **chưa cấu hình fallback ở proxy nào** (log LiteLLM: `Fallbacks=None`).
4. **Đủ API key cho pool 5 model** (GPT-4o-mini, Gemini Flash, Claude Haiku, GPT-4o, Claude Sonnet): hiện chỉ có key Gemini thật. Nên kiểm tra lại tên model trong `proxy-configs/litellm/config.yaml` còn dùng được không.
5. **Seed `model_pricing`.** Bảng đang **0 dòng** → `cost_upstream` và `predicted_cost` ghi ra bằng 0, trong khi chi phí trung bình/prompt là tiêu chí số 2 của luật quyết định. Không có bước này thì thực nghiệm không so sánh được chi phí.
6. **Đường ghi log cho thực nghiệm.** `ChatService` đã ghi `routing_decisions` cho mỗi lượt chat, nhưng đang cố định `active-proxy: litellm`; cần cơ chế chạy qua cả 3 proxy và ghi `response_quality_score`.
7. Rubric chấm mù + bảng chấm chi tiết (đã có nguyên tắc, chưa dựng bảng); chọn 30% mẫu cho 2 người chấm.
8. Chạy 30 × 3 proxy × 3 lần = 270 lượt, áp luật quyết định, chọn proxy chính thức.

Lưu ý khi đo: Gemini Flash bản miễn phí có lúc trả 503 và latency đo được tới ~36 giây cho một câu ngắn (tốn token suy luận) — cần tính đến khi so p95 latency giữa các proxy.

### 5.2 Must-have còn lại và hoàn thiện
- Tích hợp proxy được chọn vào Conduit thay cho cấu hình tĩnh hiện tại.
- Test tự động cho tầng service, load test, CI/CD (GitHub Actions), deploy (Railway/Render hoặc AWS/GCP), báo cáo và demo (tuần 14–16).

### 5.3 Should-have (chỉ làm khi Must-have ổn)
RAG (pgvector, chunking, retrieval + 2 test bảo mật còn thiếu ở trên), VNPay sandbox, fallback Gemini qua Provider Adapter, image generation, widget iframe, dashboard doanh thu, rating/comment.

---

## 6. Vấn đề mở cần nhóm quyết định

1. **Nâng role lên creator:** chưa có API/cơ chế; hiện phải sửa tay `users.role` qua SQL/pgAdmin. Nên hỏi GVHD trước khi thêm.
2. **System prompt của agent:** `introduction` không được gửi cho model, nên agent trả lời chung chung và dài (tốn credit — khoảng 1 credit/token ×1.5). Cần quyết định nguồn system prompt (ERD hiện chỉ có `introduction`).
3. **Fallback:** failover là đối tượng thực nghiệm giữa các proxy, nên chưa thêm vào backend; khi cấu hình proxy ở tuần 7–8 cần thống nhất cách cấu hình cho công bằng giữa 3 proxy.
4. **`api_keys` (admin) chưa dùng trong đường chat:** key nhà cung cấp hiện nằm ở env của container proxy, còn bảng `api_keys` (0 dòng) chưa được đọc. Cần thống nhất chỗ giữ key thật (theo `CLAUDE.md` mục 7 là mã hóa AES-GCM, key mã hóa ngoài DB).
5. **Đã thêm endpoint `GET /purchases` và tham số `q` cho `/admin/users`** — cần Khoa xem lại vì nằm trong/gần vùng của Khoa; `docs/openapi.json` đã cập nhật.
6. **Quy ước git:** làm trên branch cá nhân (`lhung`, `dangkhoa`), merge `main` qua PR; không thêm dòng `Co-Authored-By: Claude` vào commit/PR (đã ghi trong `CLAUDE.md`). Các commit cũ đã nằm trên `main` vẫn còn dòng đó — không sửa vì đã public.
7. Bảo mật thực hành: key Gemini đã bị dán vào khung chat trong quá trình làm việc → nên tạo key mới và thu hồi key cũ.

---

## 7. Nhật ký ngắn (theo git)

| Ngày | Sự kiện |
|---|---|
| 2026-09-11 | Khởi tạo repo; scaffold monorepo; OpenAPI contract; phân vai Hùng = Auth+Agent, Khoa = Credit+Chat+Payment; Flyway schema đầy đủ |
| 2026-09-12 | JPA entity + repository cho toàn bộ bảng; pgAdmin; hướng dẫn setup; checklist cho vertical Hùng |
| 2026-09-13 | Hùng: backend Auth + Agent + Admin (JWT/Redis), 40 check E2E pass |
| 2026-09-14 | Hùng: frontend Auth+Agent + theme; sửa lỗ hổng unpublished không quay lại được |
| 2026-09-18 | Khoa: vertical Credit + Chat + Payment, merge PR #1 vào `main` |
| 2026-09-19 | Hùng: pull, tích hợp, sửa lỗi SSE/logout, UI theo role, thư viện agent, test workflow (48 + 42 check), chốt 30 prompt |

---

## 8. Chạy lại và kiểm tra nhanh

```bash
docker compose up -d                       # Docker Desktop phải đang chạy
cd backend-gateway
LITELLM_MASTER_KEY=<giá trị trong .env> ./mvnw spring-boot:run   # Spring không đọc .env, phải export biến này
cd ../frontend && npm run dev              # http://localhost:3000

bash backend-gateway/scripts/e2e_test.sh            # Auth + Agent + Admin
bash backend-gateway/scripts/e2e_workflow_test.sh   # xuyên 2 vertical (chat thật cần key Gemini hợp lệ trong .env)
```

Các "bẫy" khi chạy local (port Redis `26379`, encoding tiếng Việt với `curl` trên Windows, xóa `.next` khi đổi cấu trúc route…) được ghi trong `CLAUDE.md` mục 8.
