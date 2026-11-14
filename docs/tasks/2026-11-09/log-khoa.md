# Log tuần 09/11 → hạn nộp bản nháp 27/11 — Khoa

Theo `docs/tasks/2026-11-09/tasks.md`. Nhận việc 14/11 (tin nhắn giao việc gửi trễ — tuần 02/11 không
được giao thực tế), nên TASK-60/70 làm sau hạn 11/11. Pull `main` (60c8075) vào `dangkhoa` ngày 14/11.

## Việc đã làm

| Task | Kết quả | File | Hùng review gì |
|---|---|---|---|
| **TASK-60** kiểm lại fallback | ✅ **Đề xuất đóng** — 2 yêu cầu trong `CLAUDE.md` đều đạt về cấu hình; nhánh Gemini đã được LiteLLM gọi tới thật nhưng Gemini bản miễn phí trả 503 (chi tiết dưới) | không sửa code | Đồng ý đóng hay không |
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

## Cần bàn / chốt

1. **TASK-60:** Hùng đồng ý đóng với kết luận trên không?
2. **RAG (TASK-57a), điểm cắt 14/11:** chưa làm — xem mục "Còn thiếu".

## Còn thiếu

- **TASK-57a RAG phần 1** — điểm cắt hôm nay 14/11, chưa bắt đầu. Chờ quyết định.
- **TASK-62c báo cáo** — đợt 1 (chương 1–2) hạn 16/11. Khoa chưa đọc/sửa được Google Doc từ máy
  (connector Google Drive chưa cấp quyền); bản draft cũ còn trong lịch sử git (commit `0c08bc9`).
- **TASK-62a dàn ý chung** (hạn 11/11) — chưa thấy dấu vết trong repo, cần xác nhận với Hùng.
