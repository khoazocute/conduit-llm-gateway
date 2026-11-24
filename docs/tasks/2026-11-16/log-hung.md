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

## 23/11/2026 (tiếp 2): đo RQ3, RQ4 và đợt 3

Hùng cho phép đo RQ3 (chi phí dưới $0,01).

| Việc | Kết quả |
|---|---|
| RQ3 (độ trễ Gateway) | `experiments/scripts/rq3_latency.py`, dữ liệu `experiments/results/rq3-latency-20261123T135351.json`. 88 lượt gọi thật (44 gpt-4o-mini, 44 claude-haiku) + 60 lượt mô hình giả. Proxy thêm +62,7 ms (OpenAI) và +102,9 ms (Anthropic); tầng ứng dụng +11,5 ms. Tổng khoảng 74 và 114 ms, dưới ngưỡng 300-500 ms. Mỗi đường chỉ 20 lượt, độ lệch chuẩn đường OpenAI trực tiếp 176 ms nên con số OpenAI chỉ cho thấy độ lớn |
| RQ4 (sai số credit) | Tính offline từ DB: 912/912 lượt thành công khớp ceil(token × hệ số), ở cả `messages.credit_charged` và `credit_transactions`; sai số 0%. 22 đơn paid khớp 22 giao dịch cộng credit; số dư nhỏ nhất 0. 5 lượt đầu (19/09, 29/09) có cost_upstream = 0 vì chưa tra được đơn giá. Đây là kiểm nhất quán, chưa đối chiếu độc lập với bảng điều khiển nhà cung cấp |
| Chương 2 | Sửa 2.5 và 2.6 theo 3 đóng góp (Hùng cho phép) |
| Chương 4 | Dẫn nhập, 4.1.1-4.1.3, 4.2.1-4.2.5, 4.3, 4.4.1-4.4.3, 4.4.5-4.4.8, 4.5; điền Bảng 4.2 (13 yêu cầu), 4.3, 4.4, 4.5. Bỏ 4.4.4 (RAG, đợt 4) |
| Chương 5 | Dẫn nhập, 5.1.1-5.1.8, 5.3.1-5.3.4, 5.4.1; điền Bảng 5.2 và 5.3, Bảng 6.1 |

### Sự cố đã xử lý
- Lần ghi Bảng 6.1 trước đó đã điền nhầm vào Bảng 5.2 (script chọn nhầm bảng theo thứ tự). Đã hoàn nguyên: Bảng 5.2 giờ đúng nội dung RQ3, Bảng 6.1 có 6 hàng.
- Một lệnh thay thế sai chuỗi đã đổi một cụm thành "x" trong 1.2.1; đã viết lại đoạn đó.

### Còn lại, chưa làm
- 3.1.4, 4.4.4, 5.4.2 (RAG, đợt 4); 5.5 Thảo luận; tiểu kết Chương 3 và 5; Phụ lục E, F; dẫn nhập Chương 3.
- Chưa đo: TTFT, độ trễ so với gọi trực tiếp khi có RAG, hành vi khi nhà cung cấp trả 5xx.
- Cần Hùng xem: ghi chú 5.3.3 ghi DB cục bộ không có dòng `invalid_signature`; API key (kịch bản 1 ở Bảng 5.3) chưa kiểm vì DB cục bộ chưa có khóa nào.

## 23/11/2026 (tiếp 3): đợt 4 và phần còn lại

Đã viết: 3.1.4 (lý thuyết RAG, dẫn [5], [9], [11], [18], [25]), 4.4.4 (thiết kế RAG, ghi rõ trạng thái), 5.4.2 (kế hoạch đánh giá RAG, không có số), 5.5 Thảo luận, dẫn nhập Chương 3, tiểu kết Chương 3 và 5, Phụ lục E (40 endpoint, cột 14 bảng), Phụ lục F (đĩa nộp, cài đặt). Không còn placeholder văn bản trong Doc; còn 27 khung hình để Hùng chèn.

- RAG chưa có kết quả: 4.4.4, 5.4.2 và Chương 6 ghi là thiết kế và hiện thực ban đầu. Khi Khoa có số chunking và vector so với đồ thị thì thay 5.4.2 và cập nhật 6.1 đến 6.3.
- 3.1.4 không dẫn tài liệu về graph RAG vì danh mục tham khảo chưa có; nếu cần thì thêm.
- README.md ghi "7 container" nhưng docker-compose.yml có 6 service; Doc ghi 6.

## 23/11/2026 (tiếp 4): kiểm đồng nhất lần cuối

- Đã sửa: mô tả RAG cũ ở 1.2.2 và 1.4.2 (RAG là Must-have, đóng góp thứ hai); "item" đổi thành "câu"; "bộ prompt/rubric" đổi thành "bộ đề" ở phần phân công; thêm dẫn chiếu cho Hình 3.2, 3.3, 4.2 đến 4.6, 4.8 đến 4.11, 5.1, 5.9 đến 5.12 và Bảng 4.4, 4.5, 5.2; Danh mục viết tắt thêm CEL, HMAC, HNSW, HTTP, IVFFlat, JPA, MoSCoW, MRR, RBAC và bỏ CRUD, USP (không dùng); căn giữa các hình 5.2 đến 5.8.
- Hình 5.9 đến 5.12 trong Doc có tiêu đề cũ nằm trong ảnh ("Hình 5.6 đến 5.9") và Hình 5.11 ghi Portkey 791 µUSD, Bifrost 568 µUSD, lệch bảng (793 và 562). Đã vẽ lại không tiêu đề trong ảnh, số khớp bảng: `docs/figures/`, mã `experiments/analysis/make_report_figures.py`. Chưa thay vào Doc (connector không chèn được ảnh từ máy).
- Hình 4.1 (use case) có chức năng "Theo dõi doanh thu" chưa hiện thực; các hình 3.2, 4.1, 4.2, 4.4, 4.13 là dải rất rộng nên chữ nhỏ khi co về 380 pt.
- Còn lại ngoài phạm vi: Chương 2 vẫn có liệt kê "(1) ... (2)" trong một đoạn (2.1.2); các trang hướng dẫn bố cục đầu tài liệu còn dấu "—" và "–".

## 24/11/2026: rà toàn bộ hình theo góp ý của thầy

Yêu cầu của thầy: mọi hình phải được dẫn chiếu và diễn giải trong nội dung.

- Đã xem lại cả 29 hình trong Doc. Mỗi hình nay có một đoạn diễn giải đặt ngay trước ảnh (Hình 2.1, 3.1 đến 3.3, 4.1 đến 4.13, 5.1 đến 5.12), kiểm lại bằng script: 29/29 có đoạn bắt đầu bằng "Hình x.y", canh đều, không thành bullet. Với hình thể hiện thiết kế chưa hiện thực xong (4.1 đến 4.4, 4.11) đoạn diễn giải ghi rõ phần nào đã làm, phần nào chưa.
- Hình lệch nội dung với văn bản và code, đã vẽ lại vào `docs/figures/` (mã `experiments/analysis/make_diagrams.py`, `make_report_figures.py`): 3.2 (ghi sai ngày khóa luật là 14/10, đúng là 11/09/2026), 3.3 (còn "closed-QA"), 4.5 (RAG ghi Should-have), 4.7 và 4.8 (có bước kiểm credit trước khi gọi, code không làm), 4.10 (sai đường dẫn webhook và tên kết quả log), 4.11 (thiếu nhánh đồ thị), 4.13 (sai đường dẫn trang), 5.9 đến 5.12 (tiêu đề trong ảnh còn số cũ, Hình 5.11 lệch số với bảng). Chưa thay vào Doc vì connector không chèn được ảnh từ máy.
- Ảnh chụp giao diện Hình 5.2, 5.3, 5.6 hiện email cá nhân của Khoa; nên che hoặc chụp lại bằng tài khoản demo.
- Hình 4.12 (ERD) là bản gốc, chưa có cột version (credit_wallets) và instructions (agents); đoạn diễn giải đã ghi rõ.

## Review - Khoa (chưa)
