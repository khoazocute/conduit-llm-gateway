# Log tuần 28/09 – 04/10/2026 — Hùng

Điền dần trong tuần, mỗi mục việc xong thì thêm 1 dòng vào bảng, không cần viết văn xuôi dài nếu
không có gì đặc biệt. Commit kèm code, không paste vào chat — Khoa tự đọc qua `git pull`.

## Việc đã làm

| Việc | Kết quả | File/commit | Khoa cần làm |
|---|---|---|---|
| H4 — verify `decision_rule.py` | ✅ 4 hàm `compute_*` implement xong, 4 nhánh luật quyết định đều có test biết trước kết quả, 16/16 test pass | `experiments/analysis/decision_rule.py`, `experiments/tests/test_decision_rule.py` | Đọc code, thử nghĩ 1 nhánh chưa test (theo bảng review chéo) |
| H1 — LiteLLM routing thật | ✅ alias `conduit-pool` + `cost-based-routing` + D7 (`num_retries=2`/`timeout=45`). 10/10 lượt chọn đúng `gpt-4o-mini` sau khi khai giá tường minh (ban đầu có lúc chọn nhầm gemini-flash — bảng giá nội bộ LiteLLM không đúng cho model này) | `proxy-configs/litellm/config.yaml`, `docs/litellm-routing-notes.md`, `experiments/results/h1-litellm-routing-2026-09-29/` | Dựng lại trên máy Khoa, thử 1 lượt (bảng review chéo) |

## Phát hiện quan trọng

1. **LiteLLM trả model thật đã chọn ở header `x-litellm-model-id`, không phải trong JSON body**
   (`model` trong body luôn là tên nhóm, VD `"conduit-pool"`) — giống vấn đề Khoa gặp với Bifrost
   tuần trước (`extra_fields.routing_info`). Khi nối `default-model` thật vào backend (H3), phải
   đọc header này để `MessageResponse.model_used` đúng, không đọc `model` trong body.
2. **Bảng giá nội bộ của LiteLLM không đúng cho `gemini/gemini-flash-latest`** — `cost-based-routing`
   có lúc chọn nhầm gemini-flash dù đắt hơn gpt-4o-mini gần 10 lần. Phải khai tường minh
   `input_cost_per_token`/`output_cost_per_token` (dùng đúng số ở `docs/model-pricing-sources.md`)
   mới ra quyết định đúng. Đáng lưu ý cho báo cáo: nếu không phát hiện, kết quả Phase E sẽ sai mà
   không biết vì sao.

## Cần bàn / chốt cùng nhau

_(trống)_

## Còn thiếu / chưa xác nhận được

_(trống)_
