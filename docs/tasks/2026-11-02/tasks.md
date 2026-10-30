# Tuần 2026-11-02 → 2026-11-08 — việc được giao

**Phase F đã xong** (merge `main` 30/10, CI xanh). Tuần này bắt đầu **Phase G**: Should-have, deploy,
báo cáo, demo. Tracker: Notion "KLTN (26 - 27)" → Task Tracking (TASK-57 → 63, thêm TASK-69 → 71).

Quy ước giữ nguyên: mỗi người ghi `log-hung.md` / `log-khoa.md` trong folder này, commit kèm sản
phẩm. Review ghi vào cuối file log của người được review, dưới mục `## Review — <người review> (<ngày>)`.

---

## 1. Lịch Phase G — kéo sớm 1 tuần so với tracker

| Mốc | Hạn cũ (tracker) | **Hạn mới** |
|---|---|---|
| RAG, VNPay, kiểm lại fallback (TASK-57, 59, 60) | 22/11 | **15/11** |
| Test bảo mật RAG (TASK-58) | 22/11 | **15/11** |
| Deploy (TASK-61) | 29/11 | **22/11** |
| Báo cáo khóa luận — bản nháp đầy đủ (TASK-62) | 06/12 | **29/11** |
| Demo đầu-cuối (TASK-63) | 13/12 | **06/12** |

⚠️ **Các hạn này vẫn là ước lượng**: chưa có ngày nộp và ngày bảo vệ thật (TASK-69). Có ngày thật thì
chỉnh lại bảng này trước tiên.

**Báo cáo bắt đầu ngay tuần này, không đợi xong code.** Đây là khối việc lớn nhất còn lại, và chương quan
trọng nhất (thực nghiệm) đã gần như có sẵn trong `docs/experiment-design.md` + `docs/experiment-results.md`.

---

## 2. Bảng việc tuần này

| Task | Việc | Người | Review | Phụ thuộc | Hạn |
|---|---|---|---|---|---|
| TASK-69 | Hỏi lịch nộp báo cáo và bảo vệ thật | Hùng | — | — | 03/11 |
| TASK-62a | Thống nhất dàn ý báo cáo + chia chương | Cả hai | — | — | 03/11 |
| TASK-59a | Tách lớp **Payment Adapter** khỏi `PurchaseService` (Mock chạy y hệt) | Hùng | Khoa | — | 04/11 |
| TASK-57a | RAG phần 1: nạp tài liệu → chia đoạn → embedding → `kb_chunks` | Khoa | Hùng | — | 06/11 |
| TASK-60 | Kiểm lại fallback qua Provider Adapter: có cần làm thêm không | Khoa | Hùng | — | 04/11 |
| TASK-70 | Ghi `usage_logs` khi trừ credit bỏ cuộc sau 8 lần xung đột | Khoa | Hùng | — | 04/11 |
| TASK-61a | Dockerfile backend + frontend, chạy thử bản deploy ở 1 nơi | Hùng | Khoa | — | 07/11 |
| TASK-59b | VNPay sandbox qua adapter: tạo URL thanh toán, IPN có chữ ký, idempotent | Hùng | Khoa | 59a | 08/11 |
| TASK-62b | Viết chương **Thực nghiệm** (bản nháp) | Hùng | Khoa | 62a | 08/11 |
| TASK-62c | Viết phần **Credit + Chat + Payment** và **Kiểm thử** của chương hệ thống (bản nháp) | Khoa | Hùng | 62a | 08/11 |
| TASK-71 | Làm mới `CLAUDE.md` (số check, trạng thái đã cũ) | Hùng | — | — | 03/11 |
| TASK-68 | Bước cuối: lọc dashboard Anthropic theo model | Hùng | — | — | 01/11 |

Tuần sau (09–15/11): RAG phần 2 (truy hồi + đưa vào chat, TASK-57b), test bảo mật RAG (TASK-58), VNPay
xong, deploy ổn định.

## 3. Hai người có phải chờ nhau không

**Không có chỗ chờ thật trong tuần này.** Hai điểm cần phối hợp:
- **TASK-59a sửa `PurchaseService` — code của Khoa.** Hùng làm trên `lhung`, Khoa review trước khi merge.
  Khoa **không sửa** `PurchaseService` tuần này (TASK-70 nằm ở `ChatService`) để khỏi xung đột.
- **TASK-62a (dàn ý) làm chung, đầu tuần**, vì hai chương viết song song phải theo cùng một khung.

---

## 4. Việc của Hùng

### TASK-69 — Lịch thật (làm đầu tiên)
Hỏi khoa/GVHD ngày nộp báo cáo, ngày bảo vệ, yêu cầu định dạng (mẫu Word/LaTeX, số trang). Ghi vào
`docs/roadmap.md` và chỉnh bảng mục 1 nếu cần.

### TASK-59a — Payment Adapter
- Hiện `PurchaseService.createPurchase` có nhánh `if (method == vnpay) throw "not implemented"`, và logic
  Mock (tạo `transaction_ref`, kiểm chữ ký HMAC webhook) nằm thẳng trong service.
- Tách interface `PaymentAdapter` (tạo giao dịch, xác thực callback, trả kết quả) + `MockPaymentAdapter`
  giữ **y nguyên hành vi hiện tại**. CLAUDE.md mục 3: VNPay phải cắm vào **cùng lớp adapter**, không sửa
  phần còn lại.
- **Đạt khi:** `e2e_workflow_test.sh` (chữ ký sai bị 400, callback trùng không cộng 2 lần) và
  `PurchaseServiceTest` của Khoa vẫn pass nguyên. Không chạy lặp `e2e_workflow_test.sh` (gọi LLM thật).

### TASK-59b — VNPay sandbox
- Cần **tài khoản sandbox VNPay** (mã TMN + hash secret) — Hùng đăng ký, để trong `.env`, không commit.
- Tạo URL thanh toán, trang return, **IPN** xác thực chữ ký (HMAC-SHA512 theo tài liệu VNPay),
  idempotent theo `transaction_ref` UNIQUE, ghi `payment_webhook_logs` mọi lần gọi kể cả bị từ chối.
- **Test:** chữ ký sai bị từ chối, IPN gọi lại không cộng credit lần 2 — cùng bộ tiêu chí với Mock.
- **Đạt khi:** mua agent bằng VNPay sandbox từ đầu đến cuối, credit cộng đúng 1 lần.

### TASK-61a — Đóng gói và thử deploy
- Chưa có Dockerfile nào. Viết `backend-gateway/Dockerfile`, `frontend/Dockerfile`, và một
  `docker-compose.prod.yml` chỉ gồm thứ cần cho bản chính thức: backend, frontend, Postgres+pgvector,
  Redis, **LiteLLM** (Bifrost/Portkey chỉ phục vụ thí nghiệm, không cần deploy).
- Thử deploy ở **một** nơi (Railway / Render / VPS). Ghi chi phí hosting dự kiến.
- ⚠️ **Chi phí hosting chưa có quyết định** (D1 chỉ nói API key) → nêu số tiền, Hùng chốt thành **D17**.
- **Đạt khi:** đăng nhập và xem chợ agent được trên URL công khai. Chat qua LLM để tuần sau.

### TASK-62b — Chương Thực nghiệm (bản nháp)
- Nguồn: `docs/experiment-design.md`, `docs/experiment-results.md`, `docs/benchmark-survey.md`.
- Phải có: câu hỏi nghiên cứu, 3 proxy và cơ chế, bộ đề + metric theo paper, luật quyết định khóa
  trước (kèm bằng chứng commit `9d6dfd7`), kết quả, độ vững (leave-one-out, theo ngưỡng — mục 7.6), phép
  thử sự cố, giới hạn.
- Viết **để Khoa đọc hiểu được mà không cần đọc chat** — Khoa phải trả lời được câu hỏi phản biện về phần này.

### TASK-71 — Làm mới CLAUDE.md
Số check (`e2e_test.sh` 66, không phải 40), trạng thái các vertical, mục D2 cũ (đã thay bằng Design Y).

---

## 5. Việc của Khoa

### TASK-60 — Kiểm lại fallback (nhỏ, làm đầu)
TASK-51 đã cho LiteLLM `fallbacks: conduit-pool → [claude-haiku, gemini-flash]` + `retry_policy` (D16),
phục hồi 15/15. Đối chiếu với 2 yêu cầu trong CLAUDE.md: Should-have "Fallback sang Gemini" và mục 5
"cross-provider fallback bắt buộc qua Provider Adapter". Nếu đã đủ → ghi lý do vào log và **đóng task**.
Chỉ làm thêm nếu thấy thiếu thật.

### TASK-70 — Không để mất dấu chi phí khi trừ credit bỏ cuộc
Đề nghị đã thống nhất ở review tuần trước: quá 8 lần xung đột ví thì vẫn ghi một dòng `usage_logs`
`status=error` kèm `cost_upstream` (CLAUDE.md mục 5: không tính cho user nhưng phải ghi log riêng).
**Test:** giả lập 8 lần xung đột → có dòng `usage_logs`, ví không bị trừ.

### TASK-57a — RAG phần 1: nạp tài liệu
- `ai-service/` mới có `/health`. Bảng `knowledge_bases`, `kb_chunks` (`embedding vector(1536)`) có sẵn
  trong V1, **chưa có entity**.
- Luồng: creator tải file (PDF/TXT) cho agent của mình → chia đoạn → embedding → ghi `kb_chunks` kèm
  `agent_id`. 1536 chiều khớp `text-embedding-3-small`.
- **ABAC:** chỉ chủ agent tải và xem được tài liệu của agent đó.
- ⚠️ **Embedding gọi API có phí** (rẻ, nhưng vẫn theo D1): dùng tài liệu nhỏ; đợt nào > 10 lượt thì báo Hùng trước.
- **Đạt khi:** tải 1 file nhỏ → thấy các đoạn trong `kb_chunks` đúng `agent_id`.
- Phần 2 (tuần sau): truy hồi top-k theo `agent_id`, đưa vào chat dưới dạng **"ngữ cảnh tham khảo"**,
  không phải chỉ thị hệ thống (CLAUDE.md mục 7) + 2 test bảo mật (TASK-58).

### TASK-62c — Chương hệ thống (phần của Khoa) + Kiểm thử
Ví credit và optimistic lock, chat SSE qua proxy, billing 3 tầng (usage → credit qua `model_pricing`),
Mock Payment. Kiểm thử: unit test, test đồng thời (kèm phép thử bỏ `@Version`), load test và **phát hiện C**.

---

## 6. Việc chung

### TASK-62a — Dàn ý báo cáo (đầu tuần, ngồi chung)
Đề xuất khung (chỉnh theo mẫu của khoa khi có TASK-69):

1. Giới thiệu: bài toán, đóng góp (**chỉ** phần đánh giá proxy), phạm vi
2. Cơ sở lý thuyết: LLM gateway, routing proxy, 3 proxy được đánh giá, benchmark
3. Hệ thống Conduit (testbed): kiến trúc, dữ liệu, bảo mật — Hùng: Auth + Agent; Khoa: Credit + Chat + Payment
4. **Thực nghiệm** — Hùng viết, Khoa phản biện
5. Kiểm thử — Khoa viết, Hùng phản biện
6. Kết luận, giới hạn, hướng phát triển

Mỗi người đọc chéo chương của người kia: cả hai phải trả lời được phản biện về toàn bộ.

---

## 7. Chi phí

Theo D1. Dự kiến tuần này: vài lượt embedding (TASK-57a), không có đợt gọi LLM lớn nào. Hosting
(TASK-61a): **chưa có quyết định**, nêu số tiền trước khi trả.

## 8. Checklist hạn 08/11

- [ ] TASK-69 có lịch thật, bảng mục 1 đã chỉnh
- [ ] TASK-62a dàn ý chốt
- [ ] TASK-59a adapter, Mock y nguyên, test cũ pass
- [ ] TASK-60 đóng hoặc có lý do làm tiếp
- [ ] TASK-70 có test
- [ ] TASK-57a tài liệu vào `kb_chunks` đúng `agent_id`
- [ ] TASK-61a mở được trên URL công khai
- [ ] TASK-59b mua agent bằng VNPay sandbox
- [ ] TASK-62b, 62c bản nháp
- [ ] TASK-71 CLAUDE.md làm mới
- [ ] Review chéo ghi vào cuối `log-*.md`
