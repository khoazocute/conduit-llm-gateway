# Bộ 30 prompt đánh giá proxy (chốt trước khi chạy thực nghiệm)

Theo CLAUDE.md mục 2: bộ prompt này **khóa cứng** trước khi chạy thực nghiệm tuần 9–10, không sửa giữa chừng để tránh thiên lệch (bias) khi so sánh 3 proxy. Mỗi prompt chạy **3 lần** trên **mỗi proxy** (LiteLLM / Bifrost / Portkey) → 30 × 3 × 3 = 270 lượt gọi API thật, tất cả phải ghi vào bảng `routing_decisions`.

Phân tầng: 12 closed-QA (đúng/sai khách quan) + 6 code + 12 mở, đúng tỷ lệ CLAUDE.md yêu cầu.

**Quy tắc chấm** (nhắc lại từ CLAUDE.md mục 2, không lặp lại ở từng prompt):
- Closed-QA: so khớp đáp án đúng/sai, tự động hoá được — đáp án đúng ghi kèm mỗi câu bên dưới.
- Prompt mở (code + mở): rubric 3 tiêu chí (on-task / độ dài phù hợp / không lỗi), mỗi tiêu chí 0–1 điểm, chấm mù (ẩn tên proxy), 30% mẫu có 2 người chấm độc lập.

---

## A. Closed-QA (12 câu) — kiến thức, toán, logic

### A1. Kiến thức (4 câu)

| ID | Prompt | Đáp án đúng |
|---|---|---|
| Q01 | Thủ đô của Úc (Australia) là gì? | Canberra |
| Q02 | Nguyên tố hóa học có ký hiệu "Na" là gì? | Natri (Sodium) |
| Q03 | Tác phẩm "Truyện Kiều" là của tác giả nào? | Nguyễn Du |
| Q04 | Hành tinh nào trong Hệ Mặt Trời gần Mặt Trời nhất? | Sao Thủy (Mercury) |

### A2. Toán (4 câu)

| ID | Prompt | Đáp án đúng |
|---|---|---|
| Q05 | Tính: 17 × 24 | 408 |
| Q06 | Một hình chữ nhật có chiều dài 12cm, chiều rộng 7cm. Tính diện tích. | 84 cm² |
| Q07 | Giải phương trình: 3x + 5 = 20. x = ? | x = 5 |
| Q08 | Tính 15% của 240 | 36 |

### A3. Logic (4 câu)

| ID | Prompt | Đáp án đúng |
|---|---|---|
| Q09 | Nếu tất cả mèo đều là động vật, và Tom là một con mèo, thì Tom có phải là động vật không? Trả lời Có hoặc Không. | Có |
| Q10 | An cao hơn Bình, Bình cao hơn Chi. Ai thấp nhất trong ba người? | Chi |
| Q11 | Một chiếc taxi màu xanh gây tai nạn vào ban đêm. Nhân chứng nói taxi màu xanh, nhưng 80% taxi trong thành phố màu vàng, chỉ 20% màu xanh. Hỏi: kết luận nào hợp lý hơn — (a) chắc chắn taxi gây tai nạn màu xanh, hay (b) cần cân nhắc khả năng nhân chứng nhìn nhầm vì phần lớn taxi trong thành phố là màu vàng? Chỉ trả lời (a) hoặc (b). | (b) |
| Q12 | Dãy số: 2, 4, 8, 16, ?. Số tiếp theo là gì? | 32 |

---

## B. Code (6 câu)

Chấm theo rubric 3 tiêu chí chung (on-task / độ dài phù hợp / không lỗi) — "không lỗi" ở đây nghĩa là code chạy đúng logic được mô tả, không cần build/run tự động.

| ID | Prompt |
|---|---|
| C01 | Viết hàm Python kiểm tra một số nguyên có phải số nguyên tố hay không. |
| C02 | Viết đoạn code JavaScript đảo ngược một chuỗi (string), không dùng hàm `reverse()` có sẵn. |
| C03 | Đoạn code Python sau bị lỗi cú pháp: `def add(a, b): return a + b print(add(2,3))`. Nêu lỗi và viết lại code đã sửa. |
| C04 | Viết câu lệnh SQL lấy ra 5 khách hàng có tổng đơn hàng (theo cột `amount`) cao nhất, từ bảng `orders(customer_id, amount)`. |
| C05 | Giải thích ngắn gọn thuật toán binary search trên mảng đã sắp xếp, và viết code Python minh hoạ. |
| C06 | Viết hàm (ngôn ngữ bất kỳ) kiểm tra một chuỗi có phải palindrome (đọc xuôi và ngược giống nhau) hay không. |

---

## C. Prompt mở (12 câu) — email, tóm tắt, sáng tạo

### C1. Email (4 câu)

| ID | Prompt |
|---|---|
| E01 | Viết email xin nghỉ phép 2 ngày gửi quản lý vì lý do gia đình, giọng văn lịch sự, chuyên nghiệp. |
| E02 | Viết email phản hồi khách hàng đang phàn nàn vì đơn hàng giao trễ 3 ngày — xin lỗi và đề xuất hướng giải quyết cụ thể. |
| E03 | Viết email mời một đối tác tham dự buổi demo sản phẩm mới vào thứ Năm tuần sau, lúc 14h. |
| E04 | Viết email từ chối một lời mời phỏng vấn vì đã nhận công việc khác, giữ thiện chí để có thể hợp tác sau này. |

### C2. Tóm tắt (4 câu)

| ID | Prompt |
|---|---|
| S01 | Tóm tắt đoạn văn sau trong đúng 3 câu:<br>"Biến đổi khí hậu đang khiến nhiệt độ trung bình toàn cầu tăng lên rõ rệt trong vài thập kỷ qua, chủ yếu do phát thải khí nhà kính từ hoạt động công nghiệp, giao thông và nông nghiệp. Hệ quả là các hiện tượng thời tiết cực đoan như bão, hạn hán và lũ lụt xảy ra thường xuyên hơn, ảnh hưởng trực tiếp đến sản xuất nông nghiệp và an ninh lương thực ở nhiều quốc gia, đặc biệt là các nước đang phát triển ven biển như Việt Nam. Nhiều chuyên gia cho rằng nếu không có hành động cắt giảm phát thải quyết liệt trong thập kỷ tới, các mục tiêu kiểm soát nhiệt độ toàn cầu theo Thỏa thuận Paris sẽ khó đạt được." |
| S02 | Tóm tắt đoạn hội thoại họp nhóm sau thành danh sách các việc cần làm (action items), ghi rõ ai phụ trách:<br>"An: Mình nghĩ tuần này mình nên hoàn thành phần thiết kế giao diện trước, chậm nhất là thứ Sáu. Bình: Ok, còn phần API thì để mình lo, chắc mất khoảng 4 ngày. Chi: Mình sẽ viết test case song song với Bình, xong thì báo lại nhóm qua Slack. An: Được, cuối tuần mình họp lại review chung nhé." |
| S03 | Tóm tắt đoạn trích khoa học sau thành 2-3 câu dễ hiểu cho người không chuyên:<br>"Học sâu (deep learning) là một nhánh của học máy sử dụng mạng nơ-ron nhân tạo nhiều lớp để tự động trích xuất đặc trưng từ dữ liệu thô, thay vì phải thiết kế đặc trưng thủ công như các phương pháp học máy truyền thống. Nhờ khả năng học biểu diễn phân cấp này, học sâu đã đạt được những đột phá lớn trong nhận diện hình ảnh, xử lý ngôn ngữ tự nhiên và nhận dạng giọng nói trong thập kỷ qua." |
| S04 | Tóm tắt đánh giá sản phẩm sau, nêu đúng 3 điểm tích cực và 3 điểm tiêu cực dưới dạng gạch đầu dòng:<br>"Mình dùng chiếc tai nghe này được 2 tuần. Âm thanh khá chi tiết, bass ổn, đeo êm tai kể cả dùng lâu. Pin trâu, sạc 1 lần dùng được gần 30 tiếng. Tuy nhiên app đi kèm hay bị lag, kết nối Bluetooth thỉnh thoảng bị ngắt giữa chừng khi đang nghe, và mic khi gọi điện nghe hơi rè. Giá thì hơi cao so với phân khúc." |

### C3. Sáng tạo (4 câu)

| ID | Prompt |
|---|---|
| R01 | Viết một đoạn quảng cáo ngắn (khoảng 50 từ) cho một quán cà phê mới mở tại Đà Lạt. |
| R02 | Sáng tác một bài thơ lục bát ngắn (4-6 câu) về mùa thu Hà Nội. |
| R03 | Viết đoạn mở đầu (1 đoạn văn) cho một truyện trinh thám lấy bối cảnh Sài Gòn thập niên 1960. |
| R04 | Đặt tên và viết 1 câu slogan cho một startup công nghệ giáo dục dành cho trẻ em Việt Nam. |

---

## Ghi chú thực thi

- Mỗi proxy (litellm/bifrost/portkey) chạy đủ 30 prompt × 3 lần = 90 lượt/proxy, tổng 270 lượt.
- Ghi mọi lượt gọi vào `routing_decisions` (id, message_id, proxy_name, selected_model, predicted_cost, token_input, token_output, response_quality_score, latency_ms) — không bỏ qua dù đang test nhanh.
- Chấm mù: khi đưa cho người chấm (kể cả chính Hùng/Khoa), ẩn cột `proxy_name`, chỉ hiện nội dung trả lời.
- 30% mẫu cần 2 người chấm độc lập để tính % agreement, báo cáo trong khóa luận. Đơn vị "mẫu": **đã chốt theo lượt output** (quyết định D6, bảng quyết định trong `docs/roadmap.md` mục 4) — (12 mở + 6 code) × 3 proxy × 3 lần = 162 output cần chấm tay, 30% ≈ 49 output, chọn ngẫu nhiên rải đều 3 proxy (con số "≈9" ghi trước đây là sai).
