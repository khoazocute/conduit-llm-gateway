# Chọn routing proxy nào cho Conduit?

**Báo cáo tiến độ khóa luận · 22/10/2026**
Nguyễn Văn Lê Hùng (23520570) · Võ Đăng Khoa (23520758) · GVHD: TS. Nguyễn Thanh Bình, ThS. Trần Vĩnh Khiêm

---

## Kết luận: chọn LiteLLM, kèm một điều kiện bắt buộc

- **Đạt yêu cầu chất lượng:** trả lời đúng 83,8% số câu, qua mức tối thiểu 80% đã đặt trước.
- **Rẻ nhất:** rẻ hơn Bifrost 4,6 lần và rẻ hơn Portkey 6,4 lần cho mỗi câu hỏi.
- **Điều kiện:** phải bật cơ chế dự phòng (fallback) khi tích hợp. Phép thử giả lập sự cố cho thấy LiteLLM chưa tự chuyển sang nhà cung cấp khác khi một nhà cung cấp lỗi.

## Bài toán

Conduit gọi các mô hình AI (GPT, Claude, Gemini) thông qua một lớp trung gian gọi là **proxy**. Proxy quyết định mỗi câu hỏi của người dùng được gửi tới mô hình nào. Gửi sang mô hình đắt thì thường đúng hơn nhưng tốn tiền, gửi sang mô hình rẻ thì ngược lại.

```
Ứng dụng Conduit  →  Proxy  →  Mô hình AI
(người dùng chat)    (chọn mô    Rẻ:        GPT-4o-mini
                     hình cho    Trung bình: Claude Haiku
                     từng câu)   Đắt:       GPT-4o
```

**Câu hỏi nghiên cứu:** trong 3 proxy mã nguồn mở, proxy nào cho câu trả lời đạt yêu cầu với chi phí thấp nhất? Đây là đóng góp khoa học duy nhất của khóa luận; phần còn lại của hệ thống (chợ agent, ví credit, thanh toán) là môi trường thật để chạy thí nghiệm này.

## Cách đánh giá

Mỗi proxy được cấu hình theo cách chọn mô hình mạnh nhất mà bản mã nguồn mở của nó cho phép:

| Proxy | Chọn mô hình dựa vào |
|---|---|
| **LiteLLM** | Giá: tự chọn mô hình rẻ nhất trong nhóm. |
| **Bifrost** | Độ khó của câu hỏi: tự phân loại dễ / vừa / khó rồi gửi tới mô hình tương ứng. |
| **Portkey** | Độ dài câu hỏi, theo ngưỡng do nhóm tự đặt: ngắn gửi mô hình rẻ, dài gửi mô hình đắt. |

**Bộ đề:** 4 bộ đề chuẩn, công khai, dùng trong các bài báo khoa học, mỗi bộ 20 câu, chấm tự động theo đúng cách của bài báo gốc.

- **MMLU:** kiến thức tổng hợp, trắc nghiệm.
- **GSM8K:** toán đố cấp tiểu học.
- **HumanEval:** viết hàm lập trình, chạy thử bằng test thật.
- **IFEval:** làm đúng yêu cầu định dạng (độ dài, từ khóa, cấu trúc).

Mỗi proxy trả lời cả 80 câu, mỗi câu 3 lần: **80 × 3 × 3 proxy = 720 lượt gọi thật** tới nhà cung cấp, tổng chi phí khoảng 0,36 USD cho toàn bộ thí nghiệm (kể cả phép thử sự cố ở dưới).

## Tiêu chí chọn (đã khóa trước khi chạy)

Luật chọn được viết và khóa trước khi có kết quả, để không chọn tiêu chí theo hướng có lợi sau khi đã thấy số.

1. Loại proxy trả lời đúng dưới 80%.
2. Trong số còn lại, chọn proxy có chi phí trung bình mỗi câu hỏi thấp nhất.
3. Nếu chi phí chênh nhau dưới 5%, chọn proxy có thời gian chờ thấp hơn.
4. Nếu vẫn hòa, chọn proxy ổn định hơn (cùng câu hỏi hỏi 3 lần vẫn chọn cùng một mô hình).

## Kết quả

In đậm là proxy tốt nhất ở tiêu chí đó. Số liệu từ 720 lượt gọi thật, riêng dòng cuối từ phép thử sự cố 45 lượt.

| Tiêu chí | LiteLLM | Bifrost | Portkey |
|---|---:|---:|---:|
| Độ chính xác (tỷ lệ trả lời đúng, tối thiểu 80%) | 83,8% | 87,5% | **92,1%** |
| Chi phí mỗi câu hỏi (trung bình, USD) | **$0,00012** | $0,00056 | $0,00079 |
| Chi phí cho 1.000 câu trả lời đúng (gộp cả độ đúng và giá) | **$0,15** | $0,64 | $0,86 |
| Thời gian chờ (95% số câu nhanh hơn mức này) | **6,3 giây** | 7,2 giây | 6,9 giây |
| Độ ổn định (hỏi lại 3 lần vẫn chọn cùng mô hình) | **100%** | 97,5% | **100%** |
| Tỷ lệ lỗi | **0%** | 0,8% | **0%** |
| Phục hồi khi nhà cung cấp lỗi (phép thử riêng, 15 lượt mỗi proxy) | 0 / 15 | **13 / 15** | 0 / 15 |

Biểu đồ cột (xem bản trang web để thấy dạng hình): độ chính xác 83,8% / 87,5% / 92,1% so với mức 80%; chi phí cho 1.000 câu đúng $0,15 / $0,64 / $0,86, tức LiteLLM chỉ bằng khoảng 1/6 của Portkey.

### Áp dụng luật chọn

| Bước | Kết quả |
|---|---|
| 1. Loại dưới 80% | Cả ba đều từ 80% trở lên, không loại ai. |
| 2. Chi phí thấp nhất | **LiteLLM** ($0,00012 so với $0,00056 và $0,00079 mỗi câu hỏi) → **chọn LiteLLM**. |
| 3. Chênh dưới 5% thì xét thời gian chờ | Không cần: chi phí chênh hơn 355%, vượt xa ngưỡng 5%. |
| 4. Còn hòa thì xét độ ổn định | Không cần: không còn hòa. |

Kết luận giữ nguyên khi thử bỏ lần lượt từng bộ đề trong 4 bộ (cả 4 lần thử đều ra LiteLLM). Kết luận cũng không đổi khi thêm dữ liệu: ở mốc 360, 540 và 720 lượt, thứ tự ba proxy và proxy được chọn đều như nhau.

## Mỗi proxy mạnh và yếu ở đâu

**LiteLLM (được chọn)**
- (+) Rẻ nhất, ổn định tuyệt đối.
- (−) Chọn đúng một mô hình rẻ cho cả 240 lượt, không bao giờ nâng lên mô hình mạnh hơn cho câu khó.
- (−) Khi nhà cung cấp lỗi, nó chờ 40 giây rồi báo lỗi, không tự chuyển sang nhà khác.

**Bifrost**
- (+) Bền nhất khi có sự cố: tự chuyển sang Claude hoặc Gemini trong khoảng 6 giây.
- (−) Phân loại độ khó chưa chuẩn: gửi 85% câu trắc nghiệm dễ sang mô hình đắt nhất mà điểm tăng không đáng kể.
- (−) Đắt hơn LiteLLM 4,6 lần.

**Portkey**
- (+) Chính xác nhất (92,1%).
- (−) Đắt nhất, đắt hơn LiteLLM 6,4 lần.
- (−) Hiệu quả phụ thuộc ngưỡng độ dài do nhóm tự đặt, chưa chắc còn đúng với dữ liệu người dùng thật.

## Giới hạn cần nói rõ

- **Cỡ mẫu còn nhỏ.** Với 80 câu, về mặt thống kê chưa khẳng định chắc được LiteLLM thật sự trên 80%, vì khoảng tin cậy 95% của nó là 75,7% đến 91,8%. Muốn chắc cần hàng nghìn câu, ngoài khả năng của khóa luận. Điều vẫn chắc: LiteLLM rẻ nhất trên mỗi câu trả lời đúng, kể cả trong trường hợp bất lợi nhất cho nó (vẫn rẻ hơn 3,6 đến 5 lần).
- **Nhánh LiteLLM thực chất là một mô hình cố định.** Vì nó luôn chọn mô hình rẻ nhất, kết quả của nó phản ánh GPT-4o-mini hơn là một thuật toán định tuyến.
- **Chưa thử tải cao.** Thí nghiệm chạy tuần tự. Phép thử sự cố chỉ có 5 câu hỏi và mô phỏng một loại lỗi (khóa truy cập không hợp lệ).

> **Phép thử sự cố cho thấy điều gì:** khi tắt OpenAI, Bifrost vẫn trả lời được 13/15 lượt, còn LiteLLM và Portkey đều không. Nhóm dự đoán trước là LiteLLM sẽ phục hồi, và dự đoán này sai. Phép thử này không dùng để chọn lại proxy, nó chỉ cho biết chi phí phải trả cho lựa chọn đã chốt, và là lý do phải bật fallback.

## Tiến độ dự án

| Phase | Nội dung | Trạng thái |
|---|---|---|
| A | Nền tảng: đăng nhập, quản lý agent, ví credit, mua agent, chat qua proxy | Xong |
| B | Chọn 4 bộ đề chuẩn và viết bộ chấm tự động | Xong |
| C | Cấu hình cách chọn mô hình cho cả 3 proxy | Xong |
| D | Công cụ chạy thí nghiệm tự động, ghi log từng lượt | Xong |
| E | Chạy 720 lượt, áp luật chọn, viết báo cáo kết quả | Xong |
| F | Tích hợp LiteLLM chính thức, bảo mật, kiểm thử, CI | Tiếp theo |
| G | Tính năng bổ sung (RAG, VNPay), triển khai, báo cáo cuối, demo | Sau đó |

Vòng nghiệp vụ tối thiểu (tạo agent, mua agent, chat qua proxy, trừ credit) đã chạy được. Phần đóng góp khoa học của khóa luận đã hoàn thành.

## Việc tiếp theo và xin ý kiến thầy

1. Tích hợp LiteLLM chính thức vào Conduit, bật fallback, rồi chạy lại phép thử sự cố để xác nhận đã phục hồi được.
2. Viết test cho việc trừ credit khi nhiều yêu cầu đến cùng lúc (đảm bảo ví không bị âm), thêm kiểm thử bảo mật và CI.
3. Làm các tính năng bổ sung theo thứ tự ưu tiên, triển khai, viết báo cáo cuối và chuẩn bị demo.

**Em xin ý kiến thầy ba điểm:**

1. Kết luận chọn LiteLLM kèm điều kiện bật fallback có hợp lý không, khi độ chính xác của nó chỉ vượt mức tối thiểu 80% một khoảng nhỏ?
2. Hiện chưa có chức năng để người dùng tự nâng tài khoản lên vai trò Creator (đang sửa tay trong cơ sở dữ liệu). Thầy muốn làm theo hướng nào?
3. Agent hiện chưa có lời nhắc hệ thống (system prompt) riêng nên trả lời khá chung chung. Nên lấy lời nhắc từ phần giới thiệu agent hay thêm một trường riêng?

---

Dữ liệu thô và mã chạy lại được nằm trong kho mã của dự án (thư mục `experiments`). Báo cáo chi tiết kỹ thuật: `docs/experiment-results.md`.
