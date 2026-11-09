# 2026-11-09 → 2026-11-27 — kế hoạch đến hạn nộp bản nháp báo cáo

**Mốc thật: nộp bản nháp báo cáo khóa luận ngày 27/11/2026** (D19). Ngày bảo vệ chưa có. Đến 27/11,
**báo cáo là việc chính**; code chỉ làm những gì báo cáo cần kể. Tracker: Notion "KLTN (26 - 27)" →
Task Tracking.

Tuần 02/11 không được giao thực tế (tin nhắn chưa gửi Khoa) nên không có tiến triển; mọi việc của tuần
đó chuyển sang đây với hạn mới. Quyết định mới, nhóm tự chốt vì GVHD bận: **D18, D19, D20** —
`docs/roadmap.md` mục 4.

Quy ước giữ nguyên: log ghi vào `log-hung.md` / `log-khoa.md` trong folder tuần (tuần này là folder
này; thứ Hai 16/11 và 23/11 tạo folder mới, chỉ chép phần còn lại). Review ghi cuối file log của người
được review, dưới `## Review — <người review> (<ngày>)`.

---

## 1. Thay đổi so với kế hoạch tuần 02/11

| Việc | Trước | **Nay** | Lý do |
|---|---|---|---|
| Bản nháp báo cáo | 29/11 (ước lượng) | **27/11 (lịch thật)** | D19 |
| VNPay sandbox (TASK-59) | Should-have, hạn 15/11 | **Could-have, sau 27/11** | Mock Payment đã đủ Must-have, VNPay không góp gì cho phần đánh giá |
| Deploy (TASK-61) | 22/11 | **Sau 27/11** | Không cần cho bản nháp; chốt D17 trước |
| Baseline một model (D18) | — | **Mới: TASK-72** | Trả lời câu hỏi "định tuyến có đáng tiền hơn chọn cứng một model không" |
| Trang admin hiển thị routing | — | **Mới: TASK-73** | Lúc demo thấy được phần đóng góp chính |
| RAG (TASK-57, 58) | 15/11 | **Giữ, có điểm cắt 14/11** | Nạp tài liệu chưa xong 14/11 → cắt RAG khỏi bản nháp, ghi vào hướng phát triển |

## 2. Bảng việc

| Task | Việc | Người | Review | Phụ thuộc | Hạn |
|---|---|---|---|---|---|
| TASK-71 | Làm mới `CLAUDE.md` + roadmap theo D18–D20 | Hùng | — | — | ✅ 09/11 |
| TASK-68 | Bước cuối: lọc dashboard Anthropic theo model | Hùng | — | — | 10/11 |
| TASK-62a | **Dàn ý báo cáo theo mẫu của khoa**, chia chương | Cả hai | — | mẫu của khoa | 11/11 |
| TASK-60 | Kiểm lại fallback: đủ yêu cầu chưa, đủ thì đóng | Khoa | Hùng | — | 11/11 |
| TASK-70 | Ghi `usage_logs` khi trừ credit bỏ cuộc sau 8 lần xung đột | Khoa | Hùng | — | 11/11 |
| TASK-72 | **Baseline một model (D18):** chạy 240 lượt, đường biên Pareto, cận trên | Hùng | Khoa | Hùng xác nhận chi phí | chạy 12/11, kết quả 14/11 |
| TASK-57a | RAG phần 1: nạp tài liệu → chia đoạn → embedding → `kb_chunks` | Khoa | Hùng | — | **14/11 (điểm cắt)** |
| TASK-73 | Trang admin hiển thị routing | Hùng | Khoa | — | 19/11 |
| TASK-57b | RAG phần 2: truy hồi top-k theo `agent_id`, đưa vào chat làm "ngữ cảnh tham khảo" | Khoa | Hùng | 57a | 19/11 |
| TASK-58 | 2 test bảo mật RAG: tenant isolation, prompt injection | Khoa | Hùng | 57b | 20/11 |
| TASK-62b | Viết: Giới thiệu, **Thực nghiệm** (theo D20, gồm D18), Hệ thống phần Auth+Agent, Kết luận | Hùng | Khoa | 62a, 72 | 21/11 |
| TASK-62c | Viết: Hệ thống phần Credit+Chat+Payment (+RAG), **Kiểm thử** | Khoa | Hùng | 62a | 21/11 |
| TASK-62d | Đọc chéo toàn bộ, ghép một bản, sửa | Cả hai | — | 62b, 62c | 22–26/11 |
| — | **Nộp bản nháp** | Cả hai | — | 62d | **27/11** |

Sau 27/11: TASK-61 deploy (chốt D17 trước), TASK-63 demo, TASK-59 VNPay (Could-have) nếu còn thời gian,
TASK-69 khi có ngày bảo vệ.

## 3. Lịch theo tuần

- **09–15/11:** dàn ý chốt sớm nhất có thể (chương nào ai viết, theo mẫu khoa). Hùng chạy D18 và ghi
  kết quả. Khoa đóng TASK-60/70, làm RAG phần 1. **14/11: quyết RAG có vào bản nháp không.**
- **16–22/11:** viết chương là chính. Hùng làm TASK-73 xen kẽ. Khoa RAG phần 2 + test bảo mật. 21/11
  mỗi người có bản nháp các chương của mình.
- **23–27/11:** đọc chéo, ghép, sửa, nộp. Không thêm tính năng mới trong tuần này.

## 4. Hai người có phải chờ nhau không

- **Dàn ý (TASK-62a) là chỗ chờ duy nhất của phần viết**: hai người viết song song phải theo cùng khung.
  Làm sớm nhất có thể.
- TASK-72, TASK-73 (Hùng) và RAG (Khoa) không đụng code của nhau. TASK-73 thêm endpoint đọc trong khu
  admin và có thể sửa `docs/openapi.json`: ai merge sau thì xử lý xung đột.
- Chương Thực nghiệm (Hùng) cần số của TASK-72 → chạy D18 sớm, đầu tuần.

---

## 5. Việc của Hùng

### TASK-72 — Baseline một model (D18)
Đăng ký trước đầy đủ ở `docs/roadmap.md` D18 — **làm đúng như đã ghi, không đổi thiết kế khi đang làm**.
- Chạy qua app như D3, proxy `litellm`, `CHAT_DEFAULT_MODEL` lần lượt `gpt-4o-mini` / `claude-haiku` /
  `gpt-4o`, 80 item × 1 lần, `--out-dir` riêng. Không cần code mới cho đường gọi (alias có sẵn trong
  LiteLLM, `fallbacks` chỉ gắn với `conduit-pool`).
- Phân tích: độ chính xác, chi phí TB/lượt, chi phí/câu đạt cho 6 điểm (3 proxy + 3 baseline), đường
  biên Pareto, cận trên lý thuyết; biểu đồ chi phí–chính xác cho báo cáo.
- Kiểm: nhánh `gpt-4o-mini` so từng item với kết quả đa số của LiteLLM trong 720 lượt; lệch > 4/80 thì
  báo cáo con số lệch.
- ⚠️ **240 lượt, có `gpt-4o`, ≈ $0,20 → xác nhận trước khi chạy (D1).** Kết quả ghi **bổ sung** vào
  `docs/experiment-results.md`, không sửa số cũ, không chọn lại proxy.

### TASK-73 — Trang admin hiển thị routing
- Endpoint admin chỉ đọc, tổng hợp `routing_decisions` + `usage_logs` theo khoảng thời gian: tỷ lệ model
  được chọn, tổng chi phí thượng nguồn, chi phí nếu mọi lượt dùng `gpt-4o` (tính theo `model_pricing`),
  số lượt có fallback (model trả lời khác model định tuyến ban đầu), số lượt lỗi.
- Trang `/admin/routing` theo `docs/design-system.md`. Không gọi LLM.
- **Đạt khi:** có test cho phép tổng hợp (dữ liệu giả), non-admin bị 403, trang hiển thị đúng số trên
  dữ liệu thật của thí nghiệm.

### TASK-62b — Các chương của Hùng
- **Thực nghiệm** trình bày theo **D20**: (1) quy trình đánh giá tái lập, (2) kết quả + độ vững +
  baseline D18, (3) các phát hiện vận hành. Phải có: luật khóa trước (commit `9d6dfd7`), giả thuyết
  đăng ký trước và chỗ sai, D14 quyết sau khi thấy 360 lượt (kèm 5 ràng buộc), D15 phép thử sự cố, giới
  hạn (CI95 chứa 80%, kết luận đổi ở ngưỡng 85%).
- Nguồn: `docs/experiment-design.md`, `docs/experiment-results.md`, `docs/benchmark-survey.md`,
  `docs/reports/2026-11-01-bao-cao-tien-do.*` (bảng và biểu đồ dùng lại được).
- Viết **để Khoa đọc hiểu được mà không cần đọc chat** — Khoa phải trả lời được phản biện về phần này.

## 6. Việc của Khoa

### TASK-60, TASK-70 — làm đầu, nhỏ
Nội dung giữ nguyên như `docs/tasks/2026-11-02/tasks.md` mục 5 (TASK-60 đủ thì ghi lý do và đóng;
TASK-70 có test giả lập 8 lần xung đột).

### TASK-57a/57b, TASK-58 — RAG
Nội dung như tuần 02/11 mục 5, thêm:
- **Điểm cắt 14/11:** chưa nạp được 1 file nhỏ vào `kb_chunks` đúng `agent_id` thì dừng RAG, báo Hùng,
  chuyển sức sang chương Kiểm thử; RAG ghi vào hướng phát triển.
- Embedding có tính phí: dùng file nhỏ; đợt nào > 10 lượt thì báo Hùng trước (D1).
- Test bảo mật bắt buộc (CLAUDE.md mục 7): creator A không truy hồi được `kb_chunks` của B; nội dung
  RAG được đánh dấu là ngữ cảnh tham khảo, không phải chỉ thị.

### TASK-62c — Các chương của Khoa
Hệ thống phần Credit+Chat+Payment (ví và optimistic lock, chat SSE qua proxy, billing 3 tầng usage →
credit qua `model_pricing`, Mock Payment, RAG nếu qua điểm cắt) và chương **Kiểm thử** (unit, test đồng
thời kèm phép thử bỏ `@Version`, mutation test bảo mật, load test và phát hiện C, CI).

---

## 7. Chi phí

Theo D1. Đợt có phí: **TASK-72 ≈ $0,20 (240 lượt, có `gpt-4o`) — cần xác nhận**; embedding RAG (nhỏ).
Không chạy lặp `e2e_workflow_test.sh`. Hosting: chưa phát sinh (deploy sau 27/11).

## 8. Checklist

- [x] TASK-71 CLAUDE.md, roadmap (D18–D20) — 09/11
- [ ] TASK-68 đóng — 10/11
- [ ] TASK-62a dàn ý theo mẫu khoa — 11/11
- [ ] TASK-60, TASK-70 — 11/11
- [ ] TASK-72 chạy + phân tích + ghi `experiment-results.md` — 14/11
- [ ] Quyết RAG vào bản nháp hay không — 14/11
- [ ] TASK-73, TASK-57b, TASK-58 — 19–20/11
- [ ] TASK-62b, 62c bản nháp từng người — 21/11
- [ ] Đọc chéo, ghép, sửa — 26/11
- [ ] **Nộp bản nháp — 27/11**
