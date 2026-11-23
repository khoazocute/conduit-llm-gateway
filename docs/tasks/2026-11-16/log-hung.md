# Nhật ký Hùng - tuần 16/11/2026

## 23/11/2026: đợt 1 viết bản nháp KLTN (Google Doc, đóng góp 1)

Nguồn số liệu: `docs/experiment-results.md` mục 1-16, `docs/experiment-design.md`, `experiments/prompts/manifest.json`, `experiments/results/d14-full-720/tables/*.csv`, `proxy-configs/`. Không gọi API, không có số mới.

| Việc | Kết quả | Ghi chú |
|---|---|---|
| 1.3 | Sửa ô "Tiêu chí đo" của RQ1, RQ2 sang tên chỉ số chuẩn; đoạn "So với đề cương" bỏ "30 prompt", "rubric", thêm câu tách bộ đề khỏi chỉ số | Bảng RQ lúc đọc đã ghi 80 câu, 4 benchmark (có người sửa trước) |
| 3.3.1, 3.3.2 | Viết xong; H1-H3 kèm kết quả đúng/sai (2/3, 3/4, 1/2) | Hình 3.2 còn khung trống |
| 3.4.1 | Viết xong, điền giá và model ID vào Bảng 3.3 | Giá lấy từ `docs/model-pricing-sources.md` (26/09) |
| 3.4.3 | Viết lại theo 4 bộ đề, Bảng 3.4 đổi thành bảng bộ đề; đổi tên mục thành "Bộ đề kiểm thử" | Bộ tiếng Việt 30 câu chỉ nhắc như phép thử độ nhạy ngôn ngữ của Bifrost |
| 3.4.4 | Viết xong (720 lượt, biến cố định, sàn nhiễu 2,92%, nói rõ D14 mở rộng sau khi thấy 360 lượt) | |
| 3.5.1, 3.5.2 | Viết xong; Bảng 3.5 thành bảng định nghĩa chỉ số (thêm 1 cột, 4 hàng), Bảng 3.6 thành bảng chấm tự động | Thêm cột nên cần Khoa liếc lại độ rộng cột |
| 3.6 | Viết xong: luật 4 bước, bằng chứng `9d6dfd7`, D13, hệ quả theo ngưỡng, điểm 16.4 | Hình 3.3 còn khung trống |
| 5.2.1-5.2.5 | Viết xong; Bảng 5.1 thay bằng bảng 16.1 (thêm 8 hàng) | Đổi tên 5.2.1 thành "Bảng chỉ số tổng hợp và chi phí" |
| 5.2.6, 5.2.7 | Tạo mới: baseline D18 và phép thử tiêm lỗi | Mục 5.2.6 đã được Tóm tắt dẫn tới từ trước |
| Phụ lục A-D | Viết xong; đổi tên A thành "Bộ 80 câu kiểm thử", B thành "Chi tiết chấm tự động theo bộ đề" | Phụ lục A chỉ liệt kê nguồn và chỉ số dòng, nội dung câu hỏi trỏ về `experiments/prompts/prompts.json` |

Trạng thái 13 mục đã đổi sang "☒ Chờ review". Khung hướng dẫn (style HuongDan) giữ nguyên.

### Rà 9 mục viết 10/11 (3.1.1, 3.1.2, 3.1.3, 3.1.5, 3.1.6, 3.2, 3.4.2, 3.7.1, 3.7.2)
Quét từ khóa (benchmark, MMLU, chỉ số, độ chính xác, rubric, chấm): không thấy chỗ nào gọi benchmark là chỉ số. Chưa đọc lại từng câu. 3.4.2 và 3.7.1 đã nhất quán với 80 câu, 720 lượt.

### Phát hiện cần bàn
- Số "Token TB/prompt" không có trong repo (file kết quả không lưu token; chỉ có trong bảng `routing_decisions` của DB). Bảng 5.1 bỏ cột này và 5.2.1 ghi rõ "chưa trích thành chỉ số báo cáo". Nếu cần, lấy từ DB.
- Còn sót cách nói cũ ở các mục thuộc đợt 2 và 3: Tóm tắt ("30 prompt × 3 proxy × 3 lần"), 1.4.3 ("bộ thực nghiệm 30 prompt"), khung hướng dẫn 5.4.2 và 5.5 ("quy mô 30 prompt, chấm chủ quan"). Chưa sửa vì ngoài đợt 1.
- Ngưỡng 80% vẫn chỉ áp cho con số gộp; 5.2.2 và 3.6 đã nêu GSM8K của LiteLLM 75% theo 16.4.
- Các hình chưa chèn (Hình 3.2, 3.3, 5.6, 5.7, 5.8): connector không chèn được ảnh từ máy. Đã có `experiments/results/d18-baseline-20261110/tables/cost_accuracy.png` cho Hình 5.8.
- Chỉ số 5.1 "Latency" ghi ở nhóm Vận hành tách 2 hàng (trung bình, p95); Bảng 3.5 gộp thành 1 hàng.

### Việc người kia cần làm
- Khoa: đọc lại mục 3.3-3.6 và 5.2 (đã sửa thẳng phần của Khoa theo cho phép), kiểm cột thứ 4 mới của Bảng 3.5.

## 23/11/2026 (tiếp): sửa theo góp ý và đợt 2

Góp ý của Hùng: liệt kê (1)(2)(3) phải là bullet; không trích chi tiết commit.

| Việc | Kết quả |
|---|---|
| Bullet thật | 85 đoạn trong Doc: 1.1.2, 1.1.3, 1.2.2, 1.3, 1.4.3, 1.5, Tóm tắt, 3.1.5, 3.3.1, 3.3.2, 3.4.4, 3.6, 5.2.6, 6.2-6.4, Phụ lục A, C, D. Đã bỏ dấu "–" gõ tay ở các mục nội dung của 1.2.2 và 1.4.3 (khung hướng dẫn giữ nguyên) |
| Bỏ chi tiết commit | 3.3.1, 3.3.2, 3.5.2, 3.6, 3.4.4: chỉ còn ngày và nội dung |
| Lời cảm ơn | Viết xong, còn để trống ngày ký |
| Tóm tắt | Viết xong: 3 đóng góp (bullet), kết quả đóng góp 1 theo số, ứng dụng demo, RAG ghi rõ chưa có kết quả; thêm từ khóa |
| 1.5 | Viết lại theo 3 đóng góp (D21), có đoạn trạng thái thật; 1.7 sửa câu "trọng tâm khoa học" |
| Chương 6 | Dẫn nhập, 6.1 (Bảng 6.1 có 6 hàng, mức độ Đạt / Đạt một phần / Đang thực hiện), 6.2, 6.3, 6.4 |

### Sự cố khi ghi, đã xử lý
- Hai lệnh thay thế trúng cả đoạn khác có cùng cụm chữ: một đoạn Chương 2 (định nghĩa agent) và một khung hướng dẫn của 1.3. Đã hoàn nguyên đúng nguyên văn; Chương 2 không còn thay đổi nào.
- Một lỗi gõ ở đầu 6.3 ("Khoáng") đã sửa thành "Các".

### Cần Hùng quyết
- Chương 6: RQ3 (độ trễ so với gọi trực tiếp), RQ4 (sai số credit trên tập lượt chat) chưa có số, nên ghi "Đạt một phần". Muốn có số thì cần đo thêm (RQ4 đo offline được từ DB, không tốn phí).
- Ngày ký ở Lời cảm ơn, và tên Khoa trong lời cảm ơn (tôi chỉ ghi "quý thầy cô trong Khoa và Trường").
- 1.1.3 vẫn có câu "trọng tâm khoa học của khóa luận" (D20 cũ) và 1.2.1 "trọng tâm khoa học là đánh giá routing proxy": chưa sửa vì ngoài phạm vi đợt 2.

## Review - Khoa (chưa)
