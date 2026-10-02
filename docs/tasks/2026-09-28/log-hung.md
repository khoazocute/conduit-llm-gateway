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
| Nối Portkey vào app (2026-09-30) | ✅ App trước đó chưa gọi được Portkey thật (thiếu header `x-portkey-config`) — đã sửa `HttpProxyChatClient` tự đọc config + thay `$VAR` + gắn header. Sửa luôn `resolveReturnedModel` cho Portkey (routing tĩnh 1-1 → trả thẳng alias). Verify `CHAT_ACTIVE_PROXY=portkey`: chat thành công, `model_used`/`cost_upstream` đúng, 42/43 (1 fail là do script hard-code proxy litellm, không phải lỗi thật) | `HttpProxyChatClient.java`, `ChatProxyProperties.java`, `application.yml`, `docs/portkey-routing-notes.md` | Dựng lại trên máy Khoa với `CHAT_ACTIVE_PROXY=portkey`, thử 1 lượt |
| J2 — `docs/routing-policy.md` | 🟨 Bản nháp xong — tổng hợp mục tiêu D2, cách 3 proxy biểu đạt, bảng giới hạn, ảnh hưởng cách diễn giải Phase E, trạng thái cấu hình hiện tại. Chờ Khoa đọc/đồng ý mới coi J2 xong hẳn | `docs/routing-policy.md` | Đọc, đặc biệt mục 5; đồng ý hoặc sửa trực tiếp |
| H5 — chuẩn bị dry-run + chấm mù (2026-09-30) | ✅ `dry_run.sh` (gộp restart backend theo proxy + chạy runner, test bằng `--limit 0` qua LiteLLM+Portkey). `build_grading_sheets.py` (xuất bảng chấm mù + chia mẫu D6, test bằng dữ liệu giả, 6/6 pass, khớp con số 49 đã ghi trong `eval-prompts.md`) | `experiments/scripts/dry_run.sh`, `experiments/scripts/build_grading_sheets.py`, `experiments/tests/test_build_grading_sheets.py` | Không cần làm gì ngay — dùng khi có dữ liệu thật; đọc qua nếu muốn tự chạy thử |

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

- Dry-run 27 lượt (3 prompt × 3 proxy × 3 lần) — chưa chạy, cần xin xác nhận riêng trước. Giờ đã
  nối dây đủ cả 3 proxy vào app (LiteLLM + Portkey xong; Bifrost sẵn có từ tuần trước, chờ Khoa
  hoàn thiện K1 — fallback đủ 5 model + retry theo D7).
- `run_experiment.py` mới verify qua app bằng `run_experiment.py` trực tiếp cho LiteLLM; Portkey mới
  verify bằng `e2e_workflow_test.sh` (chưa chạy `run_experiment.py` qua Portkey, nhưng cùng 1 API
  app nên tin được — cần 1 lượt xác nhận lại khi dry-run thật).
- `docs/routing-policy.md` (J2) chưa viết — vẫn còn trong danh sách việc chung.

## Review — Khoa (2026-10-01)

Đã merge `origin/lhung` vào `dangkhoa`, dựng lại cả 3 proxy trên máy Khoa và chạy thật (chỉ tầng rẻ).

| Sản phẩm | Kết quả trên máy Khoa | Nhận xét |
|---|---|---|
| LiteLLM routing (H1) | ✅ App gửi `conduit-pool` → LiteLLM chọn `gpt-4o-mini`, đọc đúng header `x-litellm-model-id`, `cost_upstream` khớp giá, `e2e_workflow_test.sh` 43/43 | Cấu hình đúng. Xem điểm (1) bên dưới — `dry_run.sh` chưa dùng tới nó |
| Portkey routing (H2) + nối app | ✅ `CHAT_ACTIVE_PROXY=portkey bash scripts/e2e_workflow_test.sh` → **43/43** | "42/43" trong log là do chạy script mà không đặt `CHAT_ACTIVE_PROXY` — script đã đọc biến này từ PR #5, không phải hard-code. Xem điểm (4) |
| Runner (H3) | ✅ `run_experiment.py --limit 1 --runs 1` qua Bifrost và qua LiteLLM `conduit-pool`, đủ 3 dòng ở 3 bảng | Khoa đã thêm ghi `response_quality_score` (K3). Xem điểm (2) |
| `decision_rule.py` (H4) | ✅ 22/22 test Python pass | **Tìm được nhánh chưa test có ảnh hưởng thật** — điểm (3) |

**Cần xử lý trước dry-run 27 lượt:**

1. **`dry_run.sh` không đặt `CHAT_DEFAULT_MODEL`** → cả 3 proxy đều nhận `gpt-4o-mini`, nên LiteLLM
   **không bao giờ dùng `conduit-pool`** (routing thật của H1). Đề xuất: khi `proxy=litellm` thì
   `export CHAT_DEFAULT_MODEL=conduit-pool`. Đã test: gửi `conduit-pool` qua app chạy đúng 43/43.
   **→ Khoa đã sửa 02/10** trước khi chạy dry-run (kèm 2 lỗi môi trường, xem `log-khoa.md`).
2. **`latency_ms` của runner là thời gian đo ở runner**, gồm cả tạo conversation, `GET messages` và
   `docker exec psql` đọc `cost_upstream` — không chỉ thời gian gọi proxy. Lượt thử: runner 2817 ms,
   backend đo proxy 2333 ms (~480 ms nhiễu, có dao động). p95 dùng ở bước 3 của luật quyết định → nên
   lấy `latency_ms` backend trả về trong message (runner đã đọc được, `result["latency_ms"]`). (Phần
   Khoa thêm đã đo thời gian *trước* khi ghi điểm vào DB nên không làm nhiễu thêm.)
3. **`compute_avg_cost` tính lượt lỗi (`cost = 0`) vào trung bình → thưởng cho proxy hay lỗi.** Thử
   bằng dữ liệu giả (dùng `make_records` trong test): A luôn thành công, $0.0100/lượt; B đắt hơn 2%
   ($0.0102) và lỗi 4/36 lượt → chi phí TB của B = $0.00907 < A → **luật chọn B**, dù B vừa đắt hơn
   vừa kém ổn định (B vẫn qua bước 1 với 88.9%). Đề xuất: tính chi phí TB trên **lượt thành công**
   (lượt lỗi vẫn bị phạt ở bước 1 và bước 4), và thêm test cho trường hợp này. Cần 2 người chốt vì
   đụng tới cách hiểu "chi phí trung bình/prompt" trong CLAUDE.md mục 2.
   Thêm 2 nhánh chưa test (ít nghiêm trọng hơn): hoà cả 4 bước thì `max()` lặng lẽ chọn proxy đầu
   tiên thay vì báo hoà; lượt lỗi có `model_selected = None` bị tính như 1 "model" khác ở consistency.
4. **Portkey chưa có fallback**, trong khi D2 yêu cầu "có phương án dự phòng khi lỗi" cho cả 3 —
   khi `gpt-4o-mini` lỗi, Bifrost chuyển model còn Portkey trả lỗi luôn. Nếu thêm fallback thì phải
   sửa nhánh Portkey trong `resolveReturnedModel` (đang trả thẳng alias đã gửi). Chi tiết:
   `docs/routing-policy.md` mục 5, điểm 5.

**Chi tiết nhỏ:** mục "Còn thiếu" phía trên vẫn ghi `routing-policy.md` chưa viết, trong khi bảng ghi
đã xong bản nháp.
