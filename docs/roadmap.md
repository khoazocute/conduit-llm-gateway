# Conduit — Lộ trình theo phase (Hùng & Khoa)

Tạo: 2026-09-20. Đọc cùng `docs-local/project-status.md` (hiện trạng) và `docs-local/tasks-2026-09-21.md` (việc tuần này) — 2 file đó vẫn chỉ có trên máy Hùng; file này (`docs/roadmap.md`) đã lên repo, đọc/sửa chung được qua PR.

Mục tiêu của lộ trình này: hai người cùng làm phần **đánh giá 3 proxy** (đóng góp khoa học duy nhất của khóa luận, `CLAUDE.md` mục 1–2) và phản biện lẫn nhau, đồng thời hoàn thiện phần còn lại của hệ thống. Mỗi phase có **tiêu chí "đạt"** kiểm chứng được để tick.

---

## 1. Cách làm việc chung

- **Mỗi hạng mục có 1 người viết (A – author) và 1 người phản biện (R – reviewer).** Phản biện nghĩa là: tự chạy lại sản phẩm trên máy mình, đọc kỹ, và ghi lại ít nhất một điểm nghi ngờ hoặc một phép thử thất bại có chủ đích. Đổi vai giữa các hạng mục để hai người đều hiểu toàn bộ.
- Mỗi người làm trên branch riêng (`lhung`, `dangkhoa`), PR nhỏ, người còn lại review rồi mới merge vào `main`. Không commit thẳng `main`.
- Không thêm dòng `Co-Authored-By: Claude` hay ghi chú tương tự vào commit và mô tả PR (`CLAUDE.md` mục 8).
- API key chỉ nằm trong `.env` (đã gitignore). Không dán vào chat, commit, hay tài liệu.
- Kết quả thí nghiệm thô được lưu ngay khi có, không sửa tay; lượt lỗi phải được ghi lại, không loại bỏ lặng lẽ.
- Cuối mỗi tuần: cập nhật bảng theo dõi ở mục 5 và bảng nhật ký trong file task tuần.

---

## 2. Tổng quan các phase

Liên hệ lịch 16 tuần trong `CLAUDE.md` mục 8: phase B–D tương ứng tuần 6–8 (chuẩn bị, setup proxy), phase E là tuần 9–10 (mốc **không được trễ**).

| Phase | Tên | Mục tiêu | Đạt khi (Achievement) |
|---|---|---|---|
| **A** | Đồng bộ & chốt quyết định | `main` có toàn bộ code; các quyết định nền tảng được chốt | `main` chứa code của cả hai; hai người đều chạy pass 2 bộ test trên máy mình; quyết định D1, D3, D4, D5 có kết luận ghi ở mục 4 |
| **B** | Chuẩn bị dữ liệu thực nghiệm | Prompt, giá, key, rubric sẵn sàng | Xem 3.B |
| **C** | Thiết kế & cấu hình routing 3 proxy | Mỗi proxy thật sự tự chọn model theo luật | Xem 3.C |
| **D** | Runner, ghi log, chạy thử | Một lệnh chạy được cả thí nghiệm ở quy mô nhỏ | Xem 3.D |
| **E** | Chạy chính thức & chấm điểm | Có kết quả, chọn được proxy | Xem 3.E |
| **F** | Tích hợp proxy đã chọn & hoàn thiện Must-have | Hệ thống dùng proxy được chọn; có test và CI | Xem 3.F |
| **G** | Should-have, deploy, báo cáo, demo | Bản nộp cuối | Xem 3.G |

---

## 3. Chi tiết từng phase

Ký hiệu: **A→R** = người viết → người phản biện (đề xuất, hai bạn có thể đổi).

### Phase A — Đồng bộ & chốt quyết định
- [ ] Hùng mở PR `lhung → main` (kèm `docs-local/project-status.md`); Khoa review kỹ `GET /purchases` (nằm trong vùng của Khoa), tham số `q` của `/admin/users`, và 2 bản sửa tầng Auth cho SSE; merge. **Hùng→Khoa**
- [ ] Cả hai pull `main`, chạy `e2e_test.sh` và `e2e_workflow_test.sh` trên máy mình. Nếu chưa có key Gemini thì bước chat thành công sẽ rơi vào nhánh "lỗi provider" — chấp nhận được, ghi rõ.
- [ ] Họp chốt các quyết định D1, D3, D4, D5 (mục 4); soạn và gửi câu hỏi cho GVHD (mục 6).

**Đạt khi:** `main` = code mới nhất; 2 bộ test pass trên cả hai máy; bảng quyết định (mục 4) có kết luận cho D1, D3, D4, D5.

### Phase B — Chuẩn bị dữ liệu thực nghiệm
- [ ] `experiments/prompts/prompts.json`: 30 prompt (12 closed-QA, 6 code, 12 mở) khớp `docs/eval-prompts.md`, đúng schema `experiments/prompts/SCHEMA.md`, kèm `expected_answer` + `match_type` cho các câu tự chấm được. **Hùng→Khoa**
- [ ] Kiểm thử từng luật so khớp đáp án với ít nhất 2 câu trả lời mẫu đúng và 2 câu sai (dễ sai ở các đáp án ngắn như `5`, `Có`, `36`). **Hùng→Khoa**
- [ ] Bảng `model_pricing`: 10 dòng (5 model × `token_input`/`token_output`), giá **theo 1 token** (giá niêm yết chia 1.000.000), có URL nguồn + ngày lấy giá ghi trong `docs/model-pricing-sources.md`. **Khoa→Hùng**
- [ ] Đủ API key cho 5 model, có hạn mức chi tiêu; kiểm tra lại tên model trong `proxy-configs/litellm/config.yaml`; smoke test 1 lượt/model qua LiteLLM. **Hùng→Khoa**
- [ ] Rubric chấm mù (`docs/grading-rubric.md`) + mẫu bảng chấm (CSV). **Khoa→Hùng**

**Đạt khi:** script kiểm tra `prompts.json` pass (đúng 12/6/12, id duy nhất, không thiếu trường); `select count(*) from model_pricing` = 10 và một lượt chat cho `cost_upstream > 0`; smoke test 5/5 model trả lời; rubric có mô tả và ví dụ mốc cho từng tiêu chí; hai người cùng chấm thử 3 câu trả lời mẫu và thảo luận các chỗ lệch điểm để làm rõ rubric.

### Phase C — Thiết kế & cấu hình routing 3 proxy
"Routing thật" nghĩa là mỗi proxy phải tự quyết định chọn model nào (hiện backend đang chỉ định cố định `gemini-flash`, proxy chỉ chuyển tiếp nên chưa có gì để đo).
- [ ] `docs/routing-policy.md`: mục tiêu chung cho cả 3 proxy (ví dụ: ưu tiên model rẻ nhất đủ tốt, có failover khi lỗi), cách mỗi proxy diễn đạt mục tiêu đó bằng tính năng riêng của nó, và **những chỗ một proxy không diễn đạt được** (ghi thành giới hạn cho báo cáo). **Khoa→Hùng**, GVHD duyệt (D2).
- [ ] Cấu hình LiteLLM (cost/latency/usage-based, nhóm 5 model). **Hùng→Khoa**
- [ ] Cấu hình Bifrost (weight/load balancing + failover; nạp qua API/UI). **Khoa→Hùng**
- [ ] Cấu hình Portkey (conditional routing; gửi kèm request qua `x-portkey-config`). **Hùng→Khoa**
- [ ] Mọi cấu hình nằm trong `proxy-configs/`, commit được (không chứa key thật).

**Đạt khi:** `routing-policy.md` được cả hai + GVHD đồng ý; với 5 prompt bất kỳ, cả 3 proxy trả lời và mỗi lượt xác định được `selected_model`; mỗi proxy ghi rõ đã bật/không bật fallback và lý do (để so công bằng).

### Phase D — Runner, ghi log, chạy thử
- [ ] `experiments/scripts/run_experiment.py` gọi thật 3 proxy, lặp 3 lần/prompt, lưu kết quả thô vào `experiments/results/`. Cùng `max_tokens`, timeout, quy tắc retry ở cả 3 proxy (D7). **Hùng→Khoa**
- [ ] Đường ghi log thí nghiệm theo quyết định D3: mỗi lượt có 1 dòng `messages` (bắt buộc vì `routing_decisions.message_id` là `NOT NULL`) + `usage_logs` + `routing_decisions` (kèm `response_quality_score`). **Khoa→Hùng**
- [ ] Chấm tự động closed-QA; xuất file chấm mù (ẩn tên proxy, xáo trộn thứ tự) kèm file đối chiếu giữ riêng. **Khoa→Hùng**
- [ ] `experiments/analysis/decision_rule.py` được kiểm chứng: dữ liệu giả có kết quả biết trước cho từng nhánh của luật (loại <80%, chi phí, chênh <5% → p95, hòa → consistency) + đối chiếu tay ít nhất 1 con số trên dữ liệu chạy thử. **cả hai, phản biện chéo**
- [ ] Chạy thử nhỏ: 3 prompt × 3 proxy × 3 lần = 27 lượt.

**Đạt khi:** một lệnh chạy hết dry-run và cho ra file kết quả thô + đủ 27 dòng `routing_decisions`; `decision_rule.py` ra bảng tổng hợp trên dữ liệu thật của dry-run; chi phí thực của dry-run được ghi lại; xử lý lượt lỗi/timeout được ghi trong tài liệu.

### Phase E — Chạy chính thức & chấm điểm (tuần 9–10)
- [ ] Chạy 30 prompt × 3 proxy × 3 lần = **270 lượt**; mỗi người chạy và kiểm tra phần 15 prompt của mình (`CLAUDE.md` mục 8).
- [ ] Chấm tự động closed-QA; chấm mù các câu code/mở; mẫu chấm kép (D6) do **2 người chấm độc lập**; tính % agreement.
- [ ] Áp luật quyết định (`CLAUDE.md` mục 2), chọn proxy chính thức.

**Đạt khi:** đủ 270 lượt (đếm được trong `routing_decisions`), lượt lỗi được liệt kê chứ không bị loại; kết quả thô được lưu bất biến (commit hoặc sao lưu); có bảng số liệu + % agreement + kết luận "proxy được chọn và vì sao" theo đúng thứ tự luật.

### Phase F — Tích hợp proxy đã chọn & hoàn thiện Must-have
- [ ] Chat của Conduit chạy qua proxy được chọn với cấu hình routing đã đánh giá (thay cấu hình tĩnh `active-proxy`).
- [ ] Test service: `AuthService`, `AgentService`, `PurchaseService`, `CreditService`/`ChatService`; **test trừ credit đồng thời không làm số dư âm** (ràng buộc bắt buộc ở `CLAUDE.md` mục 4, hiện chưa có test).
- [ ] Security acceptance test chạy tự động: webhook sai chữ ký, callback trùng, JWT hết hạn (đã có dạng script; đưa vào CI).
- [ ] CI (GitHub Actions): build + test + lint; load test k6/Locust.

**Đạt khi:** CI xanh trên `main`; có báo cáo load test; chat đi qua proxy đã chọn (kiểm tra bằng `routing_decisions.proxy_name`).

### Phase G — Should-have, deploy, báo cáo, demo
- [ ] Should-have theo thứ tự ưu tiên (chỉ khi F xong): RAG (kèm 2 test bảo mật còn thiếu: tenant isolation, prompt injection), VNPay sandbox, fallback qua Provider Adapter, image generation, widget, dashboard doanh thu, rating.
- [ ] Deploy; viết báo cáo; chuẩn bị demo.

**Đạt khi:** hệ thống chạy trên môi trường deploy; báo cáo hoàn chỉnh với phần thực nghiệm và giới hạn; demo chạy được đầu-cuối.

---

## 4. Bảng quyết định cần chốt

| # | Quyết định | Cần chốt trước | Đề xuất của tài liệu này | Kết luận |
|---|---|---|---|---|
| D1 | Ai trả tiền / nguồn API key OpenAI + Anthropic; hạn mức chi tiêu | Phase B | Nạp trước số nhỏ hoặc đặt hạn mức; key riêng cho thí nghiệm, thu hồi sau khi xong | **Đã chốt 2026-09-21:** Hùng chịu chi phí key; dùng tối thiểu (xem CLAUDE.md mục 2). Còn cần: đặt hạn mức ở console, chốt cách Khoa dùng key khi chạy 15 prompt của mình (không gửi key qua chat) |
| D2 | Mục tiêu routing chung để 3 proxy so sánh công bằng | Phase C | Hỏi GVHD; ghi rõ giới hạn của từng proxy | _(trống)_ |
| D3 | Đường ghi log thí nghiệm: qua API chat của Conduit, hay runner gọi thẳng proxy rồi tự ghi DB | Phase D | Gọi thẳng proxy (đo latency sạch, không dính trừ credit/`active-proxy` cố định); runner ghi `messages`+`usage_logs`+`routing_decisions` dưới 1 user/agent/conversation riêng cho thí nghiệm | **Đã chốt 2026-09-23:** đi qua app Conduit thật (`POST /agents/{id}/chat` — đúng luồng chat thật của backend, tự ghi `messages`/`usage_logs`/`routing_decisions`), không gọi thẳng 3 proxy. Lý do: khớp lời dặn của thầy Bình ("áp dụng proxy đó cho dự án của em và đánh giá cái nào chạy ok nhất") — proxy phải được đánh giá *trong* testbed Conduit, không phải bằng benchmark script tách biệt. Hệ quả: cần 1 user/agent/conversation riêng cho thí nghiệm (không lẫn dữ liệu thật); runner gọi HTTP API thật của backend-gateway, không gọi thẳng LiteLLM/Bifrost/Portkey. `active-proxy` tĩnh hiện tại (`app.chat.active-proxy: litellm`) cần đổi được theo từng đợt chạy (env/config) để lần lượt trỏ 3 proxy khi chạy 270 lượt. |
| D4 | Cách chấm 6 prompt code: `SCHEMA.md` nói có `expected_answer`, còn `docs/eval-prompts.md` nói chấm rubric | Phase B | Chấm rubric 3 tiêu chí như prompt mở, hoặc kiểm tra bằng test chạy được — chọn một, ghi rõ | **Đã chốt 2026-09-23:** rubric 3 tiêu chí (on-task/độ dài phù hợp/không lỗi) giống 12 prompt mở, chấm mù. `code` không có `expected_answer`/`match_type` trong `experiments/prompts/prompts.json` (đã cập nhật khớp quyết định này) — 18 prompt (6 code + 12 mở) đều rơi vào nhóm chấm tay. |
| D5 | Giá Gemini khi dùng key miễn phí (thực trả 0 đồng) | Phase B | Nhập **giá niêm yết** để so công bằng, ghi vào báo cáo | **Tạm chốt 2026-09-23:** dùng giá niêm yết trước để không chặn tiến độ. Khoa sẽ chốt lại toàn bộ bảng `model_pricing` (5 model, cả nguồn giá 4 model còn lại) và có thể đổi con số này sau — đây là quyết định tạm, không phải cuối cùng. |
| D6 | Đơn vị "30% mẫu" chấm kép: theo lượt output hay theo prompt. Nếu theo output: (12 mở + 6 code) × 3 proxy × 3 lần = 162 output cần chấm tay, 30% ≈ 49 | Phase E | Theo output, chọn ngẫu nhiên rải đều 3 proxy | **Đã chốt 2026-09-23:** theo output (response) — chọn ngẫu nhiên ~49/162 output rải đều 3 proxy, không theo prompt. |
| D7 | Quy tắc chung: `max_tokens`, timeout, retry, cách tính lượt lỗi | Phase D | Giống hệt nhau ở cả 3 proxy; lượt lỗi ghi lại và tính vào kết quả | _(trống)_ |
| D8 | Nâng role lên creator (chưa có cách); nguồn system prompt của agent (hiện `introduction` không được gửi cho model) | Trước Phase F | Không chặn thí nghiệm; hỏi GVHD rồi quyết | _(trống)_ |

---

## 5. Bảng theo dõi tiến độ

Trạng thái: ⬜ chưa bắt đầu · 🟨 đang làm · ✅ đạt (đã đối chiếu "Đạt khi")

| Phase | Trạng thái | Bắt đầu | Xong | Ghi chú |
|---|---|---|---|---|
| A | 🟨 | 2026-09-20 | | `main` có code cả hai, 2 bộ test pass; D1/D3/D4/D5/D6 đã chốt, còn D2/D7/D8 và câu hỏi GVHD chưa gửi |
| B | 🟨 | 2026-09-22 | | `prompts.json` + luật chấm + test xong (Hùng); smoke test LiteLLM 4/5 model qua (1 lỗi do Gemini quá tải, không phải lỗi cấu hình); còn thiếu: `model_pricing` 10 dòng + nguồn giá (Khoa), rubric chấm mù + mẫu bảng chấm (Khoa) |
| C | ⬜ | | | |
| D | ⬜ | | | |
| E | ⬜ | | | |
| F | ⬜ | | | |
| G | ⬜ | | | |

---

## 6. Câu hỏi nên hỏi GVHD

1. Khóa luận có hai sinh viên: thầy đánh giá đóng góp của từng người ở phần thực nghiệm proxy như thế nào? (Chúng em định chia theo cặp viết – phản biện, mỗi người sở hữu một số hạng mục.)
2. Mục tiêu routing chung để 3 proxy so sánh công bằng nên là gì, khi mỗi proxy có tính năng khác nhau (cost/latency/usage-based, load balancing + failover, conditional routing)?
3. Dùng Gemini bản miễn phí trong thí nghiệm (có lúc quá tải, latency cao) có chấp nhận được không, hay cần nguồn trả phí để phép đo ổn định?
4. Cách chấm prompt code: rubric hay chạy test tự động?
5. Có ngân sách/API credit từ khoa hay phải tự chi trả?

---

## 7. Rủi ro và cách giảm

| Rủi ro | Cách giảm |
|---|---|
| Hết tiền / vượt ngân sách API | Hạn mức chi tiêu, dry-run nhỏ, key riêng, `max_tokens` giống nhau, dùng model rẻ khi debug |
| Gemini bản miễn phí quá tải (503) hoặc chậm (đã thấy ~36 giây cho một câu ngắn, lặp lại ở smoke test 2026-09-23) làm nhiễu p95 latency | Trước phase E: chạy vài lượt thử riêng cho Gemini Flash để đo tỷ lệ lỗi sớm (xem CLAUDE.md mục 2). Nếu lỗi nhiều: ưu tiên bật billing thật cho Gemini hoặc tăng `num_retries`, **không vội đổi model khác** — Gemini Flash là model duy nhất của Google trong pool, đổi sang model OpenAI/Anthropic khác sẽ làm pool chỉ còn 2 hãng, giảm tính đa dạng provider khi so sánh 3 proxy. Chỉ đổi model nếu billing/retry vẫn không đủ. Ghi nhận và báo cáo (câu hỏi 3) |
| Một proxy không diễn đạt được mục tiêu routing chung | Ghi rõ trong `routing-policy.md` và báo cáo như một giới hạn, không che giấu |
| Mất dữ liệu thô khi runner lỗi giữa chừng | Ghi từng lượt ra file ngay khi có; chạy tiếp từ lượt lỗi |
| Trễ mốc tuần 9–10 | Phase B–D làm sớm; kiểm tra tiến độ hằng tuần; việc Should-have không được chen vào |
| Người phản biện chỉ đọc lướt | Yêu cầu tối thiểu ở mục 1: tự chạy lại + ghi ít nhất một điểm nghi ngờ |
