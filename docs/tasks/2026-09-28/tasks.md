# Task tuần 28/09 – 04/10/2026 (Hùng & Khoa)

Thuộc lộ trình `docs/roadmap.md`: tuần này làm **Phase C** (thiết kế & cấu hình routing thật cho 3
proxy). Ký hiệu **A→R** = người viết → người phản biện. Việc ghi "Nếu còn thời gian" là mở rộng,
không bắt buộc.

**Bản nháp do Hùng dựng lúc tạo folder (29/09, giữa tuần vì mới đổi quy ước) — điều chỉnh tự do ở
buổi họp đầu tuần, không coi đây là đã chốt.**

**Quy ước mới (đọc trước khi làm):** đây là tuần đầu tiên dùng `docs/tasks/<tuần>/` thay cho
`docs-local/tasks-*.md`. Mỗi người ghi output/log vào đúng file riêng của mình
(`log-hung.md`/`log-khoa.md`), commit kèm code, **không paste log vào chat nữa** — người kia tự
`git pull` và đọc. Review (nếu có) viết thẳng vào cuối file log được review, dưới mục
`## Review — <người review> (<ngày>)`.

## Đích của tuần (kiểm tra vào cuối tuần)

- [ ] D2 (mục tiêu routing chung để so 3 proxy công bằng) và D7 (`max_retries`/timeout/cách tính
      lượt lỗi) có kết luận, ghi vào `docs/roadmap.md` mục 4.
- [ ] `docs/routing-policy.md` tồn tại: mục tiêu chung + cách mỗi proxy diễn đạt được/không diễn
      đạt được (dựa trên `docs/litellm-routing-notes.md`, `bifrost-routing-notes.md`,
      `portkey-routing-notes.md`).
- [ ] LiteLLM chạy với routing strategy thật (không còn `simple-shuffle` mặc định), xác định được
      `selected_model` mỗi lượt.
- [ ] Bifrost có chuỗi `fallbacks` thật theo D2 (phần lớn nền tảng đã xong từ tuần trước — K4).
- [ ] Portkey có ít nhất 1 rule thật (không còn `strategy.mode: "single"`).
- [ ] OpenAI đã top-up, `app.chat.default-model` đổi lại `gpt-4o-mini` (đang tạm để `gemini-flash`
      từ lúc test Gemini tuần trước).

## Việc chung (cả hai)

**J1. Họp đầu tuần chốt D2 + D7**
- D2: mục tiêu routing chung cho cả 3 proxy — đề xuất "ưu tiên model rẻ nhất đủ tốt, có failover
  khi lỗi" (đã có trong `roadmap.md` mục 3.C), cần chốt cụ thể hơn: có dùng Bifrost Complexity
  Router không (câu hỏi mở trong `bifrost-routing-notes.md` mục 5), chuỗi fallback theo thứ tự
  nào (rẻ→trung→đắt hay khác).
- D7: con số cụ thể `num_retries`/`timeout` áp dụng giống nhau ở cả 3 proxy (Bifrost mặc định
  `max_retries: 0` — xem `bifrost-routing-notes.md` mục 3).
- Xong khi: D2, D7 có cột "Kết luận" trong `roadmap.md` mục 4.

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

**H3 (chờ Khoa xác nhận top-up).** Đổi `app.chat.default-model` về `gpt-4o-mini` sau khi Khoa báo
OpenAI đã có credit thật; test 1 lượt chat thật ngắn qua app để xác nhận.

**Nếu còn thời gian**
- **H4.** Runner skeleton (carry-over từ tuần trước, H6 cũ): gọi 1 prompt thật qua LiteLLM, lưu JSON
  thô vào `experiments/results/`.

---

## Khoa

**K1. Bifrost: hoàn thiện `fallbacks` theo D2**
- Phần lớn đã xong tuần trước (K4: `fallbacks` chạy thật, `routing_info` đọc được). Còn thiếu:
  set `max_retries` theo D7 (hiện `max_retries: 0` mặc định), cấu hình chuỗi fallback đúng thứ tự
  D2 chọn cho **cả 5 model** (tuần trước mới test 1 cặp).
- Xong khi: chuỗi fallback đủ 5 model, retry giống LiteLLM/Portkey theo D7.

**K2. OpenAI top-up**
- Nạp credit thật (theo D1, mức tối thiểu đủ dùng — xem CLAUDE.md mục 2 "Chính sách chi phí API
  key"). Báo Hùng ngay khi xong để đổi `default-model`.
- Xong khi: 1 lượt chat GPT-4o-mini thật thành công, `usage_logs.status=success`.

**K3. Review C03 với Hùng**
- Đọc lại `experiments/results/grading-sample.csv` dòng `o-0003`, giải thích lý do cho 0.5 điểm
  "không lỗi" (hay đồng ý đổi thành 1) — ghi vào cuối `docs/grading-rubric.md`.

**Nếu còn thời gian**
- **K4.** Bifrost Complexity Router: test thử xem có dùng được không (cần "Configure embedding"
  trước, xem `bifrost-routing-notes.md` mục 2) — chỉ làm nếu D2 quyết định có dùng.

---

## Danh sách review chéo

| Sản phẩm | Người viết | Người phản biện | Phản biện cần làm gì |
|---|---|---|---|
| `docs/routing-policy.md` | Cả hai (J2) | — | Đọc chéo trước khi coi là chốt |
| Cấu hình LiteLLM thật | Hùng | Khoa | Dựng lại trên máy Khoa, thử 1 lượt |
| Cấu hình Portkey thật | Hùng | Khoa | Dựng lại trên máy Khoa, thử 1 lượt |
| Bifrost `fallbacks` đủ 5 model | Khoa | Hùng | Dựng lại trên máy Hùng, thử 1 lượt lỗi cưỡng ép |

## Nếu bị chặn

| Tình huống | Làm gì |
|---|---|
| Chưa chốt được D2 | Tạm dùng đề xuất trong `roadmap.md` mục 3.C, ghi rõ "tạm", làm tiếp Phase D sau |
| OpenAI chưa top-up kịp | H3 lùi sang tuần sau, không chặn H1/H2/K1 |
| Portkey conditional rule phức tạp hơn dự kiến | Tạm dùng rule đơn giản nhất (1 điều kiện), ghi giới hạn vào `routing-policy.md` |

## Nhật ký cuối tuần (điền vào Chủ nhật 04/10)

| Việc | Trạng thái (✅/🟨/⛔) | Ghi chú |
|---|---|---|
| J1–J3 | | |
| H1 | | |
| H2 | | |
| H3 | | |
| K1 | | |
| K2 | | |
| K3 | | |
