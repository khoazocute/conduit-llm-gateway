# Log tuần 16/11 (RAG theo D21) — Khoa

Theo `docs/tasks/2026-11-16/tasks.md` (mục 3, nhánh "nạp tài liệu, chunking, vector") và kế hoạch chi tiết
`docs/tasks/2026-11-16/plan-khoa.md`. Test Python ai-service **96/96** (cũ `test_ingest` 20 + mới `test_chunking` 60, `test_chunk_api` 16). Phần trong log này
**không gọi API có phí** (mọi test dùng embedding giả; chạy thử index dùng vector tổng hợp).

> Trạng thái code: chunking, endpoint và script index **đang ở máy Khoa, chưa commit**. Hùng xác nhận thì
> Khoa commit + push lên `dangkhoa`.

## Việc đã làm

| Task | Kết quả | File | Hùng review gì |
|---|---|---|---|
| **TASK-74** đường vector | ✅ Đã push 21/11 (tải tài liệu → chunk → embedding → `kb_chunks` → truy hồi lọc `agent_id`). Lưu ý: 2 knowledge base thử bị xóa cùng dữ liệu test khi dọn DB 23/11 (còn bản sao lưu) → hiện `knowledge_bases` = 0, demo RAG cần nạp lại tài liệu | `KnowledgeBase*Service`, `ingest.py` | — |
| **TASK-75** 4 cách chunking | ✅ Level 1–4 theo "5 Levels of Text Splitting" (Kamradt); Level 5 (agentic, gọi LLM để chia) loại: tốn phí (D1), không tái lập, viết lại văn bản. (1) **Cố định** `chunk_fixed`: cắt theo ký tự, lùi về ranh giới từ, gối đầu ≤ `overlap`. (2) **Đệ quy** `chunk_recursive` = **đúng thuật toán `RecursiveCharacterTextSplitter` của LangChain** (tách đoạn văn → dòng → câu → từ; chỉ gộp các mảnh liền nhau CÙNG CẤP, mảnh quá dài được cắt riêng; gối đầu bằng mảnh trọn vẹn). Kiểm chứng với thư viện `langchain-text-splitters` 1.2.0 trên 47 tài liệu × 3 cấu hình: **2.855/2.894 đoạn trùng nguyên văn**; phần khác chỉ do cách đếm khoảng trắng vào giới hạn `size` (LangChain đếm cả khoảng trắng sau mỗi mảnh nên đóng đoạn sớm hơn vài ký tự; mình đếm đúng độ dài chữ trong đoạn, không bao giờ vượt `size`). Bản đầu gộp phẳng các mảnh nên trộn đoạn văn vừa với đầu đoạn văn quá dài kế tiếp (563 đoạn bị trộn trên cùng bộ kiểm) — đã sửa, còn 0. (3) **Theo cấu trúc** `chunk_structure`: cắt tại đầu mục (Markdown `#`, Phần/Chương/Mục/Điều, mục đánh số kiểu `2.1 Data`, Abstract/Kết luận…); mục dài cắt đệ quy *bên trong mục*; mục ngắn gộp; không có đầu mục → giống hệt đệ quy; tiêu đề lưu ở `metadata.heading`/`heading_path`. (4) **Ngữ nghĩa** `chunk_semantic`: tách câu bằng cùng biểu thức với bản gốc Kamradt / `SemanticChunker` (`(?<=[.?!])\s+`, chưa xử lý chữ viết tắt — ghi vào hạn chế) → cửa sổ ±1 câu → embedding **1 lượt** → cắt khi khoảng cách cosine > phân vị 95 → gộp theo min/max. Câu dài hơn `max_size` được chia thành vài mảnh gần `max_size` (bản đầu chia thành từng từ lẻ, mỗi từ một cửa sổ embedding — đã sửa). **Bất biến cho mọi cách:** `normalize(t)[start_char:end_char] == chunk.text` (TASK-76 cần để biết đoạn nào chứa bằng chứng). `normalize()` giữ `\n`/`\n\n` (hàm cũ gộp mất ranh giới đoạn) và chuẩn hóa Unicode NFC (tiếng Việt từ PDF hay ở dạng NFD) | `ai-service/chunking.py`, `tests/test_chunking.py` (60 test) | Đọc 4 docstring; chạy `python -m unittest discover -s tests` |
| **TASK-75** nối vào ai-service | ✅ Hàm chung `chunk(text, method, params, embed_fn)` (kiểm tham số lạ/sai kiểu/> 8.000 ký tự). **`POST /chunk`**: chỉ cắt, không embedding — **đường graph (TASK-78) gọi cái này**. **`/chunk-embed`** nhận thêm `method`, `params` (form, `params` là chuỗi JSON); không gửi → cố định `CHUNK_SIZE`/`CHUNK_OVERLAP` (1000/150) như cũ. Kết quả thêm `start_char`, `end_char`, `method`, `metadata`, `source`, `chunking_prompt_tokens`; 3 trường Java đang đọc (`index`, `text`, `embedding`) giữ nguyên → **backend không phải sửa**. Semantic chia lô embedding ≤ 2.048 đầu vào/request. Kiểm trên service thật (tài liệu `experiment-results.md`): fixed 60 đoạn, recursive 63, structure 74 | `ai-service/main.py`, `tests/test_chunk_api.py` (16 test) | Gọi `/chunk` với 1 tài liệu của mày, xem `metadata.heading` |
| **TASK-75** index | 🟡 Script đánh giá 3 cách: quét toàn bộ / IVFFlat / HNSW, trên **DB riêng `conduit_eval`** (không đụng dữ liệu Conduit). Đo recall@k so với top-k chính xác (numpy), độ trễ server (EXPLAIN ANALYZE: TB, p50, p95), tỉ lệ trả thiếu kết quả, thời gian tạo, dung lượng; cả truy vấn toàn bảng và **lọc theo agent** (như Conduit). pgvector trong container: **0.8.6**. **Mới chạy thử trên vector tổng hợp** (xem phát hiện A, B) — chưa phải kết quả báo cáo. Chưa chọn index mặc định, chưa có V5 | `experiments/rag/eval_index.py`, `experiments/rag/results/index-synthetic-20261125-010305/` | Duyệt chi phí FiQA (mục "Cần Hùng") |
| **TASK-76** chọn chunking tối ưu | 🟡 **Chọn xong bộ dữ liệu, chưa chạy.** Theo góp ý của thầy, bỏ "~20 câu hỏi tự soạn", dùng benchmark đã công bố (đã kiểm nơi công bố trên ACL Anthology). Tiêu chí: hội nghị/tạp chí có phản biện; công khai cho nghiên cứu; có vị trí bằng chứng (để tính Recall@k, MRR); tài liệu đủ dài để phải cắt. Chunking: **Qasper** (NAACL 2021, bài báo có mục, EN), **ConditionalQA** (ACL 2022, trang chính sách có tiêu đề, EN), **Natural Questions** (TACL 2019, Wikipedia, EN), **UIT-ViQuAD** (COLING 2020, Wikipedia, VI); TechQA (ACL 2020) tùy chọn. Index: **BEIR-FiQA** (~57.000 tài liệu). So cặp: Qasper/ConditionalQA với NQ → khi nào nên cắt theo cấu trúc; NQ với ViQuAD → tiếng Việt có đổi kết luận không | `plan-khoa.md` (sẽ cập nhật mục 3) | Xem phát hiện F (ảnh hưởng TASK-81) |
| **TASK-77** bảo mật | ⏳ Đã có `RagTenantIsolationTest`, `RagPromptInjectionTest`. **Chưa sửa PWNED, chưa đo trước/sau** | — | — |
| Ngoài kế hoạch | ✅ (1) Chat hiển thị Markdown (in đậm, danh sách, code, bảng) thay vì ký tự thô; không bật HTML thô, chặn ảnh, link mở tab mới `noopener`. (2) Dọn dữ liệu test + tạo dữ liệu demo có tên tiếng Việt để chụp hình báo cáo (qua API thật, không gọi LLM; sao lưu DB trước khi dọn) | `frontend/components/chat-markdown.tsx`, `chat/page.tsx`, `globals.css`, `package.json` (+`react-markdown`, `remark-gfm`) | Mở chat một agent, xem câu trả lời |

## Kết quả chạy thử index (vector TỔNG HỢP — chỉ để kiểm script, KHÔNG dùng cho báo cáo)

50.000 vector 1536 chiều, 50 agent (kích thước lệch kiểu Zipf), 200 câu hỏi, k = 10, HNSW `m=16`,
`ef_construction=64`, IVFFlat `lists=50`.

| Cách | Tham số | Recall@10 toàn bảng | Độ trễ TB | Tạo index | Dung lượng |
|---|---|---|---|---|---|
| Không index | – | 1.000 | 204 ms | – | – |
| IVFFlat | probes = 1 | 1.000 | 1.7 ms | 3.0 s | 391 MB |
| HNSW | ef_search = 40 (mặc định) | 0.986 | 0.5 ms | 28.7 s | 391 MB |
| HNSW | ef_search = 160 | 0.998 | 0.8 ms | | |

IVFFlat đạt 1.000 ngay cả `probes=1` là **do dữ liệu tổng hợp chia cụm quá rõ** — không thực tế, nên số
chính thức phải chạy trên embedding thật (FiQA).

## Phát hiện quan trọng

**A. ⚠️ HNSW + `WHERE agent_id` trả THIẾU đoạn nếu không bật iterative scan.** HNSW lấy các vector gần
nhất trên toàn bảng trước rồi mới lọc theo agent. Chạy thử (`ef_search=20`): **28% câu hỏi nhận ít hơn 10
đoạn**, recall 0.858 → người dùng hỏi agent A nhưng hệ thống tìm thiếu tài liệu của A. Bật
`SET hnsw.iterative_scan = relaxed_order` (pgvector ≥ 0.8): **0% thiếu, recall 0.990**, độ trễ không đổi.
→ **Nếu chọn HNSW thì truy vấn `findNearestChunks` bắt buộc bật tùy chọn này** (Khoa làm cùng V5).

**B. Agent nhỏ thì index vector gần như không được dùng.** Với truy vấn lọc theo agent, planner chỉ dùng
index vector cho 29–42% câu hỏi (agent lớn); agent nhỏ dùng btree `agent_id` + sắp xếp chính xác (recall 1,
~19 ms trên bảng 50.000 dòng). Agent Conduit hiện chỉ vài trăm đoạn → **quét chính xác theo agent đang
đủ**; index chỉ có ý nghĩa khi có agent rất lớn. Sẽ xác nhận lại trên FiQA.

**C. Index là cấu hình CẤP HỆ THỐNG, không phải theo agent.** pgvector tạo index cho cả cột `embedding`,
không tạo riêng từng agent được. → Form cấu hình của creator (TASK-79) **không nên có lựa chọn index**; chỉ
cần vector/graph, chunking, top_k. Index chọn một lần sau khi có kết quả đánh giá.

**D. Đổi chunking thì phải nạp lại tài liệu** (cắt lại + embedding lại). Form nên có nút "nạp lại" hoặc
cảnh báo khi creator đổi cách chunking.

**E. Hành vi mặc định của `/chunk-embed` thay đổi nhẹ.** Mặc định giờ dùng `chunk_fixed` mới thay
`ingest.chunk_text` cũ: giữ xuống dòng và cắt sát `size` hơn, nên đoạn hơi khác bản cũ. Agent đã nạp trước
đó không bị ảnh hưởng (chỉ khác khi nạp lại). `chunk_text` cũ để nguyên (test cũ còn dùng).

**F. Dữ liệu đánh giá đổi so với `tasks.md` → ảnh hưởng TASK-81.** TASK-81 ghi "dùng lại bộ ~20 câu hỏi
của TASK-76", nhưng TASK-76 giờ dùng benchmark (mục trên). Đề xuất: vector và graph dùng chung **một tập
con 20–30 câu** (Qasper hoặc ConditionalQA), vì trích quan hệ cho graph tốn `gpt-4o-mini`. Hùng chọn bộ,
Khoa xuất sẵn tập con cùng định dạng.

**G. Chunker ngữ nghĩa: phân vị 95 có thể làm nó gần giống đệ quy.** Phân vị 95 ≈ cứ ~20 câu mới có 1 chỗ
cắt theo chủ đề (~2.000 ký tự) > `max_size` 1.000 → phần lớn chỗ cắt do giới hạn kích thước. Đề xuất chốt
phân vị (vd 90) trong **bản đăng ký trước**, trước khi chạy đánh giá.

**H. Môi trường máy Khoa (để Hùng biết nếu gặp):** cổng 5432 từng bị PostgreSQL đi kèm Odoo chiếm (đã
chuyển service đó sang khởi động thủ công); cổng 8000 có thể bị dự án khác chiếm — `/health` vẫn trả ok
nên dễ nhầm là ai-service của Conduit.

## Cần Hùng

1. **V4 / `rag_config`**: lưu ở bảng nào, cột gì, kiểu gì (jsonb?), JSON có dạng `{kb_type, chunking:
   {method, params}, index: {method}, top_k}` không. **Đang chặn** phần "chọn được qua `rag_config`" của
   TASK-75 và V5 của Khoa.
2. **Chốt hợp đồng mục 7 `tasks.md`** (vẫn "chưa chốt"). Đề xuất của Khoa:
   - `Chunk = {index, text, start_char, end_char, method, metadata}` + `source` (tên file) ở cấp ngoài;
   - gọi chunker: multipart `file` + `method` (`fixed` | `recursive` | `structure` | `semantic`) + `params`
     (chuỗi JSON). Mặc định: fixed/recursive `{size: 1000, overlap: 150}`; structure thêm `min_size: 200`;
     semantic `{breakpoint_percentile: 95, buffer: 1, min_size: 200, max_size: 1000}` (tốn phí embedding
     lúc cắt).
3. **TASK-81**: chọn bộ dữ liệu cho tập con chung (phát hiện F).
4. **Duyệt chi phí** (> 10 lượt): TASK-76 embedding `text-embedding-3-small` (~200–300 câu hỏi mỗi bộ × 4
   cách cắt + FiQA ~57.000 tài liệu cho index; gộp lô, cache) ước **vài chục đến hơn 100 lượt, < $1**;
   TASK-77 ~80 lượt `gpt-4o-mini`, ~$0,02–0,05. Khoa gửi **bản đăng ký trước** (bộ dữ liệu, cỡ mẫu, tham
   số, số lượt, chi phí) trước khi chạy.
5. **Xác nhận để Khoa commit + push** phần chunking, endpoint, script index lên `dangkhoa`.
6. **Review chéo**: TASK-78 → 81 push chưa? Push rồi báo để Khoa review.

## Chi phí API

| Việc | Lượt có phí | Chi phí |
|---|---|---|
| Unit test chunking + endpoint (embedding giả) | 0 | $0 |
| Gọi thử `/chunk` trên service thật (fixed, recursive, structure — không embedding) | 0 | $0 |
| Chạy thử đánh giá index (vector tổng hợp) | 0 | $0 |
| **Tổng** | **0** | **$0** |
