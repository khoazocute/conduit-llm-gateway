# ai-service

FastAPI cho RAG (Should-have). TASK-57a: nạp tài liệu.

## Endpoint

- `GET /health` → `{"status": "ok"}`
- `POST /chunk-embed` (multipart, trường `file`, header `X-Internal-Token`): đọc PDF/TXT → chia đoạn
  → embedding → trả `{model, prompt_tokens, chunks: [{index, text, embedding[1536]}]}`.
  **Chỉ backend gọi.** Service không có quyền vào DB: backend kiểm ABAC, lưu file vào kho S3,
  rồi tự ghi `kb_chunks`.

Embedding gọi **qua LiteLLM** (`/v1/embeddings`, alias `text-embedding-3-small` trong
`proxy-configs/litellm/config.yaml`), không gọi thẳng OpenAI (CLAUDE.md mục 5). Tất cả đoạn của một
file đi trong **một** request → một file = một lượt gọi có phí.

## Chạy

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # Windows; Linux/macOS: .venv/bin/python
# Cần LITELLM_MASTER_KEY (lấy từ ../.env) và LiteLLM chạy ở localhost:4000
.venv/Scripts/python -m uvicorn main:app --port 8000
```

| Biến môi trường | Mặc định | Ghi chú |
|---|---|---|
| `AI_SERVICE_TOKEN` | `dev-only-ai-service-token` | Phải trùng `app.ai-service.token` của backend |
| `LITELLM_BASE_URL` | `http://localhost:4000/v1` | |
| `LITELLM_MASTER_KEY` | `sk-1234` | |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 1536 chiều, khớp `kb_chunks.embedding` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `150` | Ký tự; cắt ở ranh giới từ |
| `MAX_CHUNKS` | `200` | File sinh nhiều đoạn hơn → 422, không gọi embedding |
| `MAX_FILE_BYTES` | `5242880` | 5 MB |

PDF scan (chỉ có ảnh, không có lớp chữ) → 422 "No extractable text". Không làm OCR.

## Test (không gọi API thật)

```bash
.venv/Scripts/python -m unittest discover -s tests -t .
```
