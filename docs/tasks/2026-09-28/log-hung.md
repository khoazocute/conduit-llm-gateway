# Log tuần 28/09 – 04/10/2026 — Hùng

Điền dần trong tuần, mỗi mục việc xong thì thêm 1 dòng vào bảng, không cần viết văn xuôi dài nếu
không có gì đặc biệt. Commit kèm code, không paste vào chat — Khoa tự đọc qua `git pull`.

## Việc đã làm

| Việc | Kết quả | File/commit | Khoa cần làm |
|---|---|---|---|
| H4 — verify `decision_rule.py` | ✅ 4 hàm `compute_*` implement xong, 4 nhánh luật quyết định đều có test biết trước kết quả, 16/16 test pass | `experiments/analysis/decision_rule.py`, `experiments/tests/test_decision_rule.py` | Đọc code, thử nghĩ 1 nhánh chưa test (theo bảng review chéo) |
| H1 — LiteLLM routing thật | ✅ alias `conduit-pool` + `cost-based-routing` + D7 (`num_retries=2`/`timeout=45`). 10/10 lượt chọn đúng `gpt-4o-mini` sau khi khai giá tường minh (ban đầu có lúc chọn nhầm gemini-flash — bảng giá nội bộ LiteLLM không đúng cho model này) | `proxy-configs/litellm/config.yaml`, `docs/litellm-routing-notes.md`, `experiments/results/h1-litellm-routing-2026-09-29/` | Dựng lại trên máy Khoa, thử 1 lượt (bảng review chéo) |
| H2 — Portkey routing thật | ✅ `strategy.mode: conditional`, 5 alias khớp `params.model` → đúng target thật, default rơi về `gpt-4o-mini`. 3/3 lượt đúng | `proxy-configs/portkey/config.json`, `docs/portkey-routing-notes.md`, `experiments/results/h2-portkey-routing-2026-09-29/` | Dựng lại trên máy Khoa, thử 1 lượt |
| Merge `main`→`lhung` | ⚠️ phát hiện `lhung` đang thiếu hẳn PR #5 của Khoa (K1-K4) — merge lại trước khi làm H3, không conflict | commit merge | Không cần làm gì, chỉ để biết đã xảy ra |
| H3 — default-model + runner | ✅ `default-model` env-overridable, về `gpt-4o-mini`. Sửa `HttpProxyChatClient` đọc header `x-litellm-model-id` (bug giống Bifrost). Viết lại `run_experiment.py` theo D3 (qua app thật). Verify `--limit 1`: đủ 3 dòng DB, model đúng, chấm đúng | `application.yml`, `HttpProxyChatClient.java`, `run_experiment.py`, `experiments/results/run_litellm_20260929T084350Z.json` | Đọc code runner, thử chạy lại trên máy Khoa |

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
3. **Portkey OSS không tự thay `$VAR` trong `api_key` của config** (khác LiteLLM đọc `os.environ/VAR`
   lúc khởi động) — Portkey nhận config qua header mỗi request, gửi `$OPENAI_API_KEY` nguyên văn sẽ
   bị coi là key thật (401 sai key). Bên gửi request (`run_experiment.py`) phải tự thay `$VAR` bằng
   giá trị thật trước khi đưa vào header `x-portkey-config`.
4. **`lhung` bị thiếu PR #5 của Khoa** (K1-K4: Bifrost, model_pricing, rubric) — nhánh đang làm việc
   dựa trên `main` cũ, không có code Bifrost mới nhất. Đã merge lại trước khi sửa `application.yml`
   (H3), không conflict vì không đụng chung file, nhưng nếu không phát hiện kịp sẽ làm mất code của
   Khoa khi PR merge sau. **Bài học:** merge `main` mới nhất về đầu mỗi phiên làm việc dài, không chỉ
   lúc bắt đầu.
5. **`model_pricing` không tự có trên máy mới** — không phải migration, phải tự chèn tay (xem
   `docs/model-pricing-cleanup.sql` làm mẫu). Máy Hùng đang có đủ 10 dòng khớp
   `docs/model-pricing-sources.md` (tự chèn lúc verify H3).

## Cần bàn / chốt cùng nhau

**Tự nhận lỗi quy trình (không giấu):** lúc test Portkey (H2), 1 trong 3 lượt gọi thật lỡ chạm tầng
đắt (Claude Sonnet 5) thay vì chọn alias tầng rẻ để test — đáng lẽ phải dừng xin xác nhận trước theo
đúng CLAUDE.md mục 2. Chi phí không đáng kể (1 lượt, `max_tokens=8`) nhưng là sai quy trình. Ghi lại
để rút kinh nghiệm cho cả 2 người khi verify routing các tuần sau: luôn chọn alias/tầng rẻ khi chỉ
cần test logic mapping, không cần test đúng model đắt thật.

## Còn thiếu / chưa xác nhận được

- Dry-run 27 lượt (3 prompt × 3 proxy × 3 lần) — chưa chạy, cần xin xác nhận riêng trước.
- Runner (`run_experiment.py`) mới verify qua LiteLLM, chưa thử qua Bifrost/Portkey (cần đổi
  `CHAT_ACTIVE_PROXY` + backend restart, chưa làm trong phiên này).
- `docs/routing-policy.md` (J2) chưa viết — vẫn còn trong danh sách việc chung.
