# Task tuần 28/09 – 04/10/2026 (Hùng & Khoa)

Thuộc lộ trình `docs/roadmap.md`: tuần này gộp **Phase C + Phase D** (cấu hình routing thật cho 3
proxy, rồi viết runner + chạy thử nhỏ 27 lượt) — Hùng chủ động đẩy nhanh tiến độ, không đợi tách
riêng 2 tuần như roadmap gốc. Ký hiệu **A→R** = người viết → người phản biện. Việc ghi "Nếu còn
thời gian" là mở rộng, không bắt buộc.

**Rủi ro của việc gộp (nói thẳng để biết mà canh):** Phase D phụ thuộc Phase C xong trước (runner
cần routing thật mới có gì để đo) — nên trong tuần vẫn phải làm C xong trước rồi mới D, không làm
song song được hoàn toàn. Nếu C trễ, ưu tiên xong C cho chắc, đừng cắt ngắn C để kịp D — D chưa
xong thì lùi được, C mà cấu hình ẩu thì toàn bộ dữ liệu Phase E sau này sai theo.
**Lượt gọi thật (27 lượt dry-run) chỉ chạy khi đã xin xác nhận riêng lúc đó** (CLAUDE.md mục 2,
D1) — không tự chạy chỉ vì đã ghi trong kế hoạch tuần.

**Bản nháp do Hùng dựng lúc tạo folder (29/09, giữa tuần vì mới đổi quy ước) — điều chỉnh tự do ở
buổi họp đầu tuần, không coi đây là đã chốt.**

**Quy ước mới (đọc trước khi làm):** đây là tuần đầu tiên dùng `docs/tasks/<tuần>/` thay cho
`docs-local/tasks-*.md`. Mỗi người ghi output/log vào đúng file riêng của mình
(`log-hung.md`/`log-khoa.md`), commit kèm code, **không paste log vào chat nữa** — người kia tự
`git pull` và đọc. Review (nếu có) viết thẳng vào cuối file log được review, dưới mục
`## Review — <người review> (<ngày>)`.

## Đích của tuần (kiểm tra vào cuối tuần)

- [x] D2 (mục tiêu routing chung để so 3 proxy công bằng) và D7 (`max_retries`/timeout/cách tính
      lượt lỗi) có kết luận, ghi vào `docs/roadmap.md` mục 4. — chốt 2026-09-29.
- [ ] `docs/routing-policy.md` tồn tại: mục tiêu chung + cách mỗi proxy diễn đạt được/không diễn
      đạt được (dựa trên `docs/litellm-routing-notes.md`, `bifrost-routing-notes.md`,
      `portkey-routing-notes.md`).
- [ ] LiteLLM chạy với routing strategy thật (không còn `simple-shuffle` mặc định), xác định được
      `selected_model` mỗi lượt.
- [ ] Bifrost có chuỗi `fallbacks` thật theo D2 (phần lớn nền tảng đã xong từ tuần trước — K4).
- [ ] Portkey có ít nhất 1 rule thật (không còn `strategy.mode: "single"`).
- [x] `app.chat.default-model` đổi lại `gpt-4o-mini` (đang tạm để `gemini-flash` từ lúc test Gemini
      tuần trước) — OpenAI top-up **đã xong từ trước** (1 key dùng chung cho cả Hùng và Khoa, chia
      tiền sau; Khoa đã xác nhận gọi được cả 5 model từ 26/09), không còn gì phải chờ.
- [ ] Runner (`experiments/scripts/run_experiment.py`) gọi thật qua app Conduit (D3), lặp 3
      lần/prompt, lưu kết quả thô + ghi `messages`/`usage_logs`/`routing_decisions`.
- [ ] `experiments/analysis/decision_rule.py` kiểm chứng bằng dữ liệu giả (biết trước kết quả từng
      nhánh của luật) — **không cần key thật**, chạy trước khi tốn tiền cho dry-run.
- [ ] Dry-run 3 prompt × 3 proxy × 3 lần = 27 lượt (**chỉ chạy sau khi xin xác nhận riêng lúc đó**).

## Việc chung (cả hai)

**J1. Họp đầu tuần chốt D2 + D7** — ✅ xong 2026-09-29
- D2: **đã chốt** — ưu tiên model rẻ nhất, có phương án dự phòng khi lỗi; LiteLLM `cost-based-routing`,
  Bifrost/Portkey chuỗi tĩnh rẻ→trung→đắt; không dùng Bifrost Complexity Router ở vòng chính.
- D7: **đã chốt** — `num_retries=2`, `timeout=45s` giống nhau cả 3 proxy; lượt lỗi ghi log đầy đủ,
  không tính phí, tính là 1 lần lặp, không chạy bù.
- Chi tiết đầy đủ: `docs/roadmap.md` mục 4.

**J2. `docs/routing-policy.md`**
- Tổng hợp từ D2 + 3 file routing-notes đã có. Bảng "proxy nào diễn đạt được gì" (đã có sẵn khung ở
  `bifrost-routing-notes.md` mục 4, làm tương tự cho LiteLLM/Portkey).
- Xong khi: file tồn tại, cả hai đọc và đồng ý; nếu cần hỏi GVHD thì hỏi trước khi chốt.

**J3. Review chéo (giữa/cuối tuần)**
- Theo danh sách "Review chéo" bên dưới.
- Còn nợ từ tuần trước: **thống nhất điểm C03** trong `experiments/results/grading-sample.csv`
  (Khoa chấm 0.5, Hùng chấm 1 ở tiêu chí "không lỗi" — xem `docs-local` hoặc hỏi lại Hùng lý do cho
  0.5). Ghi kết luận + lý do vào cuối `docs/grading-rubric.md`.

---

## Hùng

**H1. Cấu hình LiteLLM routing thật**
- Dùng `proxy-configs/litellm/config.routing-draft.yaml` làm nền (đã nhóm 5 model vào alias
  `conduit-pool`, đã sửa 2 model Claude). Chọn 1 routing_strategy theo D2, áp `num_retries`/timeout
  theo D7. Merge vào `config.yaml` chính thức khi chạy ổn.
- Xong khi: gọi alias `conduit-pool` nhiều lần, xác định được model LiteLLM tự chọn mỗi lần từ
  response, khớp đúng chiến lược đã chọn.

**H2. Cấu hình Portkey routing thật**
- Theo `docs/portkey-routing-notes.md`: viết `strategy.mode: "conditional"` với ít nhất 1 rule tĩnh
  mô phỏng "chọn rẻ nhất" (vd. theo `metadata.prompt_group` runner sẽ gắn sau, hoặc đơn giản hơn:
  `default` trỏ model rẻ nhất). Cập nhật `proxy-configs/portkey/config.json`.
- Xong khi: gửi request kèm `x-portkey-config`, Portkey chọn đúng target theo rule.

**H3. Đổi `default-model`, viết runner**
- Đổi `app.chat.default-model` về `gpt-4o-mini` (hết bị chặn — 1 key dùng chung cho cả 2 người,
  Khoa đã xác nhận cả 5 model gọi được từ 26/09); test 1 lượt chat thật ngắn qua app để xác nhận.
- Viết `experiments/scripts/run_experiment.py` (Phase D, gộp vào tuần này): gọi thật qua app Conduit
  theo D3 (không gọi thẳng proxy), dùng 1 user/agent/conversation riêng cho thí nghiệm, lặp 3
  lần/prompt, lưu JSON thô vào `experiments/results/` + tự động ghi được `messages`/`usage_logs`/
  `routing_decisions` (qua chính luồng chat có sẵn của Khoa).
- Xong khi: chạy được với **1 prompt duy nhất** trên 1 proxy (chưa cần dry-run 27 lượt) và ra đúng
  file kết quả + đủ 3 dòng `routing_decisions`.

**H4. Kiểm chứng `decision_rule.py`**
- Dùng dữ liệu giả (viết tay hoặc random có kiểm soát) cho từng nhánh của luật quyết định (loại
  <80%, chi phí, chênh <5% → p95, hòa → consistency) — không cần key thật.
- Xong khi: mỗi nhánh có ít nhất 1 test case biết trước kết quả, script cho ra đúng kết luận mong
  đợi.

---

## Khoa

**K1. Bifrost: hoàn thiện `fallbacks` theo D2**
- Phần lớn đã xong tuần trước (K4: `fallbacks` chạy thật, `routing_info` đọc được). Còn thiếu:
  set `max_retries` theo D7 (hiện `max_retries: 0` mặc định), cấu hình chuỗi fallback đúng thứ tự
  D2 chọn cho **cả 5 model** (tuần trước mới test 1 cặp).
- Xong khi: chuỗi fallback đủ 5 model, retry giống LiteLLM/Portkey theo D7.

**K2. Review C03 với Hùng**
- Đọc lại `experiments/results/grading-sample.csv` dòng `o-0003`, giải thích lý do cho 0.5 điểm
  "không lỗi" (hay đồng ý đổi thành 1) — ghi vào cuối `docs/grading-rubric.md`.
- (K2 cũ "OpenAI top-up" đã xong — dùng chung 1 key với Hùng, chia tiền sau, không cần việc riêng.)

**K3. Ghi log thí nghiệm (D3, Phase D gộp vào tuần này)**
- Phối hợp với H3 (runner): đảm bảo 1 lượt chat qua app tạo đủ `messages` + `usage_logs` +
  `routing_decisions` (kèm `response_quality_score` — cột này hiện có ghi được từ chấm tự động
  closed-QA chưa? kiểm tra lại, nếu chưa thì đây là việc cần làm).
- Xong khi: 1 lượt chat thật qua runner của Hùng cho ra đủ 3 dòng ở 3 bảng, không thiếu cột nào.

**Nếu còn thời gian**
- **K4.** Bifrost Complexity Router: test thử xem có dùng được không (cần "Configure embedding"
  trước, xem `bifrost-routing-notes.md` mục 2) — chỉ làm nếu D2 quyết định có dùng (hiện đang
  **không dùng**, nên việc này ưu tiên thấp).

---

## Danh sách review chéo

| Sản phẩm | Người viết | Người phản biện | Phản biện cần làm gì |
|---|---|---|---|
| `docs/routing-policy.md` | Cả hai (J2) | — | Đọc chéo trước khi coi là chốt |
| Cấu hình LiteLLM thật | Hùng | Khoa | Dựng lại trên máy Khoa, thử 1 lượt |
| Cấu hình Portkey thật | Hùng | Khoa | Dựng lại trên máy Khoa, thử 1 lượt |
| Bifrost `fallbacks` đủ 5 model | Khoa | Hùng | Dựng lại trên máy Hùng, thử 1 lượt lỗi cưỡng ép |
| Runner + `decision_rule.py` kiểm chứng | Hùng | Khoa | Chạy lại trên máy Khoa với 1 prompt, đọc code `decision_rule.py` tìm 1 nhánh chưa test |

## Nếu bị chặn

| Tình huống | Làm gì |
|---|---|
| Chưa chốt được D2 | Đã chốt (29/09), không còn áp dụng |
| Portkey conditional rule phức tạp hơn dự kiến | Tạm dùng rule đơn giản nhất (1 điều kiện), ghi giới hạn vào `routing-policy.md` |
| Phase C (routing 3 proxy) chưa xong kịp giữa tuần | **Không cắt ngắn C để chạy D** — lùi runner/dry-run sang tuần sau, báo lại trong `log-*.md` |
| Runner viết xong nhưng dry-run 27 lượt chưa kịp xin xác nhận | Dừng ở "chạy được 1 prompt", để dry-run đầy đủ cho lần làm việc tiếp theo — không tự ý chạy 27 lượt |

## Nhật ký cuối tuần (điền vào Chủ nhật 04/10)

| Việc | Trạng thái (✅/🟨/⛔) | Ghi chú |
|---|---|---|
| J1–J3 | | |
| H1 | | |
| H2 | | |
| H3 | | |
| H4 | | |
| K1 | | |
| K2 | | |
| K3 | | |
