# Kế hoạch chi tiết — Khoa, nhánh vector RAG (TASK-74 → 77)

Theo `docs/tasks/2026-11-16/tasks.md` (D21, đóng góp 2: RAG cấu hình được). Viết 24/11/2026.
Hạn bản nháp **27/11**. Điểm cắt **24/11**: phần chưa chạy được thì bản nháp ghi thiết kế + trạng thái thật,
**không bịa kết quả**.

> **Cập nhật 29/11:** bộ dữ liệu ở mục 3 đã đổi. Chốt với Hùng (28/11): chunking dùng **Qasper, ConditionalQA,
> Natural Questions, UIT-ViQuAD**; index dùng **BEIR-FiQA**. Trạng thái và quyết định mới nhất: `log-khoa.md`.

Nguyên tắc giữ suốt kế hoạch:
- Đánh giá **đăng ký trước** (giống D14, D18): bộ dữ liệu, tham số, định nghĩa "đoạn đúng", chỉ số, giả thuyết
  được commit **trước** khi chạy lượt có phí nào.
- Mọi lời gọi embedding/LLM đi **qua LiteLLM** (CLAUDE.md mục 5).
- Đợt gọi có phí **> 10 lượt**: nêu số lượt + ước tính chi phí, **Hùng duyệt trước** (D1).
- Chỉ sửa file thuộc nhánh của mình; điểm chạm với Hùng đi qua hợp đồng (mục 1).

---

## 1. Các quyết định phải chốt (và hạn)

| # | Quyết định | Đề xuất | Hạn | Ai chốt |
|---|---|---|---|---|
| Q1 | Hợp đồng chung (`Chunk`, `/chunk`, `RagRetriever`, `rag_config`, V4/V5) | Như bản đề xuất đã gửi Hùng; ghi vào `tasks.md` mục 7 | **24/11** | Khoa + Hùng |
| Q2 | **Bộ benchmark** cho đánh giá chunking | **Qasper** (bộ chính) + một phần **Natural Questions** (bộ phụ), xem mục 3 | **24/11** (trước khi viết script đánh giá) | Khoa, báo Hùng |
| Q3 | Tham số chunking | Tối đa 1.000 ký tự, gối 150 (cố định, đệ quy); tối thiểu 200 / tối đa 1.500 (cấu trúc, ngữ nghĩa); ngưỡng ngữ nghĩa phân vị 95 | 24/11 | Khoa |
| Q4 | Index pgvector | Index là **cấu hình toàn hệ thống**, không theo từng agent; đánh giá 3 cách ở TASK-76; mặc định chọn sau khi có số | 24/11 | Khoa, báo Hùng |
| Q5 | Có dùng RAGAS không | Chỉ số chính: Recall@k, MRR, nDCG (chấm bằng code). RAGAS: chỉ số không cần LLM, hoặc Faithfulness trên mẫu nhỏ, là bổ sung | 25/11 | Khoa, hỏi thầy buổi sau |
| Q6 | Duyệt chi phí | Gửi ước tính ở mục 6 | 24/11 | Hùng |

---

## 2. Lịch

| Ngày | Buổi | Việc | Đầu ra |
|---|---|---|---|
| **24/11** | Sáng | Q1: gửi hợp đồng cho Hùng. Nghiên cứu (mục 4.1). Commit phần hiển thị Markdown ở trang chat | Hợp đồng gửi đi; ghi chú 3 dòng/phương pháp |
| | Sáng | **Q2: chọn và kiểm bộ benchmark** (mục 3) | Bộ dữ liệu, giấy phép, cách tải đã xác nhận |
| | Chiều | TASK-75 bước 1–2: `normalize`, `chunk_fixed`, `chunk_recursive` + test | Test pass |
| | Tối | TASK-75 bước 4 (ngữ nghĩa) + test embedding giả; bước 5 (`/chunk`) | Báo Hùng có `/chunk` |
| **25/11** | Sáng | TASK-75 bước 3 (theo cấu trúc, nếu kịp). Chuẩn bị dữ liệu (mục 3.4). **Bản đăng ký trước** (mục 5.1) + gửi Hùng duyệt chi phí | Commit đăng ký trước |
| | Chiều | Script đánh giá TASK-76; chạy thử 10 câu; chạy đủ | Bảng kết quả chunking |
| | Tối | Đánh giá index (mục 4.2-B) | Bảng kết quả index |
| **26/11** | Sáng | TASK-77: sửa PWNED + đo trước/sau (nếu Hùng duyệt) | Số liệu trước/sau |
| | Chiều | Viết 5.4.2 (thay bản "chưa có số" của Hùng), bổ sung 3.1.4, 4.4.4; báo Hùng cập nhật 6.1–6.3. Review phần Hùng sửa (3.3–3.6, 5.2) | Doc cập nhật |
| | Tối | V5 + nối `rag_config` (nếu V4 của Hùng đã có); merge main, chạy toàn bộ test | Test pass |
| **27/11** | | Nộp bản nháp | |

Sau 27/11: UIT-ViQuAD (tiếng Việt), RAGAS đầy đủ, chấm tay đối chiếu, tối ưu index theo kết quả.

---

## 3. Chọn bộ benchmark (Q2)

### 3.1. Tiêu chí
1. **Đã công bố** ở hội nghị/tạp chí uy tín (yêu cầu của thầy).
2. **Tài liệu dài, nguyên văn**, chưa bị cắt sẵn thành đoạn ngắn (để so được cách cắt).
3. **Có đánh dấu bằng chứng** (đoạn/câu chứa đáp án) → chấm truy hồi bằng code, không cần LLM.
4. Có đáp án chuẩn (để có thể chạy RAGAS về sau).
5. Giấy phép cho phép dùng trong nghiên cứu.

### 3.2. Ứng viên
| Bộ | Công bố | Hợp chunking? | Ghi chú |
|---|---|---|---|
| **Qasper** | Dasigi và cộng sự, NAACL 2021 | ⭐ Rất hợp | Toàn văn bài báo NLP, có đoạn bằng chứng, chỉ số chính thức là Answer F1 |
| **Natural Questions** | Kwiatkowski và cộng sự, TACL 2019 | ⭐ Hợp | Toàn trang Wikipedia, có "long answer" (đoạn chứa đáp án); file gốc rất lớn |
| MultiHop-RAG | Tang & Yang, COLM 2024 | Hợp | Kho tin tức, câu hỏi nhiều bước |
| RAGBench | Friel và cộng sự, 2024 | Hợp | Đã được dùng để đánh giá chunking (arXiv 2410.13070) |
| UIT-ViQuAD | COLING 2020 | Hợp (tiếng Việt) | Sau 27/11 |
| HotpotQA, MS MARCO, BEIR | — | Không hợp cho chunking | Đoạn đã cắt sẵn; BEIR dùng được cho **đánh giá index** |

### 3.3. Đề xuất
- **Bộ chính: Qasper.** Mẫu: khoảng **50 bài báo, 150–200 câu hỏi** có bằng chứng dạng đoạn văn (bỏ câu "không trả lời được"
  và câu chỉ có bằng chứng trong bảng/hình), lấy ngẫu nhiên với **seed cố định**.
- **Bộ phụ: Natural Questions**, khoảng **100 câu** có long answer (bộ validation), để xem kết quả có đổi theo loại tài liệu.
- Phải kiểm trước khi dùng: **giấy phép**, **nơi tải chính thức**, **định dạng trường bằng chứng**.

### 3.4. Chuẩn bị dữ liệu
1. Tải, ghi phiên bản và mã băm (sha256) như `docs/benchmark-survey.md` đã làm cho phần proxy.
2. Ghép toàn văn mỗi tài liệu; chuẩn hóa bằng **đúng hàm `normalize()`** của chunker.
3. Tìm vị trí ký tự (`start`, `end`) của từng đoạn bằng chứng trong văn bản đã chuẩn hóa; bỏ câu hỏi không tìm được vị trí (ghi lại số câu bị bỏ).
4. Lưu thành `experiments/rag/data/<bộ>.jsonl`: `{doc_id, question, answers, evidence: [{start, end, text}]}`.
5. Thống kê: số tài liệu, độ dài trung bình, số câu hỏi, số bằng chứng mỗi câu.

---

## 4. TASK-75: chunking + index

### 4.1. Nghiên cứu (đọc gì, lấy gì)
| Tài liệu | Lấy gì |
|---|---|
| LangChain Text Splitters (Recursive, MarkdownHeader, SemanticChunker) | Thuật toán tham khảo |
| "5 Levels of Text Splitting" (Greg Kamradt) | Khung phân loại 5 cấp (trích như tài liệu trực tuyến) |
| "Is Semantic Chunking Worth the Computational Cost?" (arXiv 2410.13070) | Cách đánh giá bằng bằng chứng; kết luận cho phần thảo luận |
| README pgvector (HNSW, IVFFlat, `<=>`) | Cú pháp và tham số index |
| Malkov & Yashunin, HNSW (IEEE TPAMI) | Lý thuyết cho 3.1.4 |

Ghi 3 dòng mỗi phương pháp: ý tưởng, tham số, ưu/nhược.

### 4.2-A. Các chunker (`ai-service/ingest.py`) — tự viết, không dùng LangChain
Định dạng: `Chunk{text, index, start_char, end_char, method, metadata}`.
**Bất biến bắt buộc:** `normalized_text[start_char:end_char] == chunk.text`.

| Bước | Việc | Ghi chú |
|---|---|---|
| 1 | `normalize(text)`: `\r\n`→`\n`, gộp khoảng trắng trong dòng, **giữ** `\n` và `\n\n` | Hàm hiện tại gộp cả xuống dòng → mất ranh giới đoạn |
| 1 | `chunk_fixed(text, size, overlap)` trả `Chunk` có vị trí | Giữ thuật toán cũ |
| 2 | `chunk_recursive`: tách theo `["\n\n", "\n", ". ", "? ", "! ", " "]`, đệ quy phần quá dài, gộp mảnh nhỏ, gối đầu ở ranh giới mảnh | Trường hợp khó: không có dấu chấm, câu > 1.000 ký tự |
| 3 | `chunk_structure`: cắt tại đầu mục (Markdown `#`, "Chương/Điều/khoản", tiêu đề mục bài báo); mục dài → đệ quy; mục ngắn → gộp; không có đầu mục → quay về đệ quy | Tiêu đề lưu ở `metadata.heading`, không ghép vào `text` |
| 4 | `chunk_semantic(text, embed_fn, percentile=95, min, max)`: tách câu → cửa sổ ±1 câu → embedding **1 lượt** → khoảng cách cosine liền kề → cắt ở phân vị 95 → gộp/cắt theo min/max | `embed_fn` truyền vào để test dùng embedding giả |
| 5 | `chunk(text, method, params, embed_fn)` gọi đúng chunker; endpoint `POST /chunk`; `/chunk-embed` nhận `method`, `params` (mặc định `fixed` 1000/150 để hành vi cũ không đổi) | Báo Hùng khi xong |
| 6 | Unit test (bảng dưới) | Điều kiện "Đạt khi" |

Unit test cho **mỗi** chunker: bất biến vị trí; không mất nội dung; không vượt kích thước tối đa; rỗng → `[]`; văn bản ngắn → 1 đoạn.
Riêng: đệ quy không cắt giữa câu ngắn; theo cấu trúc mỗi "Điều"/tiêu đề là một đoạn và quay về đệ quy khi không có đầu mục;
ngữ nghĩa cắt đúng chỗ đổi chủ đề với embedding giả và chỉ gọi `embed_fn` một lần.

### 4.2-B. Index
- **Migration V5** (Khoa): `kb_chunks` thêm `chunk_method`, `start_char`, `end_char`; `knowledge_bases` thêm
  `chunk_method`, `chunk_params`. Index mặc định tạo **sau** khi có kết quả đánh giá.
- **Đánh giá 3 cách index** trong script, trên **bảng thử riêng**, dữ liệu lớn (vector của một bộ BEIR, hoặc vector ngẫu nhiên
  ~50.000–100.000): quét toàn bộ / IVFFlat (`lists`, `probes`) / HNSW (`m`, `ef_construction`, `ef_search`).
  Đo: recall@k so với quét toàn bộ, độ trễ truy vấn (trung bình, p95), thời gian tạo index, dung lượng index.
- Kiểm cú pháp và tham số theo README pgvector đúng phiên bản trong `pgvector/pgvector:pg16`.

---

## 5. TASK-76: đánh giá chọn chunking tối ưu

### 5.1. Bản đăng ký trước (commit trước khi chạy)
- Bộ dữ liệu, phiên bản, mã băm, seed, cách lọc câu hỏi, cỡ mẫu.
- Tham số 4 chunker (Q3); mô hình embedding `text-embedding-3-small`; k = 1, 3, 5, 10.
- **Định nghĩa "đoạn đúng":** đoạn chứa ≥ 50% ký tự của một đoạn bằng chứng (hoặc chứa trọn câu bằng chứng ngắn). Chốt một định nghĩa, ghi lý do.
- Chỉ số chính: **Recall@k, MRR, nDCG@k**. Phụ: số đoạn, độ dài đoạn trung bình, độ trễ truy hồi, chi phí embedding.
- Giả thuyết: (H-R1) cố định có Recall@k thấp nhất; (H-R2) cấu trúc tốt nhất cho Qasper, ngữ nghĩa không vượt rõ đệ quy;
  (H-R3) HNSW giữ recall gần quét toàn bộ, nhanh hơn rõ khi dữ liệu lớn.
- Cam kết: báo cáo đúng kết quả dù giả thuyết sai; không đổi tham số sau khi thấy số.

### 5.2. Script (`experiments/rag/eval_chunking.py`)
1. Với mỗi chunker: cắt mọi tài liệu → embedding (gộp lượt) → lưu vector (cache file để chạy lại không tốn phí).
2. Embedding câu hỏi (gộp lượt, cache).
3. Truy hồi top-k **trong đúng tài liệu của câu hỏi** (giống lọc theo `agent_id`).
4. Tính chỉ số; xuất `experiments/rag/results/<ngày>/tables/*.csv` + biểu đồ.
5. Chạy thử 10 câu → kiểm → chạy đủ.

### 5.3. Đầu ra
Bảng 4 chunker × 2 bộ dữ liệu × chỉ số; kết luận chunking nào tốt nhất cho loại tài liệu nào; giá trị mặc định cho
`rag_config` và gợi ý hiển thị trên giao diện (gửi Hùng, TASK-79).

---

## 6. Chi phí (D1) — gửi Hùng duyệt

| Đợt | Ước tính | Ghi chú |
|---|---|---|
| Embedding tài liệu Qasper 50 bài × 4 chunker | ~vài cent | `text-embedding-3-small` $0,02/1M token |
| Embedding câu hỏi (~300) | < 1 cent | Gộp lượt |
| Chunker ngữ nghĩa (embedding từng câu) | ~vài cent | |
| Natural Questions ~100 trang | ~vài cent | |
| TASK-77: ~20 tài liệu × 2 câu hỏi × trước/sau ≈ 80 lượt chat gpt-4o-mini | ~$0,02–0,05 | |
| (Tùy chọn) RAGAS Faithfulness trên 30–50 mẫu | ~$0,1–0,5 | Chỉ khi thầy yêu cầu |

Tổng dự kiến **< $1**, nhưng số lượt gọi > 10 nên **phải xin duyệt trước**.

---

## 7. TASK-77: bảo mật RAG
- Cách ly dữ liệu giữa creator: **đã có test** (`RagTenantIsolationTest`).
- PWNED: ~20 tài liệu chèn lệnh (có mã đánh dấu để chấm bằng code) × câu hỏi liên quan / không liên quan;
  đo tỷ lệ tấn công thành công **trước** (cách hiện tại) và **sau** biện pháp sửa (câu cố định trong lượt `system` khi có ngữ cảnh,
  ± lọc theo ngưỡng độ liên quan). Không đổi request của agent không có tài liệu.

---

## 8. Phần viết
- **5.4.2:** thay bản "kế hoạch, chưa có số" của Hùng bằng kết quả TASK-76 (+ index).
- **3.1.4, 4.4.4:** bổ sung 4 chunker, index, thiết kế đã hiện thực (Hùng đã viết khung).
- Báo Hùng cập nhật **6.1–6.3** khi có số.
- Review: đọc lại **3.3–3.6, 5.2** (Hùng đã sửa phần của Khoa), kiểm **cột 4 Bảng 3.5**, ghi "Review – Khoa" trong `log-hung.md`.
- Chụp lại Hình **5.2, 5.3, 5.6** bằng tài khoản demo (tránh lộ email cá nhân).

---

## 9. Rủi ro và phương án cắt
| Rủi ro | Phương án |
|---|---|
| Không kịp 4 chunker | Cắt chunker theo cấu trúc trước; 3 chunker (cố định, đệ quy, ngữ nghĩa) vẫn đủ "Đạt khi" |
| Natural Questions quá lớn, tải lâu | Chỉ dùng Qasper; NQ để sau 27/11 |
| V4 của Hùng chưa có | Chunker + đánh giá vẫn chạy độc lập; phần đọc `rag_config` ghi "thiết kế" trong bản nháp |
| Hùng chưa duyệt chi phí | Chạy lớp truy hồi với embedding đã cache trên mẫu ≤ 10 lượt; chờ duyệt cho phần còn lại |
| Kết quả không như giả thuyết | Báo cáo đúng như vậy (đã đăng ký trước) |

---

## 10. Checklist
- [ ] Q1 hợp đồng gửi Hùng / chốt — 24/11
- [ ] Q2 chọn + kiểm bộ benchmark (Qasper, NQ) — 24/11
- [ ] Commit hiển thị Markdown trang chat — 24/11
- [ ] `normalize`, `chunk_fixed`, `chunk_recursive` + test — 24/11
- [ ] `chunk_semantic` + test, `/chunk` — 24/11
- [ ] `chunk_structure` + test — 25/11 (nếu kịp)
- [ ] Chuẩn bị dữ liệu + bản đăng ký trước + Hùng duyệt chi phí — 25/11
- [ ] TASK-76 chạy xong, có bảng + kết luận — 25/11
- [ ] Đánh giá index — 25/11
- [ ] TASK-77 trước/sau — 26/11
- [ ] 5.4.2, 3.1.4, 4.4.4 trên Doc; review phần Hùng — 26/11
- [ ] V5 + `rag_config` (nếu có V4) — 26/11
- [ ] Ghi `log-khoa.md`, merge main, chạy toàn bộ test — 26/11
- [ ] Nộp bản nháp — 27/11
