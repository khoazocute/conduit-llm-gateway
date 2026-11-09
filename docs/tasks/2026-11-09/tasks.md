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
| TASK-62a | Thống nhất các mục phải **đổi nội dung** so với bản draft (mục 8.2): danh sách RQ, 3.4.3, 3.5.2, 5.2.6–5.2.7, Phụ lục A/B | Cả hai | — | — | 11/11 |
| TASK-60 | Kiểm lại fallback: đủ yêu cầu chưa, đủ thì đóng | Khoa | Hùng | — | 11/11 |
| TASK-70 | Ghi `usage_logs` khi trừ credit bỏ cuộc sau 8 lần xung đột | Khoa | Hùng | — | 11/11 |
| TASK-72 | **Baseline một model (D18):** chạy 240 lượt, đường biên Pareto, cận trên | Hùng | Khoa | Hùng xác nhận chi phí | chạy 12/11, kết quả 14/11 |
| TASK-57a | RAG phần 1: nạp tài liệu → chia đoạn → embedding → `kb_chunks` | Khoa | Hùng | — | **14/11 (điểm cắt)** |
| TASK-73 | Trang admin hiển thị routing | Hùng | Khoa | — | 19/11 |
| TASK-57b | RAG phần 2: truy hồi top-k theo `agent_id`, đưa vào chat làm "ngữ cảnh tham khảo" | Khoa | Hùng | 57a | 19/11 |
| TASK-58 | 2 test bảo mật RAG: tenant isolation, prompt injection | Khoa | Hùng | 57b | 20/11 |
| TASK-62b | Viết các mục **Hùng** phụ trách theo bản draft (mục 8.1) | Hùng | Khoa | 62a, 72 | đợt 1: 16/11 · đủ: 21/11 |
| TASK-62c | Viết các mục **Khoa** phụ trách theo bản draft (mục 8.1) | Khoa | Hùng | 62a | đợt 1: 16/11 · đủ: 21/11 |
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

### TASK-62b — Phần viết của Hùng
Danh sách mục ở **mục 8.1**. Chú ý riêng: 5.2.6 (baseline D18) và 5.2.7 (phép thử sự cố) là mục **mới**,
Hùng viết; 6.2 Đóng góp viết theo **D20**.

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

### TASK-62c — Phần viết của Khoa
Danh sách mục ở **mục 8.1**. Chú ý riêng: các mục phương pháp thí nghiệm (3.3–3.6) và kết quả
(5.2.2, 5.2.3, 5.2.5) **phải viết theo thiết kế đã chạy thật** (Design Y, 4 benchmark, 720 lượt), không
theo bản draft cũ — xem mục 8.2.

---

## 7. Chi phí

Theo D1. Đợt có phí: **TASK-72 ≈ $0,20 (240 lượt, có `gpt-4o`) — cần xác nhận**; embedding RAG (nhỏ).
Không chạy lặp `e2e_workflow_test.sh`. Hosting: chưa phát sinh (deploy sau 27/11).

## 8. Phân công viết báo cáo

Theo đúng cách Khoa đã chia trong bản draft (`docs/reports/Draft_KLTN.docx.md`, phần "Phân công và theo
dõi tiến độ" + dòng "Phụ trách" của từng mục). Bản làm việc chung: Google Doc của nhóm (Hùng giữ link).
Định dạng theo Phụ lục 2 đã cài sẵn trong file; sửa phần của người kia thì bật theo dõi thay đổi.

### 8.1. Ai viết mục nào

| Chương | Hùng | Khoa |
|---|---|---|
| Tóm tắt, Lời cảm ơn | cùng viết, **viết sau cùng** (24–25/11) | cùng viết |
| 1. Mở đầu | — | **toàn chương** (1.1–1.7) |
| 2. Tổng quan | — | **toàn chương** (2.1–2.6) |
| 3. Cơ sở lý thuyết & phương pháp | 3.1.1–3.1.3, 3.1.5–3.1.6, 3.2, **3.4.2**, 3.7, 3.8 | 3.1.4, **3.3, 3.4.1, 3.4.3, 3.4.4, 3.5, 3.6** |
| 4. Phân tích, thiết kế | 4.3, 4.4.1–4.4.3, 4.4.5–4.4.7, 4.5 | 4.1, 4.2, 4.4.4, 4.4.8 |
| 5. Hiện thực & đánh giá | 5.1.1–5.1.3, 5.1.5, 5.1.7, **5.2.1, 5.2.4, 5.2.6 (mới), 5.2.7 (mới)**, 5.3, 5.5, 5.6 | 5.1.4, 5.1.6, 5.1.8, **5.2.2, 5.2.3, 5.2.5**, 5.4 |
| 6. Kết luận | toàn chương (6.1–6.4) | rà soát phần nghiên cứu |
| Tài liệu tham khảo | cùng giữ (một người giữ danh mục chính) | cùng giữ |
| Phụ lục | C (số liệu), D (cấu hình proxy), E (API + CSDL), F (cài đặt) | A, B (đổi nội dung — mục 8.2) |

Khoa chia theo **mảng chuyên môn của đề cương**, không theo vertical code, nên có mục người viết phải
lấy thông tin từ code của người kia: Hùng viết 4.4.2–4.4.3, 5.1.2.4, 5.1.5 (ví, thanh toán — code của
Khoa); Khoa viết 3.3–3.6, 5.2.x (thí nghiệm — Hùng dựng nhiều). **Hỏi trực tiếp người kia, và người đó
review đúng mục ấy.**

Đợt 1 (16/11): Khoa xong Chương 1–2; Hùng xong 3.1–3.2, 3.4.2, 3.7. Đợt 2 (21/11): mọi mục còn lại.
22–26/11 đọc chéo, ghép, cập nhật mục lục/danh mục, xóa khung hướng dẫn. **27/11 nộp.**

### 8.2. Mục phải đổi nội dung so với bản draft

Bản draft viết theo thiết kế cũ (30 prompt, rubric chấm mù, 270 lượt). Thí nghiệm đã chạy theo thiết kế
khác (D10, Design Y, D14). Báo cáo phải kể **cái đã chạy thật**:

| Mục | Draft đang ghi | Viết lại theo | Nguồn |
|---|---|---|---|
| 1.3 (RQ1) | "cùng bộ 30 prompt" | 4 benchmark công khai, 80 item | `docs/experiment-design.md` mục 2, 5 |
| 1.5 Đóng góp | — | 3 phần theo **D20** (6.2 cũng vậy) | `docs/roadmap.md` D20 |
| 1.4.3 / 6.4 | VNPay là chức năng | VNPay vào hướng phát triển (D19) | D19 |
| 3.3.2 Giả thuyết | — | H1–H3 đăng ký 14/10 + kết quả đúng/sai | `experiment-design.md` mục 7, `experiment-results.md` |
| 3.4.1 Pool | "2 tầng / 3 tầng" lẫn lộn | 5 model 3 tầng; Sonnet bị loại khỏi định tuyến (D12) | D12 |
| 3.4.2 Cấu hình proxy | — | Design Y: giá / độ khó / độ dài câu hỏi | `experiment-design.md` mục 4, `proxy-configs/` |
| 3.4.3 Bộ prompt | 30 prompt 4 loại | **4 benchmark** (MMLU, GSM8K, HumanEval, IFEval), 20 item/bộ, seed 20261014, vì sao 0-shot, vì sao bỏ MT-Bench | `docs/benchmark-survey.md`, D10 |
| 3.4.4 Lặp, biến | 270 lượt | 720 lượt; D14 mở rộng **sau khi thấy 360 lượt** kèm 5 ràng buộc | D14 |
| 3.5.2 Chấm điểm | rubric, chấm mù, chấm kép | metric chuẩn tự động: accuracy, exact match, pass@1, IFEval strict | D10, `experiments/analysis/graders.py` |
| 3.6 Luật quyết định | — | luật 4 bước + bằng chứng khóa (`9d6dfd7`, 11/09) + luật dự phòng D13 | D13 |
| 5.2.1–5.2.5 | — | số liệu 720 lượt | `experiment-results.md`, `experiments/results/d14-full-720/tables/` |
| **5.2.6 (mới)** | — | baseline một model, đường biên Pareto, cận trên (D18) | TASK-72 |
| **5.2.7 (mới)** | — | phép thử sự cố trước/sau D16 | `experiment-results.md` mục phép thử tiêm lỗi |
| Phụ lục A | 30 prompt + đáp án | danh sách 80 item (ID, bộ, chỉ số nguồn) + 1 ví dụ mỗi bộ | `experiments/prompts/prompts.json` |
| Phụ lục B | bảng chấm rubric | cách chấm từng metric + phiên bản harness | `docs/benchmark-survey.md` |

Các điểm bản draft tự ghi "cần thống nhất" đã có đáp án: dùng **credit** (không gọi token); markup 50%
= lợi nhuận biên **33,3%**; Mock Payment là Must-have, VNPay giờ là Could-have; pool **3 tầng**;
dùng "Creator". Riêng "giới thiệu (thay cho system prompt)" trong bảng thuật ngữ đã cũ: nay system
prompt là trường `instructions` riêng (D8).

## 9. Checklist

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
