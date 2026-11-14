# Log tuần 09/11 → hạn nộp bản nháp 27/11 — Khoa

Theo `docs/tasks/2026-11-09/tasks.md`. Nhận việc 14/11 (tin nhắn giao việc gửi trễ — tuần 02/11 không
được giao thực tế), nên TASK-60/70 làm sau hạn 11/11. Pull `main` (60c8075) vào `dangkhoa` ngày 14/11.

## Việc đã làm

| Task | Kết quả | File | Hùng review gì |
|---|---|---|---|
| **TASK-60** kiểm lại fallback | ✅ **Đề xuất đóng** — 2 yêu cầu trong `CLAUDE.md` đều đạt về cấu hình; nhánh Gemini đã được LiteLLM gọi tới thật nhưng Gemini bản miễn phí trả 503 (chi tiết dưới) | không sửa code | Đồng ý đóng hay không |
| **TASK-57a** RAG phần 1: nạp tài liệu | ✅ **Đạt điểm cắt 14/11** — tải 1 file TXT nhỏ thật → **2 đoạn** trong `kb_chunks`, cả 2 **đúng `agent_id`**, `vector(1536)`; file gốc nằm trong kho S3. Chi tiết dưới. Backend `./mvnw test` **104/104** (+14), ai-service **17/17** | xem "TASK-57a — chi tiết" | Thiết kế, 3 điểm cần chốt |
| **TASK-70** ghi `usage_logs` khi trừ credit bỏ cuộc | ✅ Quá 8 lần xung đột ví → `ChatService.recordAbandonedBillingTurn` ghi, trong transaction riêng: tin nhắn (không nội dung), `usage_logs` **`status=error` kèm `cost_upstream` thật**, `revenue_credit = 0`, và `routing_decisions` (CLAUDE.md mục 2: mọi lượt gọi phải ghi). **Không trừ ví.** Lỗi SSE trả cho người dùng giữ nguyên. Không sửa `recordSuccessfulTurn`; hàm phụ `upstreamCost` dùng đúng cách tra giá theo từng dòng `model_pricing`. **Test:** giả lập 8 lần xung đột liên tiếp → 8 lần thử trừ, không lần nào thành công; đúng 1 dòng `usage_logs` (`error`, cost 0,000045 cho 100 vào + 50 ra `gpt-4o-mini`, revenue 0) và 1 dòng `routing_decisions`. `./mvnw test` **90/90** | `ChatService.java`, `ChatServiceTest.java` | Đọc diff |

### TASK-60 — chi tiết

**Yêu cầu 1 — "Cross-provider fallback bắt buộc qua Provider Adapter" (CLAUDE.md mục 5): ĐẠT.**
- `pom.xml` không có SDK nhà cung cấp nào; code không gọi thẳng `api.openai.com` / `api.anthropic.com`
  / Gemini.
- Chỉ `ChatService` gọi LLM, qua `ProxyChatClient` → `HttpProxyChatClient` (lớp adapter). Việc chuyển
  nhà cung cấp diễn ra trong proxy, phía sau adapter; adapter ghi đúng model thật đã trả lời
  (`x-litellm-model-group` sau fallback, TASK-51).

**Yêu cầu 2 — "Fallback sang Gemini" (Should-have): ĐẠT về cấu hình, nhưng Gemini miễn phí không ổn định.**
- Cấu hình: `fallbacks: conduit-pool → [claude-haiku, gemini-flash]` + `retry_policy` (D16).
- Trước đây **chưa từng có bằng chứng nhánh Gemini chạy**: phép thử sự cố 27/10 phục hồi 15/15 đều qua
  `claude-haiku`. Gemini chỉ được dùng khi **cả OpenAI lẫn Anthropic** cùng lỗi.
- **Kiểm 14/11** (container `litellm` mang key OpenAI + Anthropic không hợp lệ, file override tạm,
  đã khôi phục key thật ngay sau): gửi `conduit-pool` → log LiteLLM ghi
  `Available Model Group Fallbacks=['claude-haiku', 'gemini-flash']`, `claude-haiku` lỗi 401, rồi
  `Error doing the fallback: GeminiException 503` → **LiteLLM CÓ đi tới Gemini**, nhưng Gemini trả
  **503 "This model is currently experiencing high demand"**; người dùng nhận lại lỗi 401 gốc của OpenAI.
- Gọi thẳng alias `gemini-flash` cùng lúc: một lần trả rỗng với `max_tokens: 8` (nghi Gemini bản mới
  cũng tiêu token cho bước suy nghĩ như Sonnet — chưa kiểm), một lần **503 sau 61,7 s** (vượt ngân
  sách 45 s của backend).
- **Kết luận:** cơ chế fallback sang Gemini có và hoạt động; độ sẵn sàng của Gemini bị giới hạn bởi key
  miễn phí — đúng rủi ro đã ghi trong `roadmap.md` mục 7 ("Gemini bản miễn phí quá tải"). Không phải lỗi
  cấu hình hay code → **không sửa gì**. Nếu cần Gemini là tầng dự phòng thật sự thì phải dùng key trả
  phí (quyết định chi phí, D1). Ghi vào phần giới hạn của báo cáo.
- Chi phí: 4 lượt gọi (2 qua `conduit-pool` bị lỗi xác thực, 2 gọi thẳng Gemini bị 503/rỗng) — ~$0.

### TASK-57a — chi tiết

Làm theo đúng tài liệu: endpoint theo `docs/openapi.json` (backend, JWT + ABAC), xử lý RAG ở
**ai-service Python + FastAPI**, kho file **S3-compatible** (CLAUDE.md mục 3), embedding **qua lớp
proxy** (CLAUDE.md mục 5).

**Luồng:**
```
POST /agents/{agentId}/knowledge-base (multipart "file")
  backend: chủ agent? (403 nếu không) → .pdf/.txt, ≤ 5 MB (400) → lưu file vào kho S3
         → knowledge_bases(status=processing) → trả 202
  chạy nền (2 luồng, hàng đợi 20):
         → ai-service POST /chunk-embed: đọc chữ → chia đoạn 1000 ký tự, gối 150, cắt ở ranh giới từ
             → LiteLLM /v1/embeddings (text-embedding-3-small), MỘT request cho cả file
         → backend ghi kb_chunks + đổi ready trong MỘT transaction; lỗi bất kỳ → failed
GET /agents/{agentId}/knowledge-base — chỉ chủ agent (403 nếu không)
```
- `kb_chunks` chưa có entity (cột `vector` cần thư viện riêng) → ghi bằng native query có `@Param`
  (CLAUDE.md mục 7), vector truyền dạng chuỗi rồi `CAST(... AS vector)`. **`agent_id` của đoạn lấy
  từ chính dòng `knowledge_bases` trong câu INSERT**, không nhận từ bên gọi → không thể ghi nhầm agent.
- ai-service chỉ nhận lệnh từ backend (header `X-Internal-Token`), không có quyền vào DB.

**Kiểm 14/11 với file thật** (`conduit-faq.txt`, 1.804 ký tự tiếng Việt):

| Bước | Kết quả |
|---|---|
| Creator B tải file vào agent của A | **403** |
| Creator B xem danh sách file của agent A | **403** |
| A tải `.docx` | **400** `Only .pdf and .txt files are supported` |
| A tải `.txt` | **202** `processing` → khoảng 1 s sau **`ready`** |
| `kb_chunks` | **2 dòng** (index 0, 1; dài 997 và 945 ký tự, có đoạn gối đầu), `agent_id` = agent của A, `vector_dims = 1536`, `source_file = conduit-faq.txt` |
| Kho S3 (SeaweedFS) | `s3://conduit-kb/agents/<agent>/<uuid>/conduit-faq.txt`, 2.313 byte |
| Chi phí | **1 lượt** embedding, 827 token × $0,02/1M = **≈ $0,000017** |

Dữ liệu thử còn trong DB local: 2 tài khoản `rag57a-*@conduit.test`, 1 agent, 1 file, 2 đoạn.

**Test** (không gọi API có phí):
- `KnowledgeBaseServiceTest` (8): ABAC upload/list, file sai đuôi/rỗng/quá lớn bị chặn **trước khi
  lưu**, tên file bỏ đường dẫn, hàng đợi đầy → `failed`.
- `KnowledgeBaseIngestionServiceTest` (5): ghi đúng thứ tự rồi `ready`; ai-service lỗi, sai số chiều,
  kết quả rỗng → `failed`, không ghi đoạn nào; lỗi giữa chừng → rollback.
- `KnowledgeBaseChunkPersistenceTest` (1, **DB thật**): INSERT + CAST vector chạy được; đoạn mang
  `agent_id` của file; lọc theo agent B ra 0 đoạn.
- ai-service `tests/test_ingest.py` (17): đọc TXT/PDF, chia đoạn không mất/không cắt đôi từ, embedding
  một request + khôi phục thứ tự, sai token → 401 và không gọi embedding.

**⚠️ Điểm bất thường / cần Hùng chốt:**
1. **MinIO không còn dùng được:** `docker pull minio/minio` báo "repository does not exist" (MinIO đã
   ngừng phát hành image bản cộng đồng). Tài liệu chỉ ghi "S3-compatible" → dùng **SeaweedFS**
   (`chrislusf/seaweedfs:4.51`, ghim phiên bản), service `seaweedfs` mới trong `docker-compose.yml`,
   cổng 8333. Backend dùng AWS SDK S3 chuẩn → đổi sang S3 thật khi deploy chỉ cần biến môi trường.
   Tài khoản dev (`storage/seaweedfs-s3.json`) commit như mật khẩu Postgres dev — **không dùng khi deploy**.
2. **Sửa `proxy-configs/litellm/config.yaml`:** thêm alias `text-embedding-3-small` (model_name riêng,
   không nằm trong `conduit-pool` → **không ảnh hưởng routing/fallback của thí nghiệm**). Đã restart
   container `litellm` máy Khoa. Máy Hùng cần restart LiteLLM thì mới có alias này.
3. **Chi phí embedding chỉ ghi log**, chưa vào `usage_logs` (bảng đó gắn với tin nhắn chat). Có cần
   ghi vào đâu để đối soát D1 không?
- Chưa làm (ngoài 57a): `DELETE /knowledge-base/{kbId}`; file đang `processing` mà backend tắt thì
  kẹt ở `processing` (không có cơ chế chạy lại); PDF scan không OCR; ai-service chưa có trong
  docker-compose (chạy bằng `uvicorn`, xem `ai-service/README.md`).

**Cách chạy lại:** `docker compose up -d seaweedfs` + restart `litellm` → ai-service (`uvicorn`,
cổng 8000, cần `LITELLM_MASTER_KEY`) → backend → `POST /agents/{id}/knowledge-base`.

## Cần bàn / chốt

1. **TASK-60:** Hùng đồng ý đóng với kết luận trên không?
2. **TASK-57a:** 3 điểm ở mục "Điểm bất thường / cần Hùng chốt" (SeaweedFS thay MinIO, alias
   embedding trong config LiteLLM, ghi chi phí embedding). RAG đạt điểm cắt → **giữ trong bản nháp**?

## Còn thiếu

- **TASK-57b** (truy hồi top-k + đưa vào chat làm "ngữ cảnh tham khảo", hạn 19/11) và **TASK-58**
  (2 test bảo mật, hạn 20/11).
- **TASK-62c báo cáo** — đợt 1 (chương 1–2) hạn 16/11. Khoa chưa đọc/sửa được Google Doc từ máy
  (connector Google Drive chưa cấp quyền); bản draft cũ còn trong lịch sử git (commit `0c08bc9`).
- **TASK-62a dàn ý chung** (hạn 11/11) — chưa thấy dấu vết trong repo, cần xác nhận với Hùng.
