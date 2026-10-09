# Tuần 2026-10-05 → 2026-10-11 — việc được giao

**Mục tiêu tuần:** mở được cổng vào Phase E. Cụ thể: xong 3 việc chặn ở phần A, và chốt hướng xử lý
vấn đề phương pháp ở phần B theo kết luận của thầy. **Không chạy 270 lượt khi phần B chưa chốt** —
chạy rồi mới đổi thiết kế là mất cả đợt dữ liệu.

**Đọc trước khi làm bất cứ việc gì trong tuần này:**
1. `docs/meetings/2026-10-03.md` — kết luận buổi họp GVHD gần nhất. Đây là thứ quyết định phần B.
2. `docs/routing-policy.md` mục 5, **điểm 7–9** — phân tích vấn đề phương pháp và cách thiết kế
   kịch bản ép lỗi cho đúng.
3. `docs/tasks/2026-09-28/log-khoa.md` mục "Cần chỉnh sửa trước Phase E" + phần "Review — Hùng
   (2026-10-03)" ở cuối — 4/7 việc đã xong, phần A dưới đây là 3 việc còn mở.

---

## Phần A — chặn Phase E, làm được ngay, không phụ thuộc kết quả họp

| # | Việc | Ai | Tốn tiền? | Đạt khi |
|---|---|---|---|---|
| A1 | **Ép lỗi LiteLLM 1 lượt** (tương tự `proxy-configs/bifrost/fallback-test.sh`). Hiện mới so được độ bền 1/3 proxy. **Đừng giả định** `conduit-pool` tự chuyển sang `gemini-flash` khi `gpt-4o-mini` lỗi — chưa ai thử | Khoa | 1–2 lượt tầng rẻ | Có log chứng minh LiteLLM **có** hoặc **không** tự chuyển model, ghi vào `docs/litellm-routing-notes.md` + `routing-policy.md` mục 3 |
| A2 | **Portkey: thêm fallback hay ghi thành hạn chế** — chốt cùng nhau. Nếu thêm thì **phải sửa luôn** `HttpProxyChatClient.resolveReturnedModel`: nhánh Portkey đang trả thẳng alias đã gửi, có fallback sẽ ghi **sai model và sai giá** (`routing-policy.md` mục 5 điểm 5) | Cả hai chốt, ai làm thì ghi vào log | Không (nếu chỉ cấu hình) | Có quyết định ghi trong `routing-policy.md`; nếu thêm fallback thì `e2e_workflow_test.sh` còn pass và model ghi nhận đúng |
| A3 | **Kiểm tra độ ổn định Gemini Flash** bằng vài lượt nhỏ trước 270 lượt — `CLAUDE.md` mục 2 bắt buộc. Giờ có **lý do thứ hai**: Gemini là mắt xích thứ 2 của chuỗi Bifrost, nó tự chết thì kịch bản ép lỗi không đo được gì (`routing-policy.md` mục 5 điểm 9d) | Hùng | ~5 lượt Gemini | Biết tỷ lệ lỗi thực tế. Nếu cao → quyết phương án thay thế (bật billing / tăng `num_retries` / thêm nghỉ giữa lượt) **trước** khi chạy 270 lượt |
| A4 | **Thử runner với prompt code + prompt mở** — dry-run chỉ dùng `--limit 3` = 3 câu closed-QA đầu, chưa biết runner xử lý câu dài/không có `expected_answer` thế nào | Hùng | 2 lượt tầng rẻ | Runner ghi được record hợp lệ cho 1 câu code + 1 câu mở (`closed_qa_correct` để trống, không crash) |

**Ghi chú chi phí:** phần A tổng cộng ~10 lượt tầng rẻ. Đúng ngưỡng phải xin xác nhận của Hùng theo
`CLAUDE.md` mục 2 — nêu rõ số lượt trước khi chạy, không tự ý chạy.

---

## Phần B — chờ kết luận họp, điền sau khi đọc `docs/meetings/2026-10-03.md`

| # | Việc | Phụ thuộc |
|---|---|---|
| B1 | Chốt hướng xử lý vấn đề hội tụ: **(a)** thêm kịch bản ép lỗi chính thức / **(b)** đổi mục tiêu sang latency-based (phải sửa D2 + chạy lại) / **(c)** ghi thành hạn chế | Câu 1 trong biên bản họp |
| B2 | Nếu thầy chốt (a): **thiết kế kịch bản ép lỗi chính thức** — ép **2 model** (`gpt-4o-mini` + `gemini-flash`), không chỉ 1 (lý do: `routing-policy.md` mục 5 điểm 9c). Quyết luôn: bao nhiêu prompt, bao nhiêu lần lặp, có ghi vào `routing_decisions` cùng 270 lượt hay tách bảng/cột riêng | B1 = (a) |
| B3 | Nếu thầy chốt (b): sửa D2 trong `roadmap.md` mục 4, cấu hình lại cả 3 proxy, **hủy kết quả dry-run cũ** và chạy lại dry-run trước Phase E | B1 = (b) |
| B4 | **Chốt D8** (nâng role creator + nguồn system prompt agent) → cập nhật `roadmap.md` mục 4 và `CLAUDE.md` mục 8 | Câu 5–6 trong biên bản họp |
| B5 | Đóng "Đạt khi" của Phase C: cần thầy xác nhận `routing-policy.md` | Câu 7 trong biên bản họp |
| B6 | Quyết Gemini free tier hay trả phí cho Phase E (nối với A3) | Câu 3 trong biên bản họp |

---

## Review chéo tuần này

Theo convention `CLAUDE.md` mục 8: người phản biện đọc `tasks.md` (được giao gì) + `log-*.md` của
người kia (báo cáo gì) + **tự chạy lại code/test thật** để đối chiếu, rồi ghi kết luận vào cuối
chính file `log-*.md` đó dưới mục `## Review — <người review> (<ngày>)`.

- A1 (Khoa làm) → Hùng phản biện: tự chạy lại kịch bản ép lỗi LiteLLM, kiểm tra kết luận
  "có/không tự chuyển model" có đúng với log không.
- A3, A4 (Hùng làm) → Khoa phản biện: kiểm tra số lượt đã chạy có khớp con số báo cáo, và record
  runner ghi ra có hợp lệ không.
- A2, B1–B6: quyết định chung, không có người phản biện riêng — cả hai phải cùng ghi đồng ý.

---

## Checklist cuối tuần

- [ ] A1 xong, có log thật, đã ghi vào notes
- [ ] A2 đã chốt (thêm fallback hoặc ghi hạn chế), `routing-policy.md` cập nhật
- [ ] A3 xong, biết tỷ lệ lỗi Gemini, có phương án nếu lỗi cao
- [ ] A4 xong, runner chạy được prompt code + mở
- [ ] Kết luận họp 03/10 đã ghi đầy đủ vào `docs/meetings/2026-10-03.md`
- [ ] B1 đã chốt → biết Phase E chạy theo thiết kế nào
- [ ] `roadmap.md` mục 5 cập nhật trạng thái Phase E
- [ ] Cả hai đã viết `log-hung.md` / `log-khoa.md` và review chéo xong
