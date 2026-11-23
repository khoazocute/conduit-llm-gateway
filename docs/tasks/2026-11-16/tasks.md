# 2026-11-20 → 2026-11-27 — RAG cấu hình được (D21) + bản nháp báo cáo

Viết ngay sau họp GVHD tối 20/11 (`docs/meetings/2026-11-20.md`). Đề tài đổi sang **3 đóng góp** (D21,
`docs/roadmap.md` mục 4):
1. Mô hình routing và đánh giá routing ⇒ chọn model — **đã xong, giữ nguyên** (phần đánh giá 3 proxy).
2. **Nền tảng RAG cấu hình được trên giao diện** — việc chính tuần này.
3. Ứng dụng demo (Conduit) triển khai 1 và 2.

**Hạn bản nháp vẫn là 27/11.** RAG làm ở mức MVP theo thứ tự ưu tiên:
**(a) chọn vector DB hoặc graph DB → (b) chọn phương pháp chunking hoặc index → (c) cấu hình pipeline.**
(a) và (b) **bắt buộc**; (c) làm nếu kịp. Trực quan hóa vector/đồ thị, bộ nhớ ngắn/dài hạn, pipeline kéo thả:
sau 27/11.

**Nguyên tắc chia việc:** chia đều, **mỗi người sở hữu trọn một nhánh**, chỉ gặp nhau ở **hợp đồng chung**
(mục 2) chốt ngày 21/11. Sau đó làm độc lập, không sửa file của nhau.

---

## 1. Thay đổi so với `docs/tasks/2026-11-09/tasks.md`

| Việc cũ | Bây giờ |
|---|---|
| TASK-57a/57b, TASK-58 (RAG cơ bản, Should-have, cắt nếu chưa xong 14/11) | Thay bằng TASK-74 → 80 dưới đây (RAG là đóng góp chính) |
| TASK-73 trang admin hiển thị routing (Should-have) | **Dời sau 27/11**, nhường sức cho RAG |
| TASK-62b/62c phần viết | Giữ, cộng thêm phần viết RAG ở mục 5 |
| Chương báo cáo trình bày đóng góp theo D20 | Trình bày **3 đóng góp theo D21** (Hùng: 1.5 phối hợp Khoa, 6.2) |

---

## 2. Ngày 21/11 — làm chung (≤ nửa ngày): chốt hợp đồng

1. **Khoa push bản RAG đang chạy trên máy** lên `dangkhoa` (hiện chưa có trên GitHub), kể cả ví dụ "PWNED".
2. **Chốt nơi đặt engine RAG.** Đề xuất mặc định: `ai-service/` (Python FastAPI: có sẵn thư viện chunking,
   driver Neo4j, pgvector); backend gọi qua adapter HTTP `RagClient` theo đúng mẫu `ProxyChatClient` /
   `HttpProxyChatClient`. Nếu bản của Khoa đã viết bằng Java và chạy tốt thì giữ Java, sửa lại mục này.
3. **Chốt hợp đồng** (ghi vào cuối file này, mục 7, sau khi thống nhất):
   - `Chunk { text, index, source, metadata }`: đầu ra của chunker.
   - `chunk(document, method, params) -> [Chunk]`: hàm chunker (Khoa viết, Hùng gọi cho đường graph).
   - `Retriever.retrieve(agent_id, query, k) -> [{ text, score, source }]`: chung cho vector và graph.
   - Cấu hình RAG của agent (JSON): `{ kb_type: "vector"|"graph", chunking: { method, params },
     index: { method }, top_k, pipeline: [ ... ] }`.
4. **Thứ tự migration Flyway** để không đụng nhau: **Hùng V4** (cấu hình RAG trên `agents` /
   `knowledge_bases`), **Khoa V5** (cột chunk/index trên `kb_chunks`).

---

## 3. Việc của Khoa — nhánh "nạp tài liệu, chunking, vector"

| Task | Nội dung | Ưu tiên | Đạt khi |
|---|---|---|---|
| **TASK-74** | Đường **vector** trọn gói: tải tài liệu → chunk → embed (`text-embedding-3-small`, khai báo trong `proxy-configs/litellm/config.yaml`) → `kb_chunks` (pgvector) → truy hồi lọc theo `agent_id` | (a) | Một tài liệu nhỏ nạp được, truy hồi top-k đúng agent |
| **TASK-75** | **≥ 3 phương pháp chunking**: kích thước cố định có overlap; đệ quy theo đoạn/câu; ngữ nghĩa. Và **phương pháp index** pgvector: không index (quét toàn bộ), IVFFlat, HNSW | (b) | Chọn được qua `rag_config`; có unit test cho từng chunker |
| **TASK-76** | **Đánh giá "chọn chunking tối ưu"**: ~20 câu hỏi có đáp án trên 1 tài liệu; so 3 chunking × index bằng **Recall@k, MRR, độ trễ truy hồi** (chỉ số chuẩn nhóm RAG, xem `experiment-results.md` mục 16.3) | (b) | Bảng kết quả + kết luận chunking nào tốt hơn, vì sao |
| **TASK-77** | Test bảo mật bắt buộc (CLAUDE.md mục 7): creator A không truy hồi được `kb_chunks` của B; ~20 tài liệu chèn lệnh, đo trước/sau biện pháp sửa lỗi PWNED | bắt buộc | 2 nhóm test pass, có số liệu trước/sau |

---

## 4. Việc của Hùng — nhánh "graph, cấu hình, pipeline, tích hợp"

| Task | Nội dung | Ưu tiên | Đạt khi |
|---|---|---|---|
| **TASK-78** | Đường **graph** trọn gói: chunk (gọi chunker của Khoa) → trích thực thể/quan hệ bằng `gpt-4o-mini` → **Neo4j** (thêm service vào `docker-compose.yml`) → truy hồi theo thực thể + lân cận | (a) | Cùng tài liệu nạp được dạng đồ thị, truy hồi trả ngữ cảnh đúng agent |
| **TASK-79** | **Cấu hình RAG trên giao diện**: lưu `rag_config` theo agent (Flyway V4), form creator chọn vector/graph + chunking + index; ABAC: chỉ chủ agent/admin sửa được; `ChatService` chèn ngữ cảnh truy hồi, đánh dấu "ngữ cảnh tham khảo" | (a)(b) | Creator đổi cấu hình trên UI, chat dùng đúng cấu hình; test ABAC pass; `e2e_test.sh` vẫn pass |
| **TASK-80** | **Pipeline cấu hình được** (bản tuyến tính): danh sách bước có thứ tự, bật/tắt (phân tích câu hỏi → truy hồi → ghép ngữ cảnh → gọi LLM). Kéo thả: sau 27/11 | (c) | Bật/tắt bước làm đổi hành vi chat, có test |
| **TASK-81** | **Đánh giá vector so với graph**: dùng lại bộ ~20 câu hỏi của TASK-76; so chất lượng trả lời và chi phí nạp | (a) | Bảng kết quả + nhận xét |

---

## 5. Phần viết báo cáo thêm cho RAG

| Người | Mục |
|---|---|
| Khoa | Lý thuyết chunking, index, embedding (3.1.4); thiết kế đường vector (4.4.4); kết quả chunking (5.4.2) |
| Hùng | Lý thuyết graph RAG và pipeline; thiết kế tổng thể "RAG cấu hình được"; kết quả vector so với graph; đóng góp theo D21 (1.5 cùng Khoa, 6.2) |

Số mục chính xác chỉnh lại theo dàn ý trong Google Doc khi thêm phần RAG.

---

## 6. Lịch, điểm cắt, chi phí

| Ngày | Việc |
|---|---|
| 21/11 | Mục 2 (làm chung) |
| 22–24/11 | Mỗi người làm nhánh mình (TASK-74 → 81) |
| **24/11** | **Điểm cắt:** nhánh nào chưa chạy được thì bản nháp ghi thiết kế + trạng thái thật, **không bịa kết quả**. Graph là nhánh rủi ro nhất; nếu chưa chạy, bản nháp vẫn có (a) nhờ đường vector + thiết kế graph |
| 25/11 | Chạy đánh giá (TASK-76, 81), ghép hai nhánh |
| 24–26/11 | Viết phần RAG, đọc chéo |
| 26/11 | Merge vào `main`; chạy `e2e_test.sh` + test RAG |
| **27/11** | **Nộp bản nháp** |

**Chi phí (D1):** embedding và trích quan hệ cho đồ thị dùng model rẻ (`text-embedding-3-small`,
`gpt-4o-mini`). Đợt nào **> 10 lượt gọi có phí** (trích quan hệ cho cả tài liệu, chạy bộ đánh giá) thì nêu số
lượt + ước tính, **Hùng duyệt trước khi chạy**.

**Review chéo:** Hùng review TASK-74 → 77, Khoa review TASK-78 → 81 (đọc `log-*.md` + chạy lại test), ghi
vào cuối `log-*.md` của người kia như các tuần trước.

---

## 7. Hợp đồng đã chốt (điền ngày 21/11)

_(chưa chốt)_

---

## 8. Checklist

- [ ] Khoa push RAG đang có — 21/11
- [ ] Hợp đồng chung chốt, ghi mục 7 — 21/11
- [ ] TASK-74 vector, TASK-78 graph chạy được — 24/11
- [ ] TASK-75 chunking + index, TASK-79 cấu hình trên UI — 24/11
- [ ] TASK-77 test bảo mật pass — 25/11
- [ ] TASK-76, TASK-81 đánh giá xong — 25/11
- [ ] TASK-80 pipeline (nếu kịp) — 25/11
- [ ] Phần viết RAG + 3 đóng góp theo D21 — 26/11
- [ ] Merge `main`, test pass — 26/11
- [ ] **Nộp bản nháp — 27/11**
