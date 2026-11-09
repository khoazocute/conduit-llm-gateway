**HƯỚNG DẪN SỬ DỤNG BẢN BỐ CỤC**

*(Xóa toàn bộ phần này trước khi gửi bản chính thức)*

**1\. Cách làm việc chung trên file**

– Các khung nền xanh nhạt là gợi ý nội dung, người phụ trách, số trang dự kiến và trạng thái. Chúng dùng kiểu chữ (style) riêng tên "HuongDan" để xóa một lần: Home → Styles → chuột phải vào "HuongDan" → Select All → nhấn Delete.

– Đánh dấu trạng thái bằng cách thay ☐ thành ☒ ở dòng "Trạng thái" của mỗi mục.

– Viết đè lên dòng "\[Viết nội dung … tại đây\]". Thay khung nét đứt "\[Chèn hình …\]" bằng hình thật, giữ nguyên dòng chú thích bên dưới.

– Nên để file trên OneDrive/SharePoint để hai người cùng mở và soạn đồng thời; khi sửa phần của người kia, bật Review → Track Changes.

– Mục lục, Danh mục hình, Danh mục bảng là trường tự động: sau khi viết xong, nhấn Ctrl+A rồi F9 (chọn "Update entire table") để cập nhật.

– Tiêu đề chương/mục dùng Heading 1–4 (đã đánh số tay). Khi thêm hoặc xóa mục, nhớ đánh lại số cho các mục phía sau. Chú thích hình dùng style "Chu thich Hinh", chú thích bảng dùng "Chu thich Bang" thì mới hiện trong danh mục.

**2\. Phân công và theo dõi tiến độ (đề xuất – nhóm điều chỉnh)**

| Phần | Phụ trách | Số trang | Hạn bản nháp | Trạng thái |
| ----- | ----- | ----- | ----- | ----- |
| Tóm tắt khóa luận | Hùng & Khoa | 1–2 |  |  |
| Chương 1\. Mở đầu | Khoa | 6–8 |  |  |
| Chương 2\. Tổng quan | Khoa | 10–12 |  |  |
| Chương 3\. Cơ sở lý thuyết và phương pháp nghiên cứu | Hùng (lý thuyết kiến trúc/hạ tầng), Khoa (RAG, phương pháp thí nghiệm & chấm điểm) | 18–22 |  |  |
| Chương 4\. Phân tích, thiết kế hệ thống | Khoa (phân tích yêu cầu, use case, RAG, giao diện), Hùng (kiến trúc, thiết kế backend) | 18–20 |  |  |
| Chương 5\. Hiện thực và thử nghiệm đánh giá | Hùng (backend, hạ tầng, triển khai, đánh giá Gateway), Khoa (frontend, mở rộng, chất lượng response, kiểm thử) | 16–18 |  |  |
| Chương 6\. Kết luận và hướng phát triển | Hùng (tổng hợp), Khoa (rà soát phần nghiên cứu) | 3 |  |  |
| Tài liệu tham khảo, Phụ lục, danh mục | Hùng & Khoa | – |  |  |
| Tổng phần nội dung |  | ≈ 72–85 |  |  |

*Phân công theo đúng mảng chuyên môn mỗi người đã làm, bám sát kế hoạch thực hiện trong đề cương: Hùng phụ trách backend, CSDL, hạ tầng 3 proxy, bảo mật, triển khai; Khoa phụ trách tổng quan, bộ prompt/rubric, frontend, RAG và các chức năng mở rộng. Vì nhiều chương vừa có phần kiến trúc/backend vừa có phần nghiên cứu/frontend, mỗi mục cấp 2–3 vẫn chỉ ghi một người phụ trách duy nhất (xem khung gợi ý tại từng mục); chỉ các mục tổng hợp nhiều mục con (ví dụ "Thiết kế chi tiết", "Hiện thực hệ thống") mới ghi cả hai tên kèm số mục cụ thể của từng người. Tổng khối lượng: Khoa ≈ 48 trang, Hùng ≈ 38 trang (lệch về Khoa do phụ trách frontend và nghiên cứu trải khắp các chương). Phụ lục 2 yêu cầu phần nội dung tối thiểu 50 trang, không nên vượt 100 trang.*

**3\. Quy định trình bày (Phụ lục 2\) – đã cài sẵn trong file**

– Times New Roman 13pt, giãn dòng 1.5; lề trên 3 cm, dưới 3,5 cm, trái 3,5 cm, phải 2 cm.

– Tiêu đề chương in đậm cỡ 14; mục cấp 2, 3 in đậm cỡ 13\. Đánh số bằng số Ả-rập (3.1, 3.1.1), không dùng số La Mã.

– Không đánh số trang các trang: Thông tin hội đồng, Lời cảm ơn, Mục lục, các danh mục. Đánh số từ Tóm tắt khóa luận, giữa bên dưới.

– Hình, bảng đánh số theo chương (Hình 2.1, Bảng 2.1); mỗi hình/bảng có chú thích và nêu nguồn. Chú thích (footnote) đặt cuối trang.

– Tài liệu tham khảo theo chuẩn IEEE, tách riêng tiếng Việt và tiếng Anh, xếp theo alphabet tên tác giả.

**4\. Các điểm cần thống nhất (phát hiện khi đối chiếu đề cương)**

– Credit và token: đề cương quy định đơn vị trong ví là "credit" (không gọi là token để tránh hiểu lầm), nhưng nhiều chỗ vẫn ghi "ví token", "default token", "nạp thêm token". Thống nhất: "credit" cho ví/tặng kèm/nạp thêm; "token" chỉ dùng cho usage thượng nguồn.

– Markup và lợi nhuận biên: markup 50% tương ứng lợi nhuận biên ≈ 33,3% (đề cương mục 2.2). Mục chức năng Admin và kịch bản demo lại ghi "lợi nhuận biên 50%" — cần sửa.

– Cổng thanh toán: Mock Payment Gateway là Must-have, VNPay sandbox là Should-have; mục chức năng User lại ghi VNPay là "cổng duy nhất".

– Pool model: đề cương lúc ghi "hai tầng", lúc ghi "ba tầng" (rẻ – trung – đắt).

– Bộ prompt: ghi "4 loại" nhưng số lượng chỉ chia cho 3 nhóm; 6 prompt code chưa có cách chấm.

– Tên đề tài: tên tiếng Anh có "in Vietnam" nhưng tên tiếng Việt không có "tại Việt Nam" — xác nhận với GVHD.

– Thuật ngữ vai trò: dùng thống nhất "Creator" (đề cương có chỗ ghi "Vender").

– Số trích dẫn trong đề cương bị lệch (ví dụ Claude được dẫn \[13\] nhưng \[13\] là Gemini; OpenRouter dẫn \[8\] nhưng \[8\] là Poe). Khi viết, dùng danh mục tài liệu tham khảo đã đánh số lại ở cuối file này.

**5\. Quy ước thuật ngữ dùng trong bài**

| Thuật ngữ gốc | Dùng trong bài | Thuật ngữ gốc | Dùng trong bài |
| ----- | ----- | ----- | ----- |
| Cosine similarity | Độ tương đồng cosine | Publish | Xuất bản |
| Default credit | Credit tặng kèm | Quota | Hạn mức sử dụng |
| Fallback | Cơ chế dự phòng | Rate limiting | Giới hạn tần suất |
| Knowledge base | Cơ sở tri thức | Re-ranking | Xếp hạng lại |
| Markup | Phụ giá | Routing | Định tuyến |
| Marketplace | Sàn agent | Streaming | Truyền theo luồng |
| Monetization | Thương mại hóa | Top-up | Nạp thêm |
| Credit wallet | Ví credit | Introduction | Phần giới thiệu (thay cho system prompt) |

**ĐẠI HỌC QUỐC GIA TP. HỒ CHÍ MINH**  
**TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN**  
**KHOA \<TÊN KHOA\>**

**NGUYỄN VĂN LÊ HÙNG**

**VÕ ĐĂNG KHOA**

**KHÓA LUẬN TỐT NGHIỆP**

**THIẾT KẾ, HIỆN THỰC VÀ ĐÁNH GIÁ NỀN TẢNG LLM GATEWAY ĐA MÔ HÌNH CHO MARKETPLACE AI AGENT**

**Design, Implementation, and Evaluation of a Multi-Model LLM Gateway Platform for an AI Agent Marketplace in Vietnam**

**KỸ SƯ/CỬ NHÂN NGÀNH \<TÊN NGÀNH\>**

**TP. HỒ CHÍ MINH, 2026**  
**ĐẠI HỌC QUỐC GIA TP. HỒ CHÍ MINH**  
**TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN**  
**KHOA \<TÊN KHOA\>**

**NGUYỄN VĂN LÊ HÙNG – 23520570**

**VÕ ĐĂNG KHOA – 23520758**

**KHÓA LUẬN TỐT NGHIỆP**

**THIẾT KẾ, HIỆN THỰC VÀ ĐÁNH GIÁ NỀN TẢNG LLM GATEWAY ĐA MÔ HÌNH CHO MARKETPLACE AI AGENT**

**Design, Implementation, and Evaluation of a Multi-Model LLM Gateway Platform for an AI Agent Marketplace in Vietnam**

**KỸ SƯ/CỬ NHÂN NGÀNH \<TÊN NGÀNH\>**

> > > > > > **GIẢNG VIÊN HƯỚNG DẪN**

> > > > > > **TS. NGUYỄN THANH BÌNH**

> > > > > > **ThS. TRẦN VĨNH KHIÊM**

**TP. HỒ CHÍ MINH, 2026**  
**THÔNG TIN HỘI ĐỒNG CHẤM KHÓA LUẬN TỐT NGHIỆP**

Hội đồng chấm khóa luận tốt nghiệp, thành lập theo Quyết định số …………………… ngày ………………….. của Hiệu trưởng Trường Đại học Công nghệ Thông tin.

1\. ……………………………………… – Chủ tịch.

2\. ……………………………………… – Thư ký.

3\. ……………………………………… – Ủy viên.

4\. ……………………………………… – Ủy viên.

**LỜI CẢM ƠN**

**Phụ trách:** Hùng & Khoa   \|   Dự kiến: 0,5–1 trang. Cảm ơn GVHD (TS. Nguyễn Thanh Bình, ThS. Trần Vĩnh Khiêm), Khoa, gia đình…; cuối trang ghi "TP. Hồ Chí Minh, ngày … tháng … năm 2026" và tên hai sinh viên.  
\[Viết nội dung Lời cảm ơn tại đây\]

**MỤC LỤC**

**DANH MỤC HÌNH**

**DANH MỤC BẢNG**

**DANH MỤC TỪ VIẾT TẮT**

– Đã điền sẵn theo thuật ngữ trong đề cương, xếp theo alphabet. Phụ lục 2: không viết tắt cụm từ dài hoặc ít xuất hiện — xóa các dòng không dùng, bổ sung khi viết.

| Từ viết tắt | Tiếng Anh | Nghĩa tiếng Việt |
| ----- | ----- | ----- |
| ABAC | Attribute-Based Access Control | Kiểm soát truy cập theo thuộc tính |
| AES-GCM | Advanced Encryption Standard – Galois/Counter Mode | Chuẩn mã hóa AES, chế độ GCM |
| API | Application Programming Interface | Giao diện lập trình ứng dụng |
| BYOK | Bring Your Own Key | Cơ chế tự mang khóa API riêng |
| CI/CD | Continuous Integration / Continuous Delivery | Tích hợp và triển khai liên tục |
| CRUD | Create, Read, Update, Delete | Các thao tác dữ liệu cơ bản |
| CSDL | – | Cơ sở dữ liệu |
| ERD | Entity Relationship Diagram | Sơ đồ thực thể – quan hệ |
| JWT | JSON Web Token | Chuẩn token xác thực dạng JSON |
| LLM | Large Language Model | Mô hình ngôn ngữ lớn |
| MVP | Minimum Viable Product | Sản phẩm khả dụng tối thiểu |
| QA | Question Answering | Hỏi đáp |
| RAG | Retrieval-Augmented Generation | Sinh tăng cường truy xuất |
| RQ | Research Question | Câu hỏi nghiên cứu |
| SaaS | Software as a Service | Phần mềm dưới dạng dịch vụ |
| SDK | Software Development Kit | Bộ công cụ phát triển phần mềm |
| SSE | Server-Sent Events | Sự kiện gửi từ máy chủ |
| TTFT | Time To First Token | Thời gian đến token đầu tiên |
| UML | Unified Modeling Language | Ngôn ngữ mô hình hóa thống nhất |
| USP | Unique Selling Proposition | Điểm khác biệt cốt lõi |

# **TÓM TẮT KHÓA LUẬN**

**Phụ trách:** Hùng & Khoa   **\|   Dự kiến:** 1–2 trang (theo Phụ lục 2\)   **\|   Viết sau cùng**  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết (theo thứ tự):**  
– Vấn đề nghiên cứu: rào cản khai thác LLM và khoảng trống của các sàn agent tại Việt Nam.  
– Hướng tiếp cận: LLM Gateway đa mô hình \+ sàn agent (Conduit); đánh giá có kiểm soát 3 routing proxy mã nguồn mở.  
– Cách giải quyết: thực nghiệm 30 prompt × 3 proxy × 3 lần với quy tắc quyết định khóa trước; kiến trúc microservice, hạch toán credit ba tầng, thanh toán idempotent.  
– Kết quả chính bằng con số: proxy được chọn và lý do, overhead Gateway, sai số billing, kết quả webhook, khả năng chịu tải.  
\[Viết nội dung Tóm tắt khóa luận tại đây\]

# **Chương 1\. MỞ ĐẦU**

**Phụ trách:** Khoa   **\|   Dự kiến:** 6–8 trang  
**Cần viết:**  
– Tương ứng phần MỞ ĐẦU (Problem Statement) trong Phụ lục 2: lý do chọn đề tài, mục đích, đối tượng và phạm vi nghiên cứu.  
– Giới thiệu tên hệ thống "Conduit" ngay trong chương này (đề cương dùng tên Conduit từ mục 1.1.3 mà chưa giới thiệu).  
\[Đoạn dẫn nhập chương: 3–5 câu giới thiệu nội dung chương\]

## **1.1. Bối cảnh và lý do chọn đề tài**

**Phụ trách:** Khoa   **\|   Dự kiến:** 2–3 trang   **\|   Nguồn:** Đề cương mục 1 (mở đầu), 1.3, 1.4

### **1.1.1. Sự phát triển của mô hình ngôn ngữ lớn và AI agent**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Sự phổ biến của LLM (GPT, Claude, Gemini) và xu hướng AI agent cá nhân hóa theo tác vụ.  
– Các nền tảng tạo agent no-code (GPT Store, Google AI Studio) mở ra thị trường phân phối trợ lý AI chuyên biệt.  
\[Viết nội dung mục 1.1.1 tại đây\]

### **1.1.2. Rào cản đối với người dùng phổ thông**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Ba rào cản: (1) thiếu kiến thức prompt; (2) không tự chuyên biệt hóa (customize) được LLM; (3) không tự triển khai LLM với dữ liệu riêng.  
– Rào cản chi phí: gói thuê bao \~500.000 VNĐ/tháng trong khi nhu cầu thực tế mang tính nhất thời, cường độ thấp → nêu lý do mô hình trả theo mức dùng (credit) hợp lý hơn.  
**Lưu ý:**  
– Con số 500.000 VNĐ/tháng cần dẫn nguồn (trang giá chính thức, ghi ngày truy cập).  
\[Viết nội dung mục 1.1.2 tại đây\]

### **1.1.3. Khoảng trống tại thị trường Việt Nam**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Nêu ngắn gọn 6 vấn đề thực trạng (đề cương 1.3): phân mảnh nhà cung cấp, quản lý API key, rào cản tạo agent, thiếu thương mại hóa tại VN, khó kiểm soát chi phí, hạn chế loại agent.  
– Kết luận bằng lý do thực hiện đề tài (đề cương 1.4) — viết thành đoạn văn, không liệt kê lại toàn bộ (phân tích chi tiết để ở Chương 2).  
\[Viết nội dung mục 1.1.3 tại đây\]

## **1.2. Mục tiêu đề tài**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1 trang   **\|   Nguồn:** Đề cương 2.1.2

### **1.2.1. Mục tiêu tổng quát**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– 1 đoạn: thiết kế, hiện thực và đánh giá nền tảng LLM Gateway đa mô hình kết hợp sàn AI agent cho thị trường Việt Nam; trọng tâm khoa học là đánh giá và lựa chọn routing proxy mã nguồn mở.  
\[Viết nội dung mục 1.2.1 tại đây\]

### **1.2.2. Mục tiêu cụ thể**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Sáu module nghiệp vụ (sàn agent, tạo agent, RAG, thanh toán – ví credit, LLM Gateway, quản trị).  
– Các mục tiêu kỹ thuật: đánh giá 3 routing proxy; xây dựng Gateway; RAG cơ bản (Should-have); streaming SSE; API công khai \+ widget iframe; bảo mật (AES, JWT, rate limit, chống prompt injection cơ bản).  
\[Viết nội dung mục 1.2.2 tại đây\]

## **1.3. Câu hỏi nghiên cứu và tiêu chí đánh giá**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1–1,5 trang   **\|   Nguồn:** Đề cương 2.1.1, Bảng 3  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Trình bày 5 câu hỏi nghiên cứu (RQ1–RQ5), mỗi RQ gắn với tiêu chí đo và ngưỡng mục tiêu (Bảng 1.1).  
– Chỉ nêu ở mức tổng quan; định nghĩa chỉ số và phương pháp đo chi tiết để ở Chương 3\.  
**Lưu ý:**  
– Tiêu chí "Khả năng chịu tải" trong Bảng 3 đề cương chưa có RQ tương ứng → hoặc bổ sung RQ6, hoặc ghi rõ đây là tiêu chí phụ.  
\[Viết nội dung mục 1.3 tại đây\]

*Bảng 1.1: Câu hỏi nghiên cứu và tiêu chí đánh giá tương ứng (Nguồn: nhóm thực hiện)*

| RQ | Câu hỏi nghiên cứu | Tiêu chí đo | Mục tiêu |
| ----- | ----- | ----- | ----- |
| RQ1 | Trong cùng điều kiện (cùng pool model, cùng bộ 30 prompt), proxy nào trong LiteLLM, Bifrost, Portkey đạt hiệu quả tốt nhất trên hai trục token spend và chất lượng response? | Token input/output, chi phí quy đổi; tỷ lệ đúng closed-QA, điểm rubric | Chỉ ra proxy tối ưu theo quy tắc quyết định khóa trước |
| RQ2 | Cơ chế định tuyến của từng proxy ảnh hưởng ra sao đến việc chọn model trên cùng bộ prompt? | Phân bố model được chọn theo loại prompt; consistency rate | Mô tả, so sánh định lượng |
| RQ3 | Gateway thêm bao nhiêu độ trễ so với gọi trực tiếp nhà cung cấp, có khác nhau giữa các provider không? | Overhead latency (OpenAI, Anthropic); TTFT (mean, p95) | \< 300–500 ms (không RAG) |
| RQ4 | Cơ chế tính và trừ credit có chính xác so với usage nhà cung cấp báo về không? | Sai số credit trừ so với token thực tế | Sai số \< 1% |
| RQ5 | Xử lý webhook thanh toán có tránh lỗi khi bị gọi trùng không? | Tỷ lệ callback trùng không bị cộng credit hai lần | 100% |

\[Nhận xét / diễn giải bảng\]

## **1.4. Đối tượng và phạm vi nghiên cứu**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1,5–2 trang   **\|   Nguồn:** Đề cương 1.6, 2.3.1, 2.3.2

### **1.4.1. Đối tượng nghiên cứu**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Đối tượng nghiên cứu: các giải pháp LLM routing proxy mã nguồn mở (LiteLLM, Bifrost, Portkey AI Gateway) và kiến trúc LLM Gateway cho sàn agent.  
– Đối tượng sử dụng hệ thống: Admin, Creator, User (chỉ giới thiệu 1–2 câu mỗi vai trò; bảng chi tiết để ở Chương 4).  
\[Viết nội dung mục 1.4.1 tại đây\]

### **1.4.2. Phạm vi nghiên cứu**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Phân tầng phạm vi theo MoSCoW: Must-have / Should-have / Could-have (đề cương 2.3.1).  
– Nhấn mạnh: vòng nghiệp vụ khép kín (tạo → mua → dùng → trừ credit) \+ đánh giá 3 proxy là trọng tâm.  
\[Viết nội dung mục 1.4.2 tại đây\]

### **1.4.3. Giới hạn đề tài**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Không sinh video; BYOK chỉ ở mức khái niệm/demo; quy mô demo vài trăm người dùng đồng thời; không tích hợp MoMo; bộ thực nghiệm 30 prompt chỉ cho kết luận mức mô tả; dùng LiteLLM ≥ v1.83.0 do sự cố supply chain tháng 3/2026.  
\[Viết nội dung mục 1.4.3 tại đây\]

## **1.5. Đóng góp của khóa luận**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1 trang   **\|   Nguồn:** Đề cương 1.5  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Đóng góp chính: đánh giá thực nghiệm có kiểm soát và lựa chọn routing proxy mã nguồn mở (quy trình: giả thuyết → thực nghiệm → quy tắc quyết định khóa trước → kết luận định lượng).  
– Hạ tầng kỹ thuật hỗ trợ (không phải đóng góp nghiên cứu độc lập): cách ly dữ liệu đa khách thuê, hạch toán credit ba tầng, ABAC, Provider Adapter \+ Fallback, Payment Adapter.  
**Lưu ý:**  
– Viết đóng góp ở dạng khẳng định kết quả sau khi có số liệu Chương 5 (cập nhật lại mục này cuối cùng).  
\[Viết nội dung mục 1.5 tại đây\]

## **1.6. Cấu trúc khóa luận**

**Phụ trách:** Khoa   **\|   Dự kiến:** 0,5 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Mỗi chương 1–2 câu mô tả nội dung. Cập nhật lại sau khi chốt bố cục cuối.  
\[Viết nội dung mục 1.6 tại đây\]

## **1.7. Tiểu kết chương**

**Phụ trách:** Khoa   **\|   Dự kiến:** 0,5 trang  
– Tóm tắt 1 đoạn những gì chương đã trình bày và dẫn sang chương tiếp theo.  
\[Viết nội dung tiểu kết chương tại đây\]

# **Chương 2\. TỔNG QUAN**

**Phụ trách:** Khoa   **\|   Dự kiến:** 10–12 trang  
**Cần viết:**  
– Tương ứng phần TỔNG QUAN (Literature review / Related work): phân tích các nghiên cứu và sản phẩm trong, ngoài nước; nêu vấn đề còn tồn tại; chỉ ra vấn đề đề tài tập trung giải quyết.  
\[Đoạn dẫn nhập chương: 3–5 câu giới thiệu nội dung chương\]

## **2.1. Các khái niệm cơ bản**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1,5 trang   **\|   Nguồn:** Đề cương 1.2

### **2.1.1. LLM Gateway**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Định nghĩa middleware giữa client và nhiều nhà cung cấp LLM; so sánh với API Gateway truyền thống (Nginx, AWS API Gateway); các chức năng đặc thù: quản lý key, định tuyến, đếm token, quota, streaming.  
\[Viết nội dung mục 2.1.1 tại đây\]

### **2.1.2. Sàn AI agent (Agent Marketplace)**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Mô hình kinh doanh nền tảng; trong phạm vi đề tài, agent \= introduction \+ cấu hình mô hình \+ cơ sở tri thức (RAG) \+ thông tin meta (tiêu đề, mô tả, giá).  
\[Viết nội dung mục 2.1.2 tại đây\]

### **2.1.3. Routing proxy**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Lớp trung gian mã nguồn mở đứng trước nhiều LLM, tự chọn model cho từng request theo tiêu chí cấu hình sẵn (chi phí, độ trễ, rule-based). Phân biệt rõ với LLM Gateway (Gateway của đề tài tích hợp 1 routing proxy bên trong).  
\[Viết nội dung mục 2.1.3 tại đây\]

## **2.2. Các nghiên cứu học thuật liên quan**

**Phụ trách:** Khoa   **\|   Dự kiến:** 3 trang   **\|   Nguồn:** Đề cương 1.1.1

### **2.2.1. Kiến trúc microservice, API Gateway và cơ chế chống lỗi lan truyền**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Richardson \[Microservices Patterns\]; Montesi & Weber (circuit breaker, discovery, API gateway); Hasselbring & Steinacker (quản lý dữ liệu phân tán).  
\[Viết nội dung mục 2.2.1 tại đây\]

### **2.2.2. Định tuyến mô hình ngôn ngữ lớn**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Tổng quan các hướng định tuyến/cascade giữa nhiều LLM để tối ưu chi phí – chất lượng.  
**Lưu ý:**  
– Đề cương CHƯA có tài liệu học thuật về LLM routing — hội đồng dễ hỏi vì đây là đóng góp chính. Gợi ý tìm đọc: FrugalGPT (Chen, Zaharia, Zou, 2023\) và RouteLLM (Ong et al., 2024). Nhóm tự kiểm tra lại thông tin trích dẫn trước khi đưa vào.  
\[Viết nội dung mục 2.2.2 tại đây\]

### **2.2.3. Sinh tăng cường truy xuất (RAG) và biểu diễn vector**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Lewis et al. (RAG); Karpukhin et al. (Dense Passage Retrieval); Wang et al. (Multilingual E5); Es et al. (RAGAS).  
\[Viết nội dung mục 2.2.3 tại đây\]

### **2.2.4. Kiểm soát truy cập trong hệ thống SaaS đa khách thuê**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Tsai et al. — cách ly dữ liệu và kiểm soát truy cập multi-tenant; liên hệ với việc nhiều agent dùng chung CSDL vector.  
\[Viết nội dung mục 2.2.4 tại đây\]

## **2.3. Các sản phẩm và nền tảng thực tế**

**Phụ trách:** Khoa   **\|   Dự kiến:** 3 trang   **\|   Nguồn:** Đề cương 1.1.2

### **2.3.1. Các nền tảng trong nước**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– FPT.AI, VinAI Chatbot Platform (B2B, chi phí cao, không có sàn agent mở); các chatbot đóng gói riêng lẻ.  
\[Viết nội dung mục 2.3.1 tại đây\]

### **2.3.2. Các nền tảng quốc tế**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– GPT Store, Google AI Studio & Gems, Poe.com (đối thủ gần nhất), OpenRouter, Dify.ai, LibreChat, Chatbase. Mỗi nền tảng: điểm mạnh – hạn chế đối với thị trường VN.  
**Lưu ý:**  
– Chatbase có trong bảng so sánh của đề cương nhưng chưa được mô tả — cần bổ sung 2–3 câu.  
\[Viết nội dung mục 2.3.2 tại đây\]

### **2.3.3. Các routing proxy mã nguồn mở**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– LiteLLM (Python, cost/latency/usage-based, simple-shuffle — baseline); Bifrost (Go, hiệu năng, failover, semantic caching); Portkey AI Gateway (TypeScript, conditional routing rule-based).  
– Các ứng viên bị loại và lý do: OpenRouter (SaaS, không self-host), Cloudflare AI Gateway / TrueFoundry / Helicone (thiên về observability), Envoy AI Gateway (quá phức tạp so với thời lượng).  
– Ghi chú sự cố supply chain của LiteLLM (bản 1.82.7, 1.82.8 trên PyPI) và phiên bản nhóm sử dụng.  
\[Viết nội dung mục 2.3.3 tại đây\]

*Bảng 2.1: So sánh ba routing proxy mã nguồn mở được lựa chọn (Nguồn: nhóm thực hiện)*

| Tiêu chí | LiteLLM | Bifrost | Portkey AI Gateway |
| ----- | ----- | ----- | ----- |
| Ngôn ngữ | Python | Go | TypeScript |
| Chiến lược định tuyến | Cost-based, latency-based, usage-based (least-busy), simple-shuffle | Load balancing, automatic failover, semantic caching | Conditional routing theo luật cấu hình, fallback, load balancing |
| Phiên bản sử dụng | ≥ 1.83.0 |  |  |
| Giấy phép |  |  |  |
| Ghi chú | Baseline so sánh | Benchmark của hãng công bố nhanh hơn LiteLLM | Bản mã nguồn mở |

\[Nhận xét / diễn giải bảng\]

## **2.4. Đánh giá đối chứng các nền tảng**

**Phụ trách:** Khoa   **\|   Dự kiến:** 2 trang   **\|   Nguồn:** Đề cương 1.1.3, Hình 1, Bảng 1

### **2.4.1. Bộ tiêu chí đối chứng**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– 8 tiêu chí chia 2 nhóm: kỹ thuật (đa mô hình LLM, sàn agent, RAG, đa loại agent) và thương mại hóa – phân phối (thanh toán nội địa, nhúng iframe, BYOK, monetize cho creator). Giải thích vì sao chọn từng tiêu chí.  
\[Viết nội dung mục 2.4.1 tại đây\]

*\[Chèn hình tại đây – Hình 2.1\]*

*Hình 2.1: Bộ tiêu chí đối chứng nền tảng AI agent (Nguồn: nhóm thực hiện)*

### **2.4.2. Ma trận so sánh**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Đối chiếu GPT Store, Poe.com, OpenRouter, Chatbase với Conduit; phân tích: mỗi nền tảng bỏ trống ít nhất một nhóm tiêu chí; không nền tảng quốc tế nào hỗ trợ thanh toán nội địa VN.  
**Lưu ý:**  
– Ghi ngày khảo sát cho bảng (tính năng các nền tảng thay đổi thường xuyên). Các ô "Không rõ"/"Không công bố" cần ghi nguồn đã kiểm tra.  
\[Viết nội dung mục 2.4.2 tại đây\]

*Bảng 2.2: So sánh các nền tảng AI agent tiêu biểu (Nguồn: nhóm thực hiện)*

| Tiêu chí | GPT Store | Poe.com | OpenRouter | Chatbase | Conduit |
| ----- | ----- | ----- | ----- | ----- | ----- |
| Đa mô hình LLM (kèm fallback) | Không | Hạn chế (1 model/bot) | Có | Có | Có (đa provider \+ fallback 3 tầng) |
| Credit accounting minh bạch, markup rõ | Không | Có (không công bố %) | Không áp dụng | Có (không công bố %) | Có (markup 50%, minh bạch) |
| Sàn agent (Marketplace) | Có | Có | Không | Không | Có |
| Cơ sở tri thức (RAG) | Có | Hạn chế | Không | Có | Có |
| Nhúng vào hệ thống thứ ba qua UI | Không | Hạn chế | Không | Có | Có |
| Thanh toán nội địa VN | Không | Không | Không | Không | Có |
| BYOK cho enterprise | Không | Không | Có | Không rõ | Có |
| Monetize cho creator | Hạn chế | Có | Không | Không | Có |

\[Nhận xét / diễn giải bảng\]

## **2.5. Vấn đề tồn tại và hướng tiếp cận của đề tài**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1 trang   **\|   Nguồn:** Đề cương 1.3, 1.4  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Tổng hợp các khoảng trống từ 2.2–2.4: (1) chưa có đánh giá độc lập, có kiểm soát giữa các routing proxy mã nguồn mở; (2) chưa có nền tảng hợp nhất gateway đa mô hình \+ sàn agent \+ RAG \+ thương mại hóa nội địa.  
– Nêu hướng tiếp cận của đề tài đối với từng khoảng trống → dẫn sang Chương 3, 4\.  
\[Viết nội dung mục 2.5 tại đây\]

## **2.6. Tiểu kết chương**

**Phụ trách:** Khoa   **\|   Dự kiến:** 0,5 trang  
– Tóm tắt 1 đoạn những gì chương đã trình bày và dẫn sang chương tiếp theo.  
\[Viết nội dung tiểu kết chương tại đây\]

# **Chương 3\. CƠ SỞ LÝ THUYẾT VÀ PHƯƠNG PHÁP NGHIÊN CỨU**

**Phụ trách:** Hùng   **\|   Dự kiến:** 18–22 trang  
**Cần viết:**  
– Tương ứng phần NGHIÊN CỨU THỰC NGHIỆM HOẶC LÍ THUYẾT (Model/Method/Solutions) của Phụ lục 2: cơ sở lí thuyết, giả thiết khoa học và phương pháp nghiên cứu.  
– Phần lý thuyết chỉ trình bày kiến thức thực sự dùng trong hệ thống/thực nghiệm. Phần phương pháp phải đủ chi tiết để người khác lặp lại được thí nghiệm, và được viết TRƯỚC khi có kết quả (ghi rõ ngày khóa quy tắc quyết định).  
– Chương này phân công xen kẽ theo mảng phụ trách thật: Hùng viết phần lý thuyết kiến trúc/hạ tầng (gắn với Chương 4–5 do Hùng hiện thực); Khoa viết phần RAG và toàn bộ phương pháp thiết kế thí nghiệm, chấm điểm (gắn với bộ prompt/rubric do Khoa chuẩn bị).  
\[Đoạn dẫn nhập chương: 3–5 câu giới thiệu nội dung chương\]

## **3.1. Cơ sở lý thuyết**

**Phụ trách:** Hùng (3.1.1–3.1.3, 3.1.5–3.1.6), Khoa (3.1.4)   **\|   Dự kiến:** 8–10 trang

### **3.1.1. Mô hình ngôn ngữ lớn và API của các nhà cung cấp**

**Phụ trách:** Hùng   **\|   Dự kiến:** 2 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Token, cửa sổ ngữ cảnh, cách tính phí theo token input/output.  
– So sánh định dạng API của OpenAI, Anthropic, Google (xác thực, rate limit, cấu trúc message, trường usage trả về) → lý do cần lớp Provider Adapter.  
– Chế độ streaming của từng nhà cung cấp.  
\[Viết nội dung mục 3.1.1 tại đây\]

*Bảng 3.1: So sánh API của các nhà cung cấp LLM (Nguồn: nhóm thực hiện)*

| Đặc điểm | OpenAI | Anthropic | Google Gemini |
| ----- | ----- | ----- | ----- |
| Xác thực |  |  |  |
| Định dạng message |  |  |  |
| Trường usage trả về |  |  |  |
| Streaming |  |  |  |
| Rate limit |  |  |  |

\[Nhận xét / diễn giải bảng\]

### **3.1.2. Kiến trúc API Gateway và microservice**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1,5 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Mẫu API Gateway; giới hạn tần suất (rate limiting); circuit breaker và fallback; mẫu thiết kế Adapter.  
– Liên hệ trực tiếp với thiết kế ở Chương 4\.  
\[Viết nội dung mục 3.1.2 tại đây\]

### **3.1.3. Các chiến lược định tuyến mô hình LLM**

**Phụ trách:** Hùng   **\|   Dự kiến:** 2 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Cost-based, latency-based, usage-based (least-busy), simple-shuffle, conditional/rule-based, load balancing, automatic failover, semantic caching.  
– Với mỗi chiến lược: nguyên lý, ưu – nhược điểm, proxy nào hiện thực.  
**Lưu ý:**  
– Đây là nền tảng lý thuyết cho RQ2 — nên có bảng hoặc hình tổng hợp.  
\[Viết nội dung mục 3.1.3 tại đây\]

*\[Chèn hình tại đây – Hình 3.1\]*

*Hình 3.1: Phân loại các chiến lược định tuyến LLM (Nguồn: nhóm thực hiện)*

### **3.1.4. Sinh tăng cường truy xuất (RAG)**

**Phụ trách:** Khoa   **\|   Dự kiến:** 2 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Chunking (200–500 token, overlap); embedding (text-embedding-3-small, multilingual-e5); độ tương đồng cosine; pgvector; re-ranking bằng cross-encoder; chỉ số Recall@k.  
– Lưu ý ràng buộc: ingestion và retrieval phải dùng chung một mô hình embedding.  
\[Viết nội dung mục 3.1.4 tại đây\]

### **3.1.5. Truyền phản hồi theo luồng với Server-Sent Events**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Cơ chế SSE so với WebSocket/long polling; Spring WebFlux; định nghĩa Time To First Token (TTFT).  
\[Viết nội dung mục 3.1.5 tại đây\]

### **3.1.6. Xác thực, phân quyền và bảo mật**

**Phụ trách:** Hùng   **\|   Dự kiến:** 2 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– JWT (access/refresh token, thuật toán ký), OAuth 2.0 (đăng nhập Google).  
– RBAC so với ABAC; cách ly dữ liệu đa khách thuê.  
– Mã hóa đối xứng AES-GCM; prompt injection; xác thực chữ ký và idempotency cho webhook thanh toán.  
\[Viết nội dung mục 3.1.6 tại đây\]

## **3.2. Công nghệ sử dụng**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1,5 trang   **\|   Nguồn:** Đề cương 2.2  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Mỗi công nghệ: vai trò trong hệ thống \+ lý do lựa chọn (1–2 câu). Có thể gộp thành bảng để tiết kiệm trang.  
\[Viết nội dung mục 3.2 tại đây\]

*Bảng 3.2: Công nghệ sử dụng trong hệ thống (Nguồn: nhóm thực hiện)*

| Thành phần | Công nghệ | Vai trò / lý do lựa chọn |
| ----- | ----- | ----- |
| Frontend Portal | Next.js, React, Tailwind CSS |  |
| Backend Gateway | Spring Boot 3, Spring AI, Spring Security, Spring WebFlux |  |
| AI Service | Python, FastAPI |  |
| Cơ sở dữ liệu | PostgreSQL \+ pgvector |  |
| Cache / rate limit | Redis |  |
| Lưu trữ tệp | Object Storage (S3-compatible) |  |
| Routing proxy | LiteLLM / Bifrost / Portkey (proxy được chọn) |  |
| Thanh toán | Mock Payment Gateway, VNPay sandbox |  |
| Triển khai | Docker Compose, GitHub Actions, Railway/Render/AWS/GCP |  |
| Kiểm thử | JUnit, Vitest, k6/Locust |  |

\[Nhận xét / diễn giải bảng\]

## **3.3. Bài toán đánh giá và giả thuyết nghiên cứu**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1,5 trang

### **3.3.1. Bài toán đánh giá và lựa chọn công nghệ**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1 trang   **\|   Nguồn:** Đề cương 1.5  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Đặt vấn đề build-vs-buy / technology evaluation; quy trình: giả thuyết → thực nghiệm có kiểm soát → quy tắc quyết định khóa trước → kết luận định lượng.  
\[Viết nội dung mục 3.3.1 tại đây\]

*\[Chèn hình tại đây – Hình 3.2\]*

*Hình 3.2: Quy trình đánh giá và lựa chọn routing proxy (Nguồn: nhóm thực hiện)*

### **3.3.2. Giả thuyết nghiên cứu**

**Phụ trách:** Khoa   **\|   Dự kiến:** 0,5 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Phát biểu giả thuyết kiểm chứng được cho RQ1, RQ2 (ví dụ: proxy định tuyến theo chi phí sẽ có chi phí trung bình thấp hơn nhưng tỷ lệ đúng trên prompt khó thấp hơn...).  
**Lưu ý:**  
– Đề cương nhắc tới "giả thuyết" nhưng chưa phát biểu cụ thể — cần bổ sung.  
\[Viết nội dung mục 3.3.2 tại đây\]

## **3.4. Thiết kế thí nghiệm**

**Phụ trách:** Khoa   **\|   Dự kiến:** 3 trang   **\|   Nguồn:** Đề cương 2.2, 2.3.2, Bảng 5

### **3.4.1. Pool mô hình ứng viên**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– 5 model chia ba tầng chi phí; giải thích vì sao phải có cả model rẻ lẫn model mạnh (tạo đánh đổi cost-quality thực sự). Ghi giá/1M token tại ngày chạy thực nghiệm.  
**Lưu ý:**  
– Đề cương lúc ghi "hai tầng", lúc ghi "ba tầng" (rẻ – trung – đắt) → thống nhất "ba tầng".  
– Ghi chính xác tên phiên bản model (model ID) đã gọi.  
\[Viết nội dung mục 3.4.1 tại đây\]

*Bảng 3.3: Pool mô hình dùng trong thực nghiệm (Nguồn: nhóm thực hiện)*

| Tầng | Model (model ID) | Giá input / output (USD/1M token) | Vai trò trong thí nghiệm |
| ----- | ----- | ----- | ----- |
| Rẻ | GPT-4o-mini |  | Chi phí thấp, chất lượng vừa đủ cho tác vụ đơn giản |
| Rẻ | Gemini Flash |  | Chi phí thấp, tốc độ cao |
| Trung | Claude Haiku |  | Mức trung gian, điểm tham chiếu |
| Đắt | GPT-4o |  | Model mạnh, chi phí cao – tạo áp lực đánh đổi |
| Đắt | Claude Sonnet |  | Model mạnh, chi phí cao – tạo áp lực đánh đổi |

\[Nhận xét / diễn giải bảng\]

### **3.4.2. Cấu hình các routing proxy**

**Phụ trách:** Hùng  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Với mỗi proxy: phiên bản, chiến lược routing được bật, tham số cấu hình (đưa file cấu hình đầy đủ vào Phụ lục). Lý giải vì sao cấu hình như vậy là công bằng giữa 3 proxy.  
\[Viết nội dung mục 3.4.2 tại đây\]

### **3.4.3. Bộ prompt kiểm thử**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– 30 prompt phân tầng 4 loại; tiêu chí soạn prompt; nguồn câu hỏi; ví dụ 1 prompt mỗi loại (toàn bộ để ở Phụ lục A).  
**Lưu ý:**  
– Đề cương ghi "4 loại" nhưng chỉ chia số lượng cho 3 nhóm (12 closed-QA gồm kiến thức/toán/logic, 6 code, 12 mở). Cần tách rõ số prompt toán/logic.  
– Chưa có cách chấm cho 6 prompt code — đề xuất: chạy test case tự động (pass/fail) và tính như closed-QA.  
\[Viết nội dung mục 3.4.3 tại đây\]

*Bảng 3.4: Phân bố bộ prompt kiểm thử (Nguồn: nhóm thực hiện)*

| Loại prompt | Số lượng | Cách chấm | Ví dụ |
| ----- | ----- | ----- | ----- |
| Closed-QA (kiến thức) |  | Đúng/sai khách quan |  |
| Toán / logic |  | Đúng/sai khách quan |  |
| Code | 6 | Đề xuất: chạy test case |  |
| Mở (email, tóm tắt, sáng tạo) | 12 | Rubric 3 tiêu chí (Bảng 3.6) |  |
| Tổng | 30 |  |  |

\[Nhận xét / diễn giải bảng\]

### **3.4.4. Số lần lặp và kiểm soát biến**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– 30 prompt × 3 proxy × 3 lần \= 270 lượt gọi API thật. Các biến được cố định: temperature, max\_tokens, thời điểm chạy, vùng mạng, thứ tự chạy (xáo trộn để tránh thiên lệch).  
\[Viết nội dung mục 3.4.4 tại đây\]

## **3.5. Chỉ số đo lường và quy trình chấm điểm**

**Phụ trách:** Khoa   **\|   Dự kiến:** 2,5 trang

### **3.5.1. Chỉ số đo lường**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Định nghĩa công thức từng chỉ số.  
\[Viết nội dung mục 3.5.1 tại đây\]

*Bảng 3.5: Định nghĩa các chỉ số đo lường (Nguồn: nhóm thực hiện)*

| Chỉ số | Định nghĩa / công thức | Đơn vị |
| ----- | ----- | ----- |
| Token tiêu tốn | token\_input \+ token\_output mỗi lượt gọi | token |
| Chi phí / prompt | Σ (token × đơn giá) theo bảng model\_pricing | USD |
| Tỷ lệ đúng | Số câu đúng / tổng số câu closed-QA | % |
| Điểm rubric | Tổng 3 tiêu chí, tối đa 3 điểm/prompt | điểm |
| Độ trễ | Mean và p95 thời gian phản hồi | ms |
| Consistency rate | Tỷ lệ prompt mà proxy chọn cùng một model qua cả 3 lần lặp | % |

\[Nhận xét / diễn giải bảng\]

### **3.5.2. Quy trình chấm điểm chất lượng**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1,5 trang   **\|   Nguồn:** Đề cương 2.1.1, Bảng 4  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Rubric 3 tiêu chí cho prompt mở; chấm mù (ẩn/mã hóa tên proxy); 30% prompt mở được cả hai thành viên chấm độc lập, báo cáo % agreement; xử lý bất đồng.  
– Thừa nhận giới hạn: đây là đánh giá chủ quan có kiểm soát.  
**Lưu ý:**  
– Có thể bổ sung hệ số Cohen's kappa bên cạnh % agreement để tăng độ tin cậy.  
\[Viết nội dung mục 3.5.2 tại đây\]

*Bảng 3.6: Rubric chấm điểm prompt mở (Nguồn: nhóm thực hiện)*

| Tiêu chí | 1 điểm | 0 điểm |
| ----- | ----- | ----- |
| Đúng yêu cầu (on-task) | Giải quyết trọn vẹn yêu cầu nêu trong prompt | Thiếu yêu cầu chính hoặc lạc đề |
| Độ dài phù hợp | Tương xứng với loại tác vụ, không thiếu ý chính, không dư thừa | Quá ngắn (thiếu thông tin) hoặc quá dài (lặp ý rõ rệt) |
| Không lỗi | Không lỗi định dạng, không lặp từ bất thường, không có nội dung lạc đề | Có ít nhất một lỗi kể trên |

\[Nhận xét / diễn giải bảng\]

## **3.6. Quy tắc quyết định lựa chọn proxy**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1 trang   **\|   Nguồn:** Đề cương 2.1.1  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Quy tắc lexicographic khóa trước: (1) loại proxy có tỷ lệ đúng closed-QA \< 80%; (2) chọn chi phí trung bình/prompt thấp nhất; (3) nếu chênh lệch chi phí \< 5% → ưu tiên p95 thấp hơn; (4) nếu vẫn hòa → consistency rate cao hơn.  
– Ghi rõ ngày khóa quy tắc; kết quả trình bày kèm biểu đồ Pareto cost-quality.  
\[Viết nội dung mục 3.6 tại đây\]

*\[Chèn hình tại đây – Hình 3.3\]*

*Hình 3.3: Lưu đồ quy tắc quyết định lựa chọn proxy (Nguồn: nhóm thực hiện)*

## **3.7. Phương pháp đánh giá hệ thống Gateway và môi trường thực nghiệm**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1,5 trang

### **3.7.1. Phương pháp đánh giá hệ thống Gateway**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– RQ3: đo overhead so với gọi trực tiếp, tách riêng OpenAI và Anthropic, có/không RAG; TTFT qua SSE (mean, p95).  
– RQ4: đối chiếu credit trừ với usage nhà cung cấp trên tập lượt chat thật.  
– RQ5: kịch bản gửi webhook trùng, sai chữ ký.  
– Load test bằng k6/Locust: tăng dần số request đồng thời đến khi p95 vượt ngưỡng.  
\[Viết nội dung mục 3.7.1 tại đây\]

### **3.7.2. Môi trường thực nghiệm**

**Phụ trách:** Hùng   **\|   Dự kiến:** 0,5 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Cấu hình máy/cloud, vùng mạng, phiên bản phần mềm, thời gian chạy thực nghiệm.  
\[Viết nội dung mục 3.7.2 tại đây\]

*Bảng 3.7: Môi trường thực nghiệm (Nguồn: nhóm thực hiện)*

| Thành phần | Cấu hình / phiên bản |
| ----- | ----- |
| Máy chủ chạy proxy |  |
| Hệ điều hành |  |
| LiteLLM | ≥ 1.83.0 |
| Bifrost |  |
| Portkey AI Gateway |  |
| Thời gian chạy |  |

\[Nhận xét / diễn giải bảng\]

## **3.8. Tiểu kết chương**

**Phụ trách:** Hùng   **\|   Dự kiến:** 0,5 trang  
– Tóm tắt 1 đoạn những gì chương đã trình bày và dẫn sang chương tiếp theo.  
\[Viết nội dung tiểu kết chương tại đây\]

# **Chương 4\. PHÂN TÍCH, THIẾT KẾ HỆ THỐNG**

**Phụ trách:** Hùng   **\|   Dự kiến:** 18–20 trang  
**Cần viết:**  
– Phần "hồ sơ thiết kế" mà Phụ lục 2 yêu cầu cho đề tài có sản phẩm phần mềm (theo mô hình UML...), thuộc phần TRÌNH BÀY, ĐÁNH GIÁ KẾT QUẢ của Phụ lục 2\.  
– Các hình trong đề cương (Hình 2–9) được tái sử dụng tại đây, đánh số lại theo chương.  
– Phân công xen kẽ: Khoa viết phân tích yêu cầu và use case (gắn với trải nghiệm người dùng); Hùng viết kiến trúc và thiết kế chi tiết backend; Khoa viết lại RAG Module và thiết kế giao diện.  
\[Đoạn dẫn nhập chương: 3–5 câu giới thiệu nội dung chương\]

## **4.1. Phân tích yêu cầu**

**Phụ trách:** Khoa   **\|   Dự kiến:** 2 trang

### **4.1.1. Các tác nhân của hệ thống**

**Phụ trách:** Khoa   **\|   Nguồn:** Đề cương 1.6, Bảng 2  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Admin, Creator, User. Thống nhất gọi "Creator" (đề cương có chỗ ghi "Vender").  
\[Viết nội dung mục 4.1.1 tại đây\]

*Bảng 4.1: Các tác nhân của hệ thống Conduit (Nguồn: nhóm thực hiện)*

| Tác nhân | Mô tả và cách sử dụng hệ thống |
| ----- | ----- |
| Admin | Quản lý API key thượng nguồn (mã hóa), cấu hình giá (markup 50%), quản lý gói bán, kiểm duyệt agent trước khi publish, theo dõi doanh thu và chi phí toàn hệ thống. |
| Creator | Khách thuê (tenant) kinh doanh dịch vụ: tạo agent qua giao diện no-code (tiêu đề, introduction, cơ sở tri thức, loại agent), đặt giá, gửi duyệt và publish; nhận doanh thu. Không cần API key. |
| User | Đăng ký, duyệt sàn, mua agent (đơn lẻ/combo), nhận credit tặng kèm một lần, sử dụng agent, nạp thêm credit khi hết. |

\[Nhận xét / diễn giải bảng\]

### **4.1.2. Yêu cầu chức năng**

**Phụ trách:** Khoa   **\|   Nguồn:** Đề cương 2.3.1, 3.3  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Liệt kê theo tác nhân, gắn mức ưu tiên MoSCoW và trạng thái hoàn thành thực tế.  
\[Viết nội dung mục 4.1.2 tại đây\]

*Bảng 4.2: Danh sách yêu cầu chức năng (Nguồn: nhóm thực hiện)*

| Mã | Yêu cầu chức năng | Tác nhân | Mức ưu tiên | Trạng thái |
| ----- | ----- | ----- | ----- | ----- |
| FR01 |  |  | Must |  |
| FR02 |  |  |  |  |
| … |  |  |  |  |

\[Nhận xét / diễn giải bảng\]

### **4.1.3. Yêu cầu phi chức năng**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Hiệu năng (overhead, TTFT), độ chính xác billing, bảo mật, khả năng mở rộng provider, khả năng chịu tải — gắn với ngưỡng ở Bảng 1.1.  
\[Viết nội dung mục 4.1.3 tại đây\]

## **4.2. Mô hình hóa chức năng**

**Phụ trách:** Khoa   **\|   Dự kiến:** 3 trang   **\|   Nguồn:** Đề cương 3.3, Hình 7–9

### **4.2.1. Sơ đồ use case tổng quát**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
\[Viết nội dung mục 4.2.1 tại đây\]

*\[Chèn hình tại đây – Hình 4.1\]*

*Hình 4.1: Sơ đồ use case tổng quát (Nguồn: nhóm thực hiện)*

### **4.2.2. Chức năng dành cho Admin**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Quản lý API thượng nguồn, cấu hình giá, quản lý khách hàng, duyệt agent, quản lý bán hàng, báo cáo chi phí – doanh thu, giám sát hệ thống.  
**Lưu ý:**  
– Đề cương ghi dashboard hiển thị "lợi nhuận biên 50%" — sai: markup 50% tương ứng lợi nhuận biên ≈ 33,3% (chính đề cương mục 2.2 đã giải thích). Sửa thống nhất.  
\[Viết nội dung mục 4.2.2 tại đây\]

*\[Chèn hình tại đây – Hình 4.2\]*

*Hình 4.2: Sơ đồ chức năng dành cho Admin (Nguồn: nhóm thực hiện)*

### **4.2.3. Chức năng dành cho Creator**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– 6 bước: tạo agent → quản lý cơ sở tri thức → test agent (không trừ credit) → đặt giá & gửi duyệt → quản lý agent đã publish → theo dõi doanh thu.  
\[Viết nội dung mục 4.2.3 tại đây\]

*\[Chèn hình tại đây – Hình 4.3\]*

*Hình 4.3: Sơ đồ chức năng dành cho Creator (Nguồn: nhóm thực hiện)*

### **4.2.4. Chức năng dành cho User**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Đăng ký/đăng nhập, duyệt sàn, tìm kiếm, mua agent, sử dụng agent, quản lý ví, nạp thêm, lịch sử, đánh giá.  
**Lưu ý:**  
– Đề cương mục 3.3.3 ghi VNPay sandbox là "cổng duy nhất" — mâu thuẫn với phạm vi (Mock Gateway là Must-have, VNPay là Should-have). Sửa thống nhất.  
\[Viết nội dung mục 4.2.4 tại đây\]

*\[Chèn hình tại đây – Hình 4.4\]*

*Hình 4.4: Sơ đồ chức năng dành cho User (Nguồn: nhóm thực hiện)*

### **4.2.5. Đặc tả các use case chính**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Đặc tả dạng bảng (tên, tác nhân, tiền điều kiện, luồng chính, luồng thay thế, hậu điều kiện) cho: Tạo & publish agent, Duyệt agent, Mua agent, Chat với agent, Nạp thêm credit.  
\[Viết nội dung mục 4.2.5 tại đây\]

*Bảng 4.3: Đặc tả use case "Mua agent" (Nguồn: nhóm thực hiện)*

| Mục | Nội dung |
| ----- | ----- |
| Tác nhân | User |
| Tiền điều kiện |  |
| Luồng chính |  |
| Luồng thay thế / ngoại lệ |  |
| Hậu điều kiện |  |

\[Nhận xét / diễn giải bảng\]

## **4.3. Kiến trúc tổng thể**

**Phụ trách:** Hùng   **\|   Dự kiến:** 2 trang   **\|   Nguồn:** Đề cương 2.1.2 (Hình 2), 3.1 (Hình 3\)  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Sáu module nghiệp vụ xoay quanh trục LLM Gateway.  
– Kiến trúc ba tầng \+ microservice: Frontend Portal, Backend Gateway, AI Service, PostgreSQL \+ pgvector, Object Storage, Redis, LLM Providers.  
– Luồng hoạt động chính (đăng nhập → mua agent → chat → trừ credit → nạp thêm) — nên thể hiện bằng sơ đồ tuần tự thay vì liệt kê.  
\[Viết nội dung mục 4.3 tại đây\]

*\[Chèn hình tại đây – Hình 4.5\]*

*Hình 4.5: Tổng quan các module nghiệp vụ (Nguồn: nhóm thực hiện)*

*\[Chèn hình tại đây – Hình 4.6\]*

*Hình 4.6: Sơ đồ kiến trúc tổng quan hệ thống (Nguồn: nhóm thực hiện)*

*\[Chèn hình tại đây – Hình 4.7\]*

*Hình 4.7: Sơ đồ tuần tự luồng chat với agent (Nguồn: nhóm thực hiện)*

## **4.4. Thiết kế chi tiết**

**Phụ trách:** Hùng (phần lớn), Khoa (5.7, 5.11)   **\|   Dự kiến:** 9–10 trang

### **4.4.1. Thiết kế LLM Gateway Module**

**Phụ trách:** Hùng   **\|   Dự kiến:** 2 trang   **\|   Nguồn:** Đề cương 3.2.1 (Hình 4\)  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Pipeline xử lý request: Reception → Authentication & Authorization → Credit Balance Check (402) → Agent Configuration Loading → RAG Retrieval → Provider Routing (qua proxy được chọn) → API Key Management → Streaming → Credit Calculation & Wallet Update → Logging → Fallback.  
– Sơ đồ lớp của Provider Adapter; chính sách fallback; xoay vòng API key khi bị rate limit.  
\[Viết nội dung mục 4.4.1 tại đây\]

*\[Chèn hình tại đây – Hình 4.8\]*

*Hình 4.8: Sơ đồ chi tiết Gateway Module (Nguồn: nhóm thực hiện)*

*\[Chèn hình tại đây – Hình 4.9\]*

*Hình 4.9: Sơ đồ lớp Provider Adapter (Nguồn: nhóm thực hiện)*

### **4.4.2. Thiết kế cơ chế hạch toán credit ba tầng**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1,5 trang   **\|   Nguồn:** Đề cương 2.2  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Ba tầng: usage thượng nguồn – credit nội bộ – bảng quy đổi (model\_pricing).  
– Công thức text: credit \= ceil(token\_upstream × 1,5); ảnh: bảng giá cố định theo độ phân giải.  
– Phân biệt markup 50% và lợi nhuận biên ≈ 33,3%; ảnh hưởng của lượt gọi lỗi khi fallback.  
– Xử lý đồng thời khi trừ ví (transaction, khóa) để tránh số dư âm.  
\[Viết nội dung mục 4.4.2 tại đây\]

*Bảng 4.4: Ví dụ quy đổi usage thượng nguồn sang credit (Nguồn: nhóm thực hiện)*

| Loại agent | Usage thượng nguồn | Quy tắc quy đổi | Credit bị trừ |
| ----- | ----- | ----- | ----- |
| Text |  | ceil(token × 1,5) |  |
| Image |  | Theo bảng giá độ phân giải |  |

\[Nhận xét / diễn giải bảng\]

### **4.4.3. Thiết kế module thanh toán**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1,5 trang   **\|   Nguồn:** Đề cương 2.2, 3.2.3b  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Payment Adapter: Mock Payment Gateway (Must) và VNPay sandbox (Should) dùng chung interface.  
– Webhook: xác thực chữ ký → kiểm tra idempotency theo transaction\_ref (unique) → cộng credit → ghi payment\_webhook\_logs.  
– Sơ đồ trạng thái agent\_purchases (pending/paid/failed/refunded).  
\[Viết nội dung mục 4.4.3 tại đây\]

*\[Chèn hình tại đây – Hình 4.10\]*

*Hình 4.10: Sơ đồ tuần tự xử lý webhook thanh toán idempotent (Nguồn: nhóm thực hiện)*

### **4.4.4. Thiết kế RAG Module**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1 trang   **\|   Nguồn:** Đề cương 3.2.2 (Hình 5\)  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Luồng ingestion (parse → chunk → embed → lưu pgvector) và luồng retrieval (embed query → similarity search top-k → re-rank tùy chọn → ghép context).  
– Cách ly dữ liệu đa khách thuê: lọc theo agent\_id trong kb\_chunks.  
\[Viết nội dung mục 4.4.4 tại đây\]

*\[Chèn hình tại đây – Hình 4.11\]*

*Hình 4.11: Sơ đồ pipeline RAG (Nguồn: nhóm thực hiện)*

### **4.4.5. Thiết kế cơ sở dữ liệu**

**Phụ trách:** Hùng   **\|   Dự kiến:** 2 trang   **\|   Nguồn:** Đề cương 3.2.4 (Hình 6\)  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– ERD phạm vi MVP, tổ chức theo 3 trục: người dùng – agent; tài chính; vận hành – đánh giá.  
– Bảng mô tả các bảng chính (đặc tả từng cột đưa vào Phụ lục).  
– Sơ đồ trạng thái của agent (draft → pending → approved/rejected → published/unpublished).  
\[Viết nội dung mục 4.4.5 tại đây\]

*\[Chèn hình tại đây – Hình 4.12\]*

*Hình 4.12: Sơ đồ ERD cơ sở dữ liệu – phạm vi MVP (Nguồn: nhóm thực hiện)*

*Bảng 4.5: Mô tả các bảng dữ liệu chính (Nguồn: nhóm thực hiện)*

| Nhóm | Bảng | Mô tả |
| ----- | ----- | ----- |
| Người dùng & xác thực | users |  |
| Agent & kho tri thức | agents, knowledge\_bases, kb\_chunks |  |
| Ví credit & giao dịch | credit\_wallets, credit\_transactions |  |
| Mua agent & thanh toán | agent\_purchases, payment\_webhook\_logs |  |
| Chat / hội thoại | conversations, messages |  |
| API key & nhà cung cấp | api\_keys |  |
| Logging & giám sát | usage\_logs |  |
| Đánh giá routing proxy | model\_pricing, routing\_decisions |  |

\[Nhận xét / diễn giải bảng\]

### **4.4.6. Thiết kế bảo mật**

**Phụ trách:** Hùng   **\|   Dự kiến:** 2 trang   **\|   Nguồn:** Đề cương 3.2.3, Bảng 6  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Mô hình mối đe dọa (Bảng 4.6), sau đó biện pháp cho từng rủi ro: (a) bảo vệ API key thượng nguồn; (b) chống giả mạo webhook; (c) kiểm soát truy cập ABAC theo quyền sở hữu và trạng thái ví (403/402); (d) phòng ngừa prompt injection trong kho tri thức; (e) chống SQL injection; (f) bảo mật JWT.  
\[Viết nội dung mục 4.4.6 tại đây\]

*Bảng 4.6: Mô hình mối đe dọa của hệ thống (Nguồn: nhóm thực hiện)*

| Nhóm rủi ro | Kẻ tấn công điển hình | Hậu quả | Biện pháp |
| ----- | ----- | ----- | ----- |
| Lộ API key thượng nguồn | Người có quyền truy cập DB/log/code bị rò rỉ | Bị dùng chùa, tốn chi phí | AES-GCM, tách khóa mã hóa, không log key |
| Giả mạo webhook thanh toán | Người ngoài gửi request giả tới endpoint công khai | Cộng credit không cần trả tiền | Xác thực chữ ký, idempotency, audit log |
| Truy cập tài nguyên không sở hữu | User/Creator cố tình vượt quyền | Dùng agent chưa mua, sửa dữ liệu người khác | ABAC theo sở hữu và trạng thái ví |
| Prompt injection | Creator hoặc nội dung file trong kho tri thức | Agent bị chiếm quyền điều khiển | Tách vai trò trong prompt, bộ test case |
| SQL injection | Người dùng nhập input độc hại | Vượt xác thực, truy cập trái phép | Prepared statement, @Param |
| Giả mạo/đánh cắp JWT | Đánh cắp token, khai thác secret yếu | Mạo danh người dùng, kể cả Admin | Secret mạnh, hạn ngắn \+ refresh, HttpOnly cookie, kiểm tra thuật toán |

\[Nhận xét / diễn giải bảng\]

### **4.4.7. Thiết kế API**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Nhóm endpoint chính (auth, agents, purchases, chat, wallet, admin, webhook); quy ước mã lỗi (401, 402, 403, 429...). Đặc tả OpenAPI đầy đủ đưa vào Phụ lục E.  
\[Viết nội dung mục 4.4.7 tại đây\]

### **4.4.8. Thiết kế giao diện**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Sơ đồ trang (sitemap) và wireframe các màn hình chính. Ảnh chụp giao diện thực tế để ở Chương 5\.  
\[Viết nội dung mục 4.4.8 tại đây\]

*\[Chèn hình tại đây – Hình 4.13\]*

*Hình 4.13: Sơ đồ trang của Frontend Portal (Nguồn: nhóm thực hiện)*

## **4.5. Tiểu kết chương**

**Phụ trách:** Hùng   **\|   Dự kiến:** 0,5 trang  
– Tóm tắt 1 đoạn những gì chương đã trình bày và dẫn sang chương tiếp theo.  
\[Viết nội dung tiểu kết chương tại đây\]

# **Chương 5\. HIỆN THỰC VÀ THỬ NGHIỆM ĐÁNH GIÁ**

**Phụ trách:** Hùng   **\|   Dự kiến:** 16–18 trang  
**Cần viết:**  
– Phần hiện thực và phần TRÌNH BÀY, ĐÁNH GIÁ BÀN LUẬN VỀ KẾT QUẢ của Phụ lục 2\.  
– Trình bày kết quả theo thứ tự RQ1 → RQ5: số liệu → biểu đồ → nhận xét → trả lời câu hỏi nghiên cứu. Số liệu thô đầy đủ đưa vào Phụ lục C.  
– Phân công xen kẽ: Hùng viết hiện thực backend/hạ tầng/triển khai và kết quả liên quan hệ thống (độ trễ, billing, webhook, tải); Khoa viết hiện thực frontend/mở rộng, kết quả chất lượng response, phân bố model, kiểm thử chức năng.  
\[Đoạn dẫn nhập chương: 3–5 câu giới thiệu nội dung chương\]

## **5.1. Hiện thực hệ thống**

**Phụ trách:** Hùng (6.1–6.3, 6.5, 6.7), Khoa (6.4, 6.6, 6.8)   **\|   Dự kiến:** 8–10 trang  
**Cần viết:**  
– Tập trung vào các điểm hiện thực có thách thức kỹ thuật (đoạn mã ngắn minh họa). Không dán mã nguồn dài. Ghi rõ mức độ hoàn thành thực tế của từng hạng mục Must/Should/Could.

### **5.1.1. Môi trường phát triển và tổ chức mã nguồn**

**Phụ trách:** Hùng   **\|   Dự kiến:** 0,5 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Cấu trúc repository (monorepo/multi-repo), quy trình làm việc nhóm (branching, review).  
\[Viết nội dung mục 5.1.1 tại đây\]

### **5.1.2. Hiện thực Backend Gateway**

**Phụ trách:** Hùng   **\|   Dự kiến:** 2,5 trang

#### ***5.1.2.1. Xác thực và phân quyền***

**Phụ trách:** Hùng  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– JWT \+ refresh token, OAuth Google, kiểm tra ABAC.  
\[Viết nội dung mục 5.1.2.1 tại đây\]

#### ***5.1.2.2. Provider Adapter và tích hợp routing proxy***

**Phụ trách:** Hùng  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Chuẩn hóa interface giữa các provider; cách Gateway gọi proxy được chọn chính thức.  
\[Viết nội dung mục 5.1.2.2 tại đây\]

#### ***5.1.2.3. Streaming phản hồi qua SSE***

**Phụ trách:** Hùng  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Spring WebFlux; xử lý ngắt kết nối; tính credit khi stream kết thúc.  
\[Viết nội dung mục 5.1.2.3 tại đây\]

#### ***5.1.2.4. Ví credit và ghi nhận usage***

**Phụ trách:** Hùng  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Transaction trừ ví, ghi credit\_transactions và usage\_logs; xử lý đồng thời.  
\[Viết nội dung mục 5.1.2.4 tại đây\]

### **5.1.3. Hiện thực hạ tầng thực nghiệm ba routing proxy**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang   **\|   Nguồn:** Kế hoạch tuần 7–8  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Triển khai LiteLLM, Bifrost, Portkey; cấu hình cùng pool 5 model; script chạy thực nghiệm (harness) và ghi log vào routing\_decisions.  
\[Viết nội dung mục 5.1.3 tại đây\]

### **5.1.4. Hiện thực Frontend Portal**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1,5 trang   **\|   Nguồn:** Kế hoạch tuần 3–6  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Sàn agent, trang chi tiết agent, giao diện chat streaming, Creator studio, ví credit, trang quản trị.  
\[Viết nội dung mục 5.1.4 tại đây\]

### **5.1.5. Hiện thực module thanh toán**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang   **\|   Nguồn:** Kế hoạch tuần 11  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Mock Payment Gateway, webhook idempotent, (VNPay sandbox nếu hoàn thành).  
\[Viết nội dung mục 5.1.5 tại đây\]

### **5.1.6. Hiện thực các chức năng mở rộng**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1 trang   **\|   Nguồn:** Kế hoạch tuần 13  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– RAG cơ bản (AI Service – FastAPI), sinh ảnh DALL·E 3, widget iframe, fallback sang Gemini. Chỉ trình bày hạng mục thực sự hoàn thành; hạng mục chưa làm chuyển sang Hướng phát triển.  
\[Viết nội dung mục 5.1.6 tại đây\]

### **5.1.7. Triển khai hệ thống**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Docker Compose, CI/CD GitHub Actions, môi trường triển khai cloud/PaaS.  
\[Viết nội dung mục 5.1.7 tại đây\]

*\[Chèn hình tại đây – Hình 5.1\]*

*Hình 5.1: Sơ đồ triển khai hệ thống (deployment diagram) (Nguồn: nhóm thực hiện)*

### **5.1.8. Giao diện hệ thống**

**Phụ trách:** Khoa   **\|   Dự kiến:** 2 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Ảnh chụp các màn hình chính kèm mô tả ngắn. Mỗi ảnh một caption.  
\[Viết nội dung mục 5.1.8 tại đây\]

*\[Chèn hình tại đây – Hình 5.2\]*

*Hình 5.2: Giao diện trang chủ sàn agent (Nguồn: nhóm thực hiện)*

*\[Chèn hình tại đây – Hình 5.3\]*

*Hình 5.3: Giao diện chat với agent (Nguồn: nhóm thực hiện)*

*\[Chèn hình tại đây – Hình 5.4\]*

*Hình 5.4: Giao diện tạo agent của Creator (Nguồn: nhóm thực hiện)*

*\[Chèn hình tại đây – Hình 5.5\]*

*Hình 5.5: Giao diện trang quản trị (Nguồn: nhóm thực hiện)*

## **5.2. Kết quả đánh giá ba routing proxy**

**Phụ trách:** Khoa   **\|   Dự kiến:** 6 trang

### **5.2.1. Token tiêu tốn và chi phí (RQ1)**

**Phụ trách:** Hùng  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
\[Viết nội dung mục 5.2.1 tại đây\]

*Bảng 5.1: Tổng hợp kết quả ba routing proxy (Nguồn: nhóm thực hiện)*

| Proxy | Token TB/prompt | Chi phí TB/prompt (USD) | Tỷ lệ đúng closed-QA | Điểm rubric TB | Độ trễ p95 (ms) | Consistency rate |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| LiteLLM |  |  |  |  |  |  |
| Bifrost |  |  |  |  |  |  |
| Portkey |  |  |  |  |  |  |

\[Nhận xét / diễn giải bảng\]

*\[Chèn hình tại đây – Hình 5.6\]*

*Hình 5.6: Chi phí trung bình mỗi prompt theo proxy và loại prompt (Nguồn: nhóm thực hiện)*

### **5.2.2. Chất lượng phản hồi (RQ1)**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Tỷ lệ đúng closed-QA, điểm rubric prompt mở, kết quả prompt code; % agreement giữa hai người chấm.  
\[Viết nội dung mục 5.2.2 tại đây\]

### **5.2.3. Phân bố lựa chọn mô hình theo cơ chế định tuyến (RQ2)**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Mỗi proxy chọn model nào cho từng loại prompt; giải thích bằng chiến lược routing (liên hệ mục 3.1.3).  
\[Viết nội dung mục 5.2.3 tại đây\]

*\[Chèn hình tại đây – Hình 5.7\]*

*Hình 5.7: Phân bố model được chọn theo proxy và loại prompt (Nguồn: nhóm thực hiện)*

### **5.2.4. Độ trễ và độ ổn định**

**Phụ trách:** Hùng  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Mean, độ lệch chuẩn, p95; consistency rate qua 3 lần lặp.  
\[Viết nội dung mục 5.2.4 tại đây\]

### **5.2.5. Áp dụng quy tắc quyết định và lựa chọn proxy**

**Phụ trách:** Khoa  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Áp dụng từng bước của quy tắc khóa trước (mục 3.6); biểu đồ Pareto cost-quality; kết luận proxy được tích hợp chính thức.  
\[Viết nội dung mục 5.2.5 tại đây\]

*\[Chèn hình tại đây – Hình 5.8\]*

*Hình 5.8: Biểu đồ Pareto chi phí – chất lượng của ba proxy (Nguồn: nhóm thực hiện)*

## **5.3. Đánh giá hệ thống Gateway**

**Phụ trách:** Hùng   **\|   Dự kiến:** 4 trang

### **5.3.1. Độ trễ của Gateway (RQ3)**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Overhead so với gọi trực tiếp (OpenAI, Anthropic), có/không RAG; TTFT mean và p95.  
\[Viết nội dung mục 5.3.1 tại đây\]

*Bảng 5.2: Độ trễ bổ sung của Gateway (Nguồn: nhóm thực hiện)*

| Provider | Gọi trực tiếp (ms) | Qua Gateway (ms) | Overhead (ms) | TTFT mean / p95 (ms) |
| ----- | ----- | ----- | ----- | ----- |
| OpenAI |  |  |  |  |
| Anthropic |  |  |  |  |
| Có RAG |  |  |  |  |

\[Nhận xét / diễn giải bảng\]

### **5.3.2. Độ chính xác tính credit (RQ4)**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Số lượt chat kiểm tra, sai số trung bình và lớn nhất so với usage nhà cung cấp báo về; so với ngưỡng \< 1%.  
\[Viết nội dung mục 5.3.2 tại đây\]

### **5.3.3. Xử lý webhook thanh toán (RQ5)**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Kịch bản: callback hợp lệ, callback trùng, sai chữ ký; kết quả theo payment\_webhook\_logs.  
\[Viết nội dung mục 5.3.3 tại đây\]

### **5.3.4. Khả năng chịu tải**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Kết quả k6/Locust: số request đồng thời tối đa trước khi p95 vượt ngưỡng; biểu đồ throughput – latency.  
\[Viết nội dung mục 5.3.4 tại đây\]

*\[Chèn hình tại đây – Hình 5.9\]*

*Hình 5.9: Kết quả kiểm thử tải (Nguồn: nhóm thực hiện)*

## **5.4. Kiểm thử hệ thống**

**Phụ trách:** Khoa   **\|   Dự kiến:** 2 trang

### **5.4.1. Kiểm thử chức năng và bảo mật**

**Phụ trách:** Khoa   **\|   Dự kiến:** 1,5 trang   **\|   Nguồn:** Đề cương 3.4  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Unit test (JUnit, Vitest), integration test; security acceptance test (cách ly tenant, prompt injection, JWT).  
– Bảng kết quả các kịch bản demo/kiểm thử chính (đề cương 3.4 có 10 kịch bản).  
**Lưu ý:**  
– Kịch bản Admin trong đề cương ghi "xác nhận lợi nhuận biên 50%" — sửa thành xác nhận tỷ lệ thu/chi \= 1,5 (lợi nhuận biên ≈ 33,3%).  
\[Viết nội dung mục 5.4.1 tại đây\]

*Bảng 5.3: Kết quả các kịch bản kiểm thử chính (Nguồn: nhóm thực hiện)*

| STT | Kịch bản | Kết quả mong đợi | Kết quả thực tế | Đạt |
| ----- | ----- | ----- | ----- | ----- |
| 1 | Admin cấu hình API key, đặt markup 50% | Key lưu ở dạng mã hóa |  |  |
| 2 | Creator tạo text agent, publish; Admin duyệt |  |  |  |
| 3 | User mua agent qua Mock Gateway | Ví được cộng đúng credit |  |  |
| 4 | Chat với agent, kiểm tra trừ credit | Trừ đúng ceil(token × 1,5) |  |  |
| 5 | Hết credit → chặn, nạp thêm |  |  |  |
| … |  |  |  |  |

\[Nhận xét / diễn giải bảng\]

### **5.4.2. Đánh giá chất lượng truy hồi RAG**

**Phụ trách:** Khoa   **\|   Dự kiến:** 0,5 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Chỉ viết nếu triển khai RAG: Recall@5 trên tập câu hỏi tự soạn. Nếu không triển khai thì xóa mục này.  
\[Viết nội dung mục 5.4.2 tại đây\]

## **5.5. Thảo luận**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1,5 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Đối chiếu kết quả với mục tiêu và ngưỡng ở Bảng 1.1.  
– Các yếu tố ảnh hưởng tính hợp lệ (threats to validity): quy mô 30 prompt, chấm chủ quan, giá model thay đổi, tính không xác định của LLM, benchmark do hãng công bố.  
\[Viết nội dung mục 5.5 tại đây\]

## **5.6. Tiểu kết chương**

**Phụ trách:** Hùng   **\|   Dự kiến:** 0,5 trang  
– Tóm tắt 1 đoạn những gì chương đã trình bày và dẫn sang chương tiếp theo.  
\[Viết nội dung tiểu kết chương tại đây\]

# **Chương 6\. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN**

**Phụ trách:** Hùng   **\|   Dự kiến:** 3 trang  
**Cần viết:**  
– Tương ứng hai phần KẾT LUẬN và HƯỚNG PHÁT TRIỂN của Phụ lục 2\. Kết luận cần ngắn gọn, không có lời bàn và bình luận thêm; hướng phát triển là kiến nghị hướng nghiên cứu tiếp theo.  
– Chương ngắn, do Hùng tổng hợp từ kết quả của cả hai; Khoa rà soát lại phần liên quan đến nghiên cứu/thực nghiệm trước khi gộp.  
\[Đoạn dẫn nhập chương: 3–5 câu giới thiệu nội dung chương\]

## **6.1. Kết quả đạt được**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Tóm tắt kết quả theo từng mục tiêu; có thể dùng bảng đối chiếu mục tiêu – kết quả.  
\[Viết nội dung mục 6.1 tại đây\]

*Bảng 6.1: Đối chiếu mục tiêu và kết quả đạt được (Nguồn: nhóm thực hiện)*

| Mục tiêu | Kết quả đạt được | Mức độ |
| ----- | ----- | ----- |
|  |  |  |
|  |  |  |

\[Nhận xét / diễn giải bảng\]

## **6.2. Đóng góp của khóa luận**

**Phụ trách:** Hùng   **\|   Dự kiến:** 0,5 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
\[Viết nội dung mục 6.2 tại đây\]

## **6.3. Hạn chế**

**Phụ trách:** Hùng   **\|   Dự kiến:** 0,5 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
\[Viết nội dung mục 6.3 tại đây\]

## **6.4. Hướng phát triển**

**Phụ trách:** Hùng   **\|   Dự kiến:** 1 trang  
**Trạng thái:** ☐ Chưa viết   ☐ Đang viết   ☐ Chờ review   ☐ Hoàn thành  
**Cần viết:**  
– Sinh video; BYOK đầy đủ cho doanh nghiệp; tích hợp MoMo/ZaloPay; re-ranking bằng cross-encoder; mở rộng bộ prompt và routing học máy; các hạng mục Should-have chưa hoàn thành.  
\[Viết nội dung mục 6.4 tại đây\]

# **TÀI LIỆU THAM KHẢO**

**Phụ trách:** Hùng & Khoa (một người giữ danh mục chính, người kia gửi tài liệu mới để bổ sung)  
– Đã chuyển 25 tài liệu từ đề cương, sắp theo alphabet tên tác giả/tổ chức và đánh số lại \[1\]–\[25\]. Dùng số mới này khi trích dẫn trong bài.  
– Đã sửa: tác giả đầu bài RAG là "P. Lewis" (đề cương ghi "K. Lewis"); tác giả đầu bài microservice dữ liệu phân tán là "W. Hasselbring" (đề cương ghi "S. Hasselbring"). Nhóm kiểm tra lại toàn bộ thông tin (tên bài, trang) của tài liệu \[22\].  
– Tài liệu web: bổ sung ngày truy cập theo IEEE, ví dụ "Accessed: Nov. 6, 2026".  
– Chỉ giữ tài liệu thực sự được trích dẫn trong bài; tài liệu MoMo \[14\] chỉ giữ nếu có nhắc tới ở mục giới hạn.  
– Nếu có tài liệu tiếng Việt, đặt vào mục "Tài liệu tiếng Việt" và đánh số trước phần tiếng Anh.  
**Tài liệu tiếng Việt**

\[Bổ sung nếu có\]

**Tài liệu tiếng Anh**

\[1\]Anthropic, "Building effective agents," Anthropic Engineering Blog, 2024\. \[Online\]. Available: https\://www\.anthropic.com/research/building-effective-agents

\[2\]Anthropic, "Claude API Documentation," 2024\. \[Online\]. Available: https\://docs.anthropic.com

\[3\]D. Avila, "LibreChat – Enhanced ChatGPT clone," GitHub Repository, 2024\. \[Online\]. Available: https\://github.com/danny-avila/LibreChat

\[4\]BerriAI, "LiteLLM – Unified interface for 100+ LLMs," GitHub Repository, 2024\. \[Online\]. Available: https\://github.com/BerriAI/litellm

\[5\]S. Es, J. James, L. Espinosa-Anke, and S. Schockaert, "RAGAS: Automated Evaluation of Retrieval Augmented Generation," arXiv preprint arXiv:2309.15217, 2023\.

\[6\]Google, "Gemini API Documentation," 2024\. \[Online\]. Available: https\://ai.google.dev/gemini-api/docs

\[7\]Google, "Google AI Studio – Build with Gemini," 2024\. \[Online\]. Available: https\://aistudio.google.com

\[8\]W. Hasselbring and G. Steinacker, "Microservice Architectures for Decentralized Data Management," IEEE Software, vol. 34, no. 2, pp. 43–49, 2017\.

\[9\]V. Karpukhin, B. Oguz, S. Min, et al., "Dense Passage Retrieval for Open-Domain Question Answering," in Proc. 2020 Conf. Empirical Methods in Natural Language Processing (EMNLP), 2020, pp. 6769–6781.

\[10\]LangGenius, "Dify – An open-source LLM app development platform," GitHub Repository, 2024\. \[Online\]. Available: https\://github.com/langgenius/dify

\[11\]P. Lewis, E. Perez, A. Piktus, et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in Advances in Neural Information Processing Systems, vol. 33, 2020, pp. 9459–9474.

\[12\]Maxim AI, "Bifrost – Fastest LLM gateway," GitHub Repository, 2025\. \[Online\]. Available: https\://github.com/maximhq/bifrost

\[13\]F. Montesi and J. Weber, "Circuit Breakers, Discovery, and API Gateways in Microservices," arXiv preprint arXiv:1609.05830, 2016\.

\[14\]MoMo Business, "MoMo Payment Gateway API Documentation," 2024\. \[Online\]. Available: https\://developers.momo.vn

\[15\]OpenAI, "GPT Store – Discover and create custom versions of ChatGPT," 2024\. \[Online\]. Available: https\://chatgpt.com/gpts

\[16\]OpenAI, "OpenAI API Reference," 2024\. \[Online\]. Available: https\://platform.openai.com/docs/api-reference

\[17\]OpenRouter, "A unified interface for LLMs," 2024\. \[Online\]. Available: https\://openrouter.ai

\[18\]pgvector contributors, "pgvector – Open-source vector similarity search for Postgres," 2024\. \[Online\]. Available: https\://github.com/pgvector/pgvector

\[19\]Poe by Quora, "Build, share, and monetize AI agents," 2024\. \[Online\]. Available: https\://poe.com

\[20\]Portkey AI, "Portkey AI Gateway – A blazing fast AI Gateway with integrated guardrails," GitHub Repository, 2024\. \[Online\]. Available: https\://github.com/Portkey-AI/gateway

\[21\]C. Richardson, Microservices Patterns: With Examples in Java. Manning Publications, 2018\.

\[22\]W. Tsai, X. Sun, and J. Balasooriya, "SaaS Multi-Tenant Data Access Control," in 2011 IEEE Int. Conf. e-Business Engineering, 2011, pp. 88–93.

\[23\]VMware, "Spring AI – AI application framework for the Spring ecosystem," 2024\. \[Online\]. Available: https\://spring.io/projects/spring-ai

\[24\]VNPay, "VNPay Payment Gateway Integration Guide," 2024\. \[Online\]. Available: https\://sandbox.vnpayment.vn/apis

\[25\]L. Wang, N. Yang, X. Huang, et al., "Multilingual E5 Text Embeddings: A Technical Report," arXiv preprint arXiv:2402.05672, 2024\.

# **PHỤ LỤC**

– Phụ lục không tính vào số trang nội dung. Đánh số hình/bảng trong phụ lục theo chữ cái (Bảng A.1, Hình D.1).

## **Phụ lục A. Bộ 30 prompt kiểm thử và đáp án**

**Phụ trách:** Khoa  
– Toàn bộ prompt theo loại, đáp án đúng (closed-QA), test case (code).  
\[Viết nội dung Phụ lục A tại đây\]

## **Phụ lục B. Bảng chấm điểm rubric**

**Phụ trách:** Khoa  
– Bảng chấm mù (mã hóa proxy), kết quả chấm của từng người, % agreement.  
\[Viết nội dung Phụ lục B tại đây\]

## **Phụ lục C. Số liệu thực nghiệm chi tiết**

**Phụ trách:** Hùng  
– Kết quả 270 lượt gọi: model được chọn, token, chi phí, độ trễ, điểm chất lượng.  
\[Viết nội dung Phụ lục C tại đây\]

## **Phụ lục D. Cấu hình các routing proxy**

**Phụ trách:** Hùng  
– File cấu hình LiteLLM, Bifrost, Portkey dùng trong thực nghiệm.  
\[Viết nội dung Phụ lục D tại đây\]

## **Phụ lục E. Đặc tả API và cơ sở dữ liệu**

**Phụ trách:** Hùng  
– Đặc tả OpenAPI các endpoint chính; đặc tả cột của từng bảng.  
\[Viết nội dung Phụ lục E tại đây\]

## **Phụ lục F. Hướng dẫn cài đặt và cấu trúc đĩa nộp**

**Phụ trách:** Hùng  
– Theo Phụ lục 2: thư mục \<TÊN PHẦN MỀM\> (SETUP, SOURCE), BAO CAO (DOC, PDF, ABS), SOFT; tập tin hướng dẫn ở thư mục gốc kèm thông tin liên lạc.  
\[Viết nội dung Phụ lục F tại đây\]