# H2 — Bằng chứng verify Portkey conditional routing (2026-09-29)

Gọi trực tiếp `POST /v1/chat/completions`, config gửi qua header `x-portkey-config` (JSON đã
compact, key thật đã thay thế client-side — xem phát hiện quan trọng bên dưới).

| Lượt | `model` gửi lên | Kết quả mong đợi | Model thật trả về | Đạt |
|---|---|---|---|---|
| 1 | `gpt-4o-mini` | khớp condition, target `gpt-4o-mini` | `gpt-4o-mini-2024-07-18` | ✅ |
| 2 | `claude-sonnet` | khớp condition, target `claude-sonnet` | `claude-sonnet-5` | ✅ |
| 3 | `nonsense-alias` (không khớp condition nào) | rơi về `default: gpt-4o-mini` | `gpt-4o-mini-2024-07-18` | ✅ |

**Kết luận:** conditional routing hoạt động đúng — khớp `params.model` theo alias, resolve đúng
model thật qua `override_params`, và fallback `default` đúng khi không khớp condition nào.

## Phát hiện quan trọng — Portkey OSS không tự thay `$VAR` trong `api_key`

Khác với LiteLLM (`os.environ/VAR` được chính LiteLLM đọc lúc khởi động từ file `.env` nạp vào
container), Portkey OSS nhận config qua **header của từng request**, không đọc `.env` cho phần này
— gửi `"api_key": "$OPENAI_API_KEY"` nguyên văn sẽ bị gửi thẳng lên OpenAI như 1 key thật (sai,
401 "$OPENAI_***_KEY"). **Bên gửi request (runner Phase D/E) phải tự thay `$VAR` bằng giá trị thật
từ `.env` trước khi đưa vào header** — không phải Portkey tự làm. Đây là điểm khác biệt quan trọng
so với LiteLLM khi viết `run_experiment.py`.

## ⚠️ Lệch chính sách chi phí (tự nhận, không giấu)

Lượt 2 gọi thật tới **Claude Sonnet 5 (tầng đắt)** để xác nhận alias `claude-sonnet` resolve đúng
— đáng lẽ phải chọn alias tầng rẻ (VD `claude-haiku`) để verify logic mapping mà không chạm tầng
đắt, và đáng lẽ phải dừng xin xác nhận trước khi gọi model tầng đắt (CLAUDE.md mục 2). Chi phí thực
tế không đáng kể (1 lượt, `max_tokens=8`), nhưng là sai quy trình, ghi lại rõ ràng thay vì bỏ qua.
