# Rubric chấm mù — prompt mở & code (K3)

Áp dụng cho 18/30 prompt không có đáp án đúng/sai khách quan: **6 code** (C01–C06) +
**12 mở** (E01–E04 email, S01–S04 tóm tắt, R01–R04 sáng tạo) — theo đúng CLAUDE.md mục 2 và
`docs/eval-prompts.md`. 12 câu closed-QA (Q01–Q12) chấm tự động bằng so khớp đáp án, **không**
dùng rubric này.

**Nguyên tắc chấm mù (bắt buộc):** người chấm chỉ thấy `output_id` + nội dung câu trả lời —
**không** bao giờ thấy cột `proxy_name`/`model`. Xem mẫu bảng CSV ở mục 4.

---

## 1. Ba tiêu chí, mỗi tiêu chí 0–1 điểm

| Tiêu chí | 0 điểm | 0.5 điểm | 1 điểm |
|---|---|---|---|
| **On-task** — có làm đúng yêu cầu đề bài không | Lạc đề hoàn toàn, hoặc từ chối trả lời không có lý do hợp lý | Có làm đúng ý chính nhưng bỏ sót 1 yêu cầu phụ trong đề (VD đề yêu cầu "đúng 3 câu" nhưng trả lời 5 câu, đề yêu cầu nêu rõ ai phụ trách nhưng thiếu 1 người) | Đáp ứng đầy đủ **mọi** yêu cầu nêu trong đề, kể cả ràng buộc định dạng (số câu, số từ, giọng văn...) |
| **Độ dài phù hợp** — không quá ngắn/dài so với yêu cầu | Quá ngắn tới mức cụt lủn (< 50% độ dài kỳ vọng) hoặc quá dài lan man, chứa nội dung thừa không liên quan | Hơi lệch so với độ dài kỳ vọng (dư/thiếu khoảng 20–50%) nhưng không ảnh hưởng chất lượng đọc | Độ dài sát với yêu cầu đề bài (nếu đề không ghi rõ số từ/câu, dùng chuẩn "độ dài tự nhiên cho thể loại" — xem mục 2) |
| **Không lỗi** — không có lỗi kỹ thuật/diễn đạt | Có lỗi nghiêm trọng: code sai logic/không chạy được, câu văn sai ngữ pháp nặng, thông tin sai sự thật rõ ràng | Có lỗi nhỏ không ảnh hưởng tới việc hiểu/dùng được (lỗi chính tả nhẹ, code đúng logic nhưng thiếu edge-case không được đề bài yêu cầu) | Không có lỗi nào phát hiện được — với code: đúng logic được mô tả (không cần build/run tự động, theo đúng `eval-prompts.md`); với văn bản: đúng chính tả/ngữ pháp, thông tin chính xác |

**Điểm 1 output = tổng 3 tiêu chí, tối đa 3.0.** Không làm tròn, không quy đổi phần trăm — giữ
nguyên thang 0/0.5/1 cho từng tiêu chí để dễ tính % agreement giữa 2 người chấm (mục 5).

---

## 2. Mốc "độ dài phù hợp" theo từng loại prompt (ví dụ cụ thể, tránh chấm cảm tính)

| Loại | Prompt mẫu | Mốc độ dài kỳ vọng |
|---|---|---|
| **Email** (E01–E04) | "Viết email xin nghỉ phép..." | 80–150 từ — đủ 3 phần (mở đầu, nội dung, kết) của 1 email công việc thông thường. Dưới 40 từ = quá cụt (thiếu phần mở/kết); trên 250 từ = lan man |
| **Tóm tắt — có ràng buộc rõ** (S01, S04) | "...trong đúng 3 câu" / "...đúng 3 điểm tích cực và 3 điểm tiêu cực" | Đếm được đúng số câu/số gạch đầu dòng đề bài yêu cầu — đây là ràng buộc **cứng**, sai số lượng trừ thẳng vào "on-task", không chỉ "độ dài" |
| **Tóm tắt — không ràng buộc số câu** (S02, S03) | "...thành danh sách việc cần làm" / "...thành 2-3 câu dễ hiểu" | S02: đủ 3 đầu việc (An/Bình/Chi) kèm người phụ trách, không cần đúng số câu. S03: đúng 2-3 câu như đề ghi |
| **Sáng tạo — có ràng buộc số từ/câu** (R01, R02) | "khoảng 50 từ" / "4-6 câu lục bát" | R01: 35–70 từ (biên độ "khoảng"). R02: đúng thể thơ lục bát (câu 6-8), 4-6 câu |
| **Sáng tạo — không ràng buộc** (R03, R04) | "viết đoạn mở đầu" / "đặt tên + slogan" | R03: 1 đoạn văn liền mạch (~80–200 từ) là hợp lý cho "đoạn mở đầu truyện". R04: ngắn gọn — 1 tên + 1 câu slogan, không cần dài |
| **Code** (C01–C06) | Tất cả | Không chấm theo số dòng — "độ dài phù hợp" ở đây nghĩa là: không viết thừa function/class không liên quan, không thiếu phần được đề bài yêu cầu (VD C03 yêu cầu "nêu lỗi VÀ viết lại code" — thiếu 1 trong 2 phần là chưa đủ độ dài) |

---

## 3. Lưu ý riêng cho Code (C01–C06) — nối với quyết định D4

Theo `eval-prompts.md`: *"không lỗi" ở đây nghĩa là code chạy đúng logic được mô tả, không cần
build/run tự động*. Người chấm đọc code bằng mắt, không chạy thật. Gợi ý kiểm tra nhanh từng câu:

| ID | Điểm cần nhìn khi chấm "không lỗi" |
|---|---|
| C01 (số nguyên tố) | Có xử lý đúng biên n≤1 (không phải số nguyên tố) không? |
| C02 (đảo chuỗi, không dùng `reverse()`) | Có thực sự tránh gọi hàm `reverse()`/`[::-1]` có sẵn không — đây là ràng buộc đề bài, vi phạm thì trừ "on-task" |
| C03 (sửa lỗi cú pháp) | Có chỉ đúng lỗi thật (thiếu `\n`/dấu `;` giữa 2 lệnh) không, code sửa lại có chạy được không |
| C04 (SQL top 5) | Có `ORDER BY amount DESC LIMIT 5` (hoặc tương đương), có `GROUP BY customer_id` nếu tính tổng theo khách hàng không |
| C05 (binary search) | Giải thích đúng độ phức tạp O(log n) không, code có đúng logic chia đôi không |
| C06 (palindrome) | Có xử lý hoa/thường, khoảng trắng theo đúng mức đề bài yêu cầu (đề không ghi rõ, nên chấp nhận cả 2 cách, không trừ điểm) |

**Nếu D4 (quyết định trong `roadmap.md`) chọn cách chấm code khác** (VD build/run tự động thay
vì rubric) — rubric này chỉ áp dụng cho phần văn bản (email/tóm tắt/sáng tạo), bỏ mục 3.

---

## 4. Mẫu bảng chấm mù (CSV)

Cấu trúc file `experiments/results/grading-sample.csv` (tạo khi có dữ liệu thật để chấm):

```csv
output_id,prompt_id,answer_text,on_task,length_ok,error_free,total,grader
o-0001,E02,"Kính gửi Anh/Chị,\n\nTôi rất tiếc khi biết đơn hàng của Anh/Chị bị giao trễ...",1,1,1,3.0,khoa
o-0002,S01,"Biến đổi khí hậu đang gia tăng do phát thải khí nhà kính...",1,0.5,1,2.5,khoa
o-0003,R02,"Heo may khe khẽ chạm vai\nHà Nội thu đến hao gầy lá rơi...",0.5,1,1,2.5,hung
```

**Cột bắt buộc có:** `output_id` (mã ẩn danh, KHÔNG lộ proxy), `prompt_id`, `answer_text`, 3 cột
điểm, `total`, `grader` (tên người chấm — để tính % agreement).
**Cột KHÔNG bao giờ có trong file đưa cho người chấm:** `proxy_name`, `model`, `latency_ms` —
những cột này chỉ join lại **sau khi** đã có điểm, lúc phân tích kết quả, không phải lúc chấm.

`output_id` sinh độc lập, không theo pattern đoán được proxy nào (VD không dùng `litellm-001`,
`bifrost-001` — dùng số ngẫu nhiên/tuần tự chung `o-0001, o-0002...` cho cả 3 proxy trộn lẫn).

---

## 5. Quy trình chấm mù + tính % agreement (đúng CLAUDE.md mục 2)

1. Sau khi chạy thực nghiệm, xuất toàn bộ output của prompt mở + code ra file CSV theo mẫu mục 4,
   **xáo trộn thứ tự**, không sắp theo proxy.
2. Chọn ngẫu nhiên **30%** số output (theo `eval-prompts.md`: 162 output mở+code → 30% ≈ 49 output)
   để **cả Hùng và Khoa cùng chấm độc lập**, không trao đổi trước.
3. 70% còn lại, mỗi người chấm phần riêng (chia đôi).
4. Tính % agreement trên tập 30% chấm chung: với mỗi tiêu chí, đếm số output 2 người chấm **giống
   hệt điểm** / tổng số output chấm chung. Báo cáo riêng % agreement cho từng tiêu chí (on-task,
   độ dài, không lỗi) — không gộp chung 1 con số, vì mức độ chủ quan khác nhau giữa 3 tiêu chí.
5. Output nào lệch điểm > 0.5 giữa 2 người → thảo luận trực tiếp, thống nhất lại — ghi log các
   trường hợp lệch vào báo cáo (đây là phần "hạn chế/rủi ro" đáng đưa vào khóa luận).

---

## 6. Việc đã làm để kiểm chứng rubric (theo đúng "Xong khi" của K3)

Đã tự chấm thử 3 câu trả lời mẫu (1 email, 1 tóm tắt, 1 code) theo rubric trên — xem
`experiments/results/grading-sample.csv` (mục 4) — các điểm số phản ánh đúng mức phân biệt
0/0.5/1 mô tả ở mục 1. **Cần Hùng chấm lại cùng 3 câu này** (theo J3 — review chéo Thứ 6) để so
điểm và tinh chỉnh mô tả rubric nếu có chỗ hiểu khác nhau.
