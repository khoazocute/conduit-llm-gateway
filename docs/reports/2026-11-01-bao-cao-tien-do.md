# Conduit: đánh giá routing proxy và tiến độ dự án

**Báo cáo tiến độ khóa luận · 01/11/2026**
Nguyễn Văn Lê Hùng (23520570) · Võ Đăng Khoa (23520758) · GVHD: TS. Nguyễn Thanh Bình, ThS. Trần Vĩnh Khiêm

Bản Word kèm 6 biểu đồ: `2026-11-01-bao-cao-tien-do.docx` (cùng thư mục).

---

## Tóm tắt

- **Đóng góp chính đã xong:** đánh giá 3 routing proxy mã nguồn mở trên 720 lượt gọi thật, theo luật quyết định khóa trước, và **chọn LiteLLM**.
- **Điều kiện đã thực hiện:** LiteLLM đã tích hợp vào Conduit, bật cơ chế dự phòng (fallback). Phép thử khóa OpenAI: phục hồi 15/15 lượt (trước đó 0/15).
- **Tiến độ:** 6/7 phase, 55/63 task trong tracker (87%). Phase G (phần mở rộng, deploy, viết báo cáo, demo) bắt đầu 02/11, các mốc kéo sớm 1 tuần.
- **Chi phí API đã dùng:** khoảng $0,62 (OpenAI $0,25, Anthropic $0,37).

## 1. Bài toán và câu hỏi nghiên cứu

Conduit gọi các mô hình AI (GPT, Claude, Gemini) qua một lớp trung gian gọi là **routing proxy**. Với mỗi câu hỏi, proxy quyết định gửi sang mô hình nào. Mô hình rẻ thì tiết kiệm nhưng dễ sai, mô hình đắt thì ngược lại.

```
Câu hỏi (80 câu) → Conduit (chat như người dùng thật) → 1 trong 3 proxy → Mô hình AI → Chấm tự động
```

**Câu hỏi nghiên cứu:** với cùng mục tiêu "trả lời đạt yêu cầu, chi phí thấp nhất", cùng một nhóm mô hình, cùng bộ đề và cùng điều kiện vận hành, trong LiteLLM, Bifrost và Portkey, proxy nào cho chi phí thấp nhất mà vẫn đạt chất lượng, và phải đánh đổi gì về thời gian chờ?

Câu hỏi bám theo yêu cầu của thầy ở buổi họp 03/10: "đáp ứng được yêu cầu, tối ưu về chi phí". Mỗi lượt đánh giá đi qua ứng dụng Conduit thật, không gọi thẳng proxy.

## 2. Ba proxy và nhóm mô hình

| Proxy | Chọn mô hình dựa vào | Luật cụ thể |
|---|---|---|
| **LiteLLM** (Python) | Giá: luôn gửi sang mô hình rẻ nhất | cost-based routing → mô hình rẻ nhất còn hoạt động |
| **Bifrost** (Go) | Độ khó: tự phân loại câu hỏi thành 3 mức | Dễ → gpt-4o-mini · Vừa → claude-haiku · Khó → gpt-4o |
| **Portkey** (TypeScript) | Độ dài câu hỏi, theo ngưỡng nhóm đặt; ứng dụng phải tự tính và gửi kèm | < 211 ký tự → gpt-4o-mini · 211–384 → claude-haiku · ≥ 385 → gpt-4o |

**Nhóm mô hình (5 mô hình, 3 tầng giá):** rẻ: GPT-4o-mini, Gemini Flash · trung: Claude Haiku · đắt: GPT-4o, Claude Sonnet.

Claude Sonnet bị loại khỏi cả 3 đường định tuyến sau khi đo thật: đây là mô hình suy luận, nó dùng hết giới hạn token để "suy nghĩ" rồi trả về câu trả lời rỗng nhưng vẫn tính tiền, và từ chối tham số temperature. Nhóm ghi lại điều này như một phát hiện của khóa luận.

## 3. Bộ đánh giá

Nhóm dùng **4 bộ đề công khai** thường dùng trong các bài báo khoa học. Mỗi bộ lấy ngẫu nhiên 20 câu từ tập test chính thức với seed cố định (20261014). Cả 4 bộ đều chấm tự động theo đúng cách của bài báo gốc.

| Bộ đề | Đo năng lực gì | Cách chấm (metric chuẩn) | Số câu |
|---|---|---|---:|
| **MMLU** | Kiến thức học thuật đa lĩnh vực, trắc nghiệm 4 đáp án | Accuracy: so chữ cái đáp án | 20 / 14.042 |
| **GSM8K** | Toán đố nhiều bước, cấp tiểu học và THCS | Exact match: so số cuối cùng | 20 / 1.319 |
| **HumanEval** | Viết hàm Python từ chữ ký và mô tả | pass@1: chạy bộ test gốc thật | 20 / 164 |
| **IFEval** | Làm đúng chỉ thị khi viết văn bản tự do | Strict: verifier chính thức của Google | 20 / 541 |

**Ví dụ câu hỏi:**

| Bộ đề | Câu hỏi (rút gọn) | Đáp án / cách chấm |
|---|---|---|
| MMLU | Cache direct-mapped 2KB, block 8 byte, chính sách write-back. Vòng lặp A[i] = A[i] + B[2*i] ghi bao nhiêu byte xuống bộ nhớ? A. 0 · B. 256 · C. 1024 · D. 2000 | A |
| GSM8K | Raymond sinh trước Samantha 6 năm. Raymond có con trai năm 23 tuổi. Samantha hiện 31 tuổi. Con trai Raymond sinh cách đây bao nhiêu năm? | 14 |
| HumanEval | Viết hàm factorize(n) trả về các thừa số nguyên tố từ nhỏ đến lớn, ví dụ factorize(70) = [2, 5, 7]. | Đạt khi qua mọi test ẩn |
| IFEval | Viết bảng tiêu chí đánh giá kỹ năng kỹ thuật của kỹ sư phần mềm, chỉ dùng tiếng Punjabi. | Code kiểm tra ngôn ngữ của câu trả lời |

**Giữ giống nhau cho cả 3 proxy:**
- Cùng 80 câu, 0-shot; mỗi câu chạy **3 lần** trên mỗi proxy: 80 × 3 × 3 = **720 lượt**.
- temperature = 0, max_tokens = 1024, timeout 45 giây, retry 2 lần.
- Cùng nhóm mô hình và bảng giá; mọi lượt được ghi vào bảng `routing_decisions`.
- Thứ duy nhất khác nhau là **cách chọn mô hình** của mỗi proxy, cũng chính là thứ cần đo.

**Vì sao chọn bộ đề này:**
- Thay bộ 30 câu tiếng Việt nhóm tự soạn (đổi ngày 14/10, D10): bộ công khai thì người khác kiểm lại được.
- Chấm hoàn toàn tự động bằng metric gốc, không có thiên vị khi chấm.
- Loại MT-Bench vì metric chuẩn của nó cần GPT-4 làm giám khảo.
- Dùng 0-shot thay cho 5-shot/8-shot của bài báo gốc: prompt dài sẽ khiến Portkey gửi mọi câu sang mô hình đắt. Chỉ so 3 proxy với nhau nên vẫn công bằng; sẽ khai báo trong báo cáo.

## 4. Luật quyết định (khóa trước khi chạy)

Luật nằm trong tài liệu dự án từ commit đầu tiên (`9d6dfd7`, 11/09), hơn 5 tuần trước khi chạy chính thức (19–20/10). Nhóm có sửa thiết kế thí nghiệm trước khi chạy, nhưng không sửa luật, kể cả ngưỡng 80%.

1. Loại proxy trả lời đúng dưới 80%.
2. Trong số còn lại, chọn proxy có chi phí trung bình mỗi câu hỏi thấp nhất.
3. Nếu chi phí chênh nhau dưới 5%, chọn proxy có thời gian chờ (p95) thấp hơn.
4. Nếu vẫn hòa, chọn proxy ổn định hơn (cùng câu hỏi hỏi 3 lần vẫn gửi sang cùng một mô hình).

## 5. Kết quả

| Tiêu chí | LiteLLM | Bifrost | Portkey |
|---|---:|---:|---:|
| Độ chính xác (tối thiểu 80%) | 83,8% | 87,5% | **92,1%** |
| Chi phí mỗi câu hỏi (USD) | **$0,000123** | $0,000562 | $0,000793 |
| Chi phí cho 1.000 câu đúng | **$0,15** | $0,64 | $0,86 |
| Thời gian chờ p95 | **6,3 giây** | 7,2 giây | 6,9 giây |
| Độ ổn định qua 3 lần lặp | **100%** | 97,5% | **100%** |
| Số lượt lỗi (trên 240) | **0** | 2 | **0** |

**Áp dụng luật:**

| Bước | Kết quả |
|---|---|
| 1. Loại dưới 80% | Cả ba đều trên 80%, không loại ai. |
| **2. Chi phí thấp nhất** | **LiteLLM → chọn LiteLLM.** Rẻ hơn Bifrost 4,55 lần, Portkey 6,43 lần. |
| 3. Chênh dưới 5% thì xét p95 | Không cần: chi phí chênh hơn 4 lần. |
| 4. Còn hòa thì xét độ ổn định | Không cần. |

**Mỗi proxy đã gửi câu hỏi sang mô hình nào (trên 240 lượt):**

| Proxy | gpt-4o-mini (rẻ) | claude-haiku (trung) | gpt-4o (đắt) | lỗi |
|---|---:|---:|---:|---:|
| LiteLLM | 100% | 0% | 0% | 0% |
| Bifrost | 57% | 18% | 24% | 1% |
| Portkey | 31% | 42% | 26% | 0% |

**Độ chính xác theo bộ đề (60 lượt mỗi ô):**

| Bộ đề | LiteLLM | Bifrost | Portkey |
|---|---:|---:|---:|
| MMLU | 80% | 90% | **95%** |
| GSM8K | 75% | 85% | **90%** |
| HumanEval | **95%** | **95%** | 93,3% |
| IFEval | 85% | 80% | **90%** |

LiteLLM yếu nhất ở GSM8K (toán nhiều bước), đúng chỗ mô hình rẻ dễ sai. Ở HumanEval cả ba gần như ngang nhau.

## 6. Kiểm chứng kết quả

**Giả thuyết ghi trước khi chạy (14/10):**

| Giả thuyết | Thực tế | Kết luận |
|---|---|---|
| H1 · LiteLLM rẻ nhất, chính xác thấp nhất, dễ trượt ngưỡng 80% | Rẻ nhất và thấp nhất (83,8%), nhưng qua ngưỡng, dư 9 lượt | Đúng 2/3 |
| H2 · Bifrost chính xác hơn nhưng đắt hơn, chậm hơn ~257 ms, xếp nhầm câu trắc nghiệm dễ lên mức khó | Chính xác hơn, đắt hơn 4,55 lần, chậm hơn 818 ms, 51/60 lượt MMLU bị xếp lên mức khó | Đúng 3/4 |
| H3 · Portkey nằm giữa, phụ thuộc ngưỡng độ dài nhóm đặt | Không nằm giữa: chính xác nhất và đắt nhất. Phụ thuộc ngưỡng: đúng | Đúng 1/2 |

**Kết luận có vững không:**
- Bỏ lần lượt từng bộ đề (4 trường hợp): cả 4 vẫn chọn LiteLLM.
- Mở rộng từ 10 lên 20 câu mỗi bộ (D14): cách mở rộng ghi trước khi chạy, giữ nguyên 10 câu cũ; kết luận không đổi.
- Ở trường hợp bất lợi nhất, chi phí cho mỗi câu đúng của LiteLLM vẫn rẻ hơn 3,6–5,0 lần.

> **Điểm cần nói rõ:** khoảng tin cậy 95% của LiteLLM là 75,7% đến 91,8%, vẫn chứa ngưỡng 80%. Nếu ngưỡng là 85% thì Bifrost được chọn. Ngưỡng 80% đã khóa từ đầu nên nhóm giữ nguyên và ghi rõ trong phần giới hạn. Muốn chắc chắn LiteLLM trên 80% cần khoảng 5.000 câu.

**Phép thử sự cố (khóa OpenAI, 5 câu × 3 lần mỗi proxy):**

| Proxy | 20/10 (lần đầu) | 27/10 (bật fallbacks, D16) |
|---|---:|---:|
| LiteLLM | 0/15 | **15/15** |
| Bifrost | 13/15 | 14/15 |
| Portkey | 0/15 | 0/15 |

Sau khi bật fallbacks và không retry các lỗi vĩnh viễn, LiteLLM chuyển sang Claude Haiku trong khoảng 4,4 giây. Đây là cấu hình Conduit đang chạy. Phép thử này không dùng để chọn lại proxy.

**Giới hạn:**
- **Cỡ mẫu nhỏ:** đủ để thấy chênh lệch chi phí (4–6 lần), chưa đủ để khẳng định chắc LiteLLM trên 80%.
- **Nhánh LiteLLM thực chất là một mô hình cố định:** kết quả phản ánh GPT-4o-mini hơn là một thuật toán định tuyến.
- **Lệch khỏi protocol gốc:** 0-shot thay cho few-shot. Phép thử sự cố chỉ có 5 câu và một loại lỗi.

## 7. Tiến độ dự án

| Phase | Hạn (tracker) | Thực tế | Task xong | Bị bỏ |
|---|---|---|---:|---:|
| Nền tảng | 11/09 – 20/09 | đúng hạn | 15/15 | 0 |
| A · Chốt quyết định | 21/09 – 27/09 | xong 29/09 (trễ 2 ngày) | 6/6 | 0 |
| B · Dữ liệu thực nghiệm | 24/09 – 27/09 | xong 20/10 (mở lại 14/10) | 5/5 | 2 |
| C · Routing 3 proxy | 26/09 – 04/10 | xong 20/10 (mở lại 14/10) | 8/8 | 0 |
| D · Runner, chạy thử | 06/10 – 11/10 | xong 03/10 (sớm 8 ngày) | 6/6 | 1 |
| E · Chạy chính thức | 12/10 – 25/10 | xong 20/10 (sớm 5 ngày) | 4/4 | 3 |
| F · Tích hợp + kiểm thử | 23/10 – 08/11 | xong 29/10 (sớm 10 ngày) | 11/12 | 0 |
| G · Mở rộng, deploy, báo cáo, demo | 22/11 – 13/12 | kế hoạch mới 02/11 – 06/12 | 0/7 | 0 |

Phase B và C kết thúc trễ vì nhóm mở lại có chủ đích ngày 14/10 để đổi sang 4 bộ đề công khai; việc này làm trước khi chạy chính thức nên luật quyết định không bị ảnh hưởng. 6 task "bị bỏ" là các task chấm tay bằng rubric, được thay bằng chấm tự động (D10). Tính trên 63 task thật: 55 xong (87%). Phase G ít task nhưng gồm các việc nặng nhất còn lại.

**Hệ thống Conduit:** vòng nghiệp vụ tối thiểu đã khép kín và chạy với dữ liệu thật (creator tạo agent → admin duyệt → người dùng mua agent → chat qua LiteLLM → trừ credit theo token).

| Chức năng | Trạng thái |
|---|---|
| Đăng ký (chọn vai trò người mua / creator), đăng nhập JWT | Xong |
| Sàn agent; creator tạo agent kèm system prompt riêng; admin duyệt | Xong |
| Ví credit; trừ credit an toàn khi nhiều yêu cầu cùng lúc | Xong |
| Mua agent qua Mock Payment; webhook có chữ ký, không cộng credit 2 lần | Xong |
| Chat streaming qua LiteLLM, tự chuyển nhà cung cấp khi OpenAI lỗi | Xong |
| Admin quản lý API key (mã hóa AES-GCM) và bảng giá mô hình | Xong |
| Dự phòng sang Gemini | Đã cấu hình, đang kiểm lại |
| RAG, VNPay sandbox, deploy | Phase G |

**Kiểm thử:**
- 89 unit test backend, 66 kiểm thử API đầu-cuối, 72 test cho công cụ thực nghiệm. CI GitHub Actions xanh cả 3 job.
- Test bảo mật được kiểm bằng cách cố tình làm hỏng code: bỏ khóa phiên bản ví thì test trừ credit đồng thời báo lỗi; cho lộ system prompt cho người mua thì 4 test báo lỗi.
- Load test: 100 người dùng ảo, 0% lỗi, p95 danh sách agent 438 ms (ngưỡng 500 ms). Chat giả lập 25 người dùng: 23.640 lượt, 0 lỗi, p95 211 ms (không gọi LLM có phí).

## 8. Việc tiếp theo, rủi ro và xin ý kiến thầy

| Mốc | Người | Hạn cũ | Hạn mới |
|---|---|---:|---:|
| RAG, VNPay sandbox, kiểm lại dự phòng, test bảo mật RAG | Khoa (RAG), Hùng (VNPay) | 22/11 | **15/11** |
| Deploy lên địa chỉ công khai | Hùng | 29/11 | **22/11** |
| Báo cáo khóa luận, bản nháp đầy đủ | Cả hai | 06/12 | **29/11** |
| Demo đầu-cuối | Cả hai | 13/12 | **06/12** |

**Rủi ro:**
- **Cao:** chưa có ngày nộp và ngày bảo vệ thật, nên các hạn trên vẫn là ước lượng.
- **Cao:** báo cáo khóa luận chưa viết; bắt đầu tuần này, chương Thực nghiệm đã có sẵn nội dung gốc.
- **Vừa:** deploy chưa thử lần nào, chi phí hosting chưa chốt.
- **Vừa:** RAG làm từ đầu (mới có bảng dữ liệu, chưa có code).

**Em xin ý kiến thầy ba điểm:**

1. Ngày nộp báo cáo, ngày bảo vệ và mẫu định dạng (Word/LaTeX, số trang).
2. Cách trình bày kết luận phụ thuộc ngưỡng 80%: ghi ở phần giới hạn như hiện tại đã đủ chưa.
3. Trong Phase G, nếu thiếu thời gian thì ưu tiên RAG hay VNPay.

---

Dữ liệu thô và mã chạy lại được nằm trong thư mục `experiments`. Báo cáo kỹ thuật chi tiết: `docs/experiment-results.md`; thiết kế thí nghiệm: `docs/experiment-design.md`.
