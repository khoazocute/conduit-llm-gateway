# Task tuần 28/09 – 04/10/2026 (Hùng & Khoa)

Thuộc lộ trình `docs/roadmap.md`: tuần này gộp **Phase C + Phase D** (cấu hình routing thật cho 3
proxy, rồi viết runner + chạy thử nhỏ 27 lượt) — Hùng chủ động đẩy nhanh tiến độ, không đợi tách
riêng 2 tuần như roadmap gốc. Ký hiệu **A→R** = người viết → người phản biện. Việc ghi "Nếu còn
thời gian" là mở rộng, không bắt buộc.

**Rủi ro của việc gộp (nói thẳng để biết mà canh):** Phase D phụ thuộc Phase C xong trước (runner
cần routing thật mới có gì để đo) — nên trong tuần vẫn phải làm C xong trước rồi mới D, không làm
song song được hoàn toàn. Nếu C trễ, ưu tiên xong C cho chắc, đừng cắt ngắn C để kịp D — D chưa
xong thì lùi được, C mà cấu hình ẩu thì toàn bộ dữ liệu Phase E sau này sai theo.
**Lượt gọi thật (27 lượt dry-run) chỉ chạy khi đã xin xác nhận riêng lúc đó** (CLAUDE.md mục 2,
D1) — không tự chạy chỉ vì đã ghi trong kế hoạch tuần.

**Bản nháp do Hùng dựng lúc tạo folder (29/09, giữa tuần vì mới đổi quy ước) — điều chỉnh tự do ở
buổi họp đầu tuần, không coi đây là đã chốt.**

**Quy ước mới (đọc trước khi làm):** đây là tuần đầu tiên dùng `docs/tasks/<tuần>/` thay cho
`docs-local/tasks-*.md`. Mỗi người ghi output/log vào đúng file riêng của mình
(`log-hung.md`/`log-khoa.md`), commit kèm code, **không paste log vào chat nữa** — người kia tự
`git pull` và đọc. Review (nếu có) viết thẳng vào cuối file log được review, dưới mục
`## Review — <người review> (<ngày>)`.

## Đích của tuần (kiểm tra vào cuối tuần)

- [x] D2 (mục tiêu routing chung để so 3 proxy công bằng) và D7 (`max_retries`/timeout/cách tính
      lượt lỗi) có kết luận, ghi vào `docs/roadmap.md` mục 4. — chốt 2026-09-29.
- [x] `docs/routing-policy.md` tồn tại: mục tiêu chung + cách mỗi proxy diễn đạt được/không diễn
      đạt được (dựa trên `docs/litellm-routing-notes.md`, `bifrost-routing-notes.md`,
      `portkey-routing-notes.md`). — xong 2026-09-30 (Hùng viết, chờ Khoa đọc/đồng ý — J2 "Xong khi"
      cần cả 2 người, mới có 1 người).
- [x] LiteLLM chạy với routing strategy thật (không còn `simple-shuffle` mặc định), xác định được
      `selected_model` mỗi lượt. — xong 2026-09-29 (H1).
- [x] Bifrost có chuỗi `fallbacks` thật theo D2 (phần lớn nền tảng đã xong từ tuần trước — K4). — xong
      2026-10-01 (K1): đủ 5 model theo giá thật + `max_retries=2`/timeout 45s, test ép lỗi qua app.
- [x] Portkey có ít nhất 1 rule thật (không còn `strategy.mode: "single"`). — xong 2026-09-29 (H2);
      nối dây vào app thật (chat qua app gọi đúng Portkey) — xong 2026-09-30.
- [x] `app.chat.default-model` đổi lại `gpt-4o-mini` (đang tạm để `gemini-flash` từ lúc test Gemini
      tuần trước) — OpenAI top-up **đã xong từ trước** (1 key dùng chung cho cả Hùng và Khoa, chia
      tiền sau; Khoa đã xác nhận gọi được cả 5 model từ 26/09), không còn gì phải chờ.
- [x] Runner (`experiments/scripts/run_experiment.py`) gọi thật qua app Conduit (D3), lặp 3
      lần/prompt, lưu kết quả thô + ghi `messages`/`usage_logs`/`routing_decisions`. — xong 2026-09-29
      (H3), verify với `--limit 1 --runs 1`, chưa chạy dry-run 27 lượt đầy đủ.
- [x] `experiments/analysis/decision_rule.py` kiểm chứng bằng dữ liệu giả (biết trước kết quả từng
      nhánh của luật) — **không cần key thật**, chạy trước khi tốn tiền cho dry-run. — xong 2026-09-29
      (H4), 16/16 test pass.
- [ ] Dry-run 3 prompt × 3 proxy × 3 lần = 27 lượt (**chỉ chạy sau khi xin xác nhận riêng lúc đó** —
      chưa xin, chưa chạy).

## Việc chung (cả hai)

**J1. Họp đầu tuần chốt D2 + D7** — ✅ xong 2026-09-29
- D2: **đã chốt** — ưu tiên model rẻ nhất, có phương án dự phòng khi lỗi; LiteLLM `cost-based-routing`,
  Bifrost/Portkey chuỗi tĩnh rẻ→trung→đắt; không dùng Bifrost Complexity Router ở vòng chính.
- D7: **đã chốt** — `num_retries=2`, `timeout=45s` giống nhau cả 3 proxy; lượt lỗi ghi log đầy đủ,
  không tính phí, tính là 1 lần lặp, không chạy bù.
- Chi tiết đầy đủ: `docs/roadmap.md` mục 4.

**J2. `docs/routing-policy.md`** — 🟨 bản nháp xong 2026-09-30, chờ Khoa đọc
- Tổng hợp từ D2 + 3 file routing-notes đã có. Bảng "proxy nào diễn đạt được gì" (đã có sẵn khung ở
  `bifrost-routing-notes.md` mục 4, làm tương tự cho LiteLLM/Portkey).
- Xong khi: file tồn tại, cả hai đọc và đồng ý; nếu cần hỏi GVHD thì hỏi trước khi chốt.
- Khoa đọc `docs/routing-policy.md`, đặc biệt mục 5 (ảnh hưởng cách diễn giải kết quả) — nếu đồng ý
  thì coi J2 xong, không cần sửa gì; nếu không đồng ý thì sửa trực tiếp vào file.

**J3. Review chéo (giữa/cuối tuần)**
- Theo danh sách "Review chéo" bên dưới.
- Còn nợ từ tuần trước: **thống nhất điểm C03** trong `experiments/results/grading-sample.csv`
  (Khoa chấm 0.5, Hùng chấm 1 ở tiêu chí "không lỗi" — xem `docs-local` hoặc hỏi lại Hùng lý do cho
  0.5). Ghi kết luận + lý do vào cuối `docs/grading-rubric.md`.

---

## Hùng

**H1. Cấu hình LiteLLM routing thật** — ✅ xong 2026-09-29
- `proxy-configs/litellm/config.yaml`: thêm alias `conduit-pool` (5 deployment), `routing_strategy:
  cost-based-routing` (D2), `num_retries=2`/`timeout=45` (D7). Khai tường minh `input_cost_per_token`/
  `output_cost_per_token` cho từng deployment — LiteLLM không có giá đúng cho
  `gemini/gemini-flash-latest` trong bảng giá nội bộ, ban đầu chọn nhầm gemini-flash dù đắt hơn.
- Xong khi: gọi alias `conduit-pool` nhiều lần, xác định được model LiteLLM tự chọn mỗi lần —
  **10/10 lượt chọn đúng `gpt-4o-mini`** (rẻ nhất). Model thật nằm ở header `x-litellm-model-id`,
  không phải trong JSON body. Ghi chú đầy đủ ở `docs/litellm-routing-notes.md`.

**H2. Cấu hình Portkey routing thật** — ✅ xong 2026-09-29
- `strategy.mode: "conditional"`, 5 condition khớp `params.model` theo alias → đúng target/model
  thật (mô phỏng "alias" mà Portkey không có sẵn), `default: gpt-4o-mini`. Cũng sửa luôn 3 model cũ
  đã bị gỡ (`gemini-1.5-flash`, `claude-3-5-haiku/sonnet-20241022` → tên mới khớp LiteLLM).
- Xong khi: 3/3 lượt test đúng — alias khớp → đúng target; alias lạ → rơi về default.
- **Phát hiện quan trọng:** Portkey OSS không tự thay `$VAR` trong `api_key` (khác LiteLLM) — bên
  gửi request phải tự thay bằng giá trị thật trước khi đưa vào header `x-portkey-config`. Xem
  `docs/portkey-routing-notes.md`.
- **Lệch chính sách chi phí (tự nhận):** 1 trong 3 lượt test lỡ gọi tầng đắt (Claude Sonnet 5) thay
  vì tầng rẻ — không dừng xin xác nhận trước như đáng lẽ phải làm. Chi phí không đáng kể, nhưng ghi
  lại đúng thực tế, xem `experiments/results/h2-portkey-routing-2026-09-29/README.md`.
- **Nối dây vào app thật (2026-09-30, để chuẩn bị dry-run 27 lượt):** hôm 29/09 mới verify gọi
  *trực tiếp* Portkey, app chưa thực sự gọi được (`HttpProxyChatClient` chỉ gửi `Authorization`,
  không gửi `x-portkey-config`). Đã sửa: tự đọc `proxy-configs/portkey/config.json`, tự thay `$VAR`
  bằng giá trị thật, gắn header khi `active-proxy=portkey`. Cũng sửa `resolveReturnedModel` — Portkey
  trả `model` là ID đầy đủ của provider (không khớp `model_pricing`), nhưng vì routing của mình tĩnh
  1-1 nên trả thẳng alias đã gửi là đúng, không cần tra bảng như Bifrost. Verify qua
  `e2e_workflow_test.sh` với `CHAT_ACTIVE_PROXY=portkey`: chat thành công, `model_used=gpt-4o-mini`,
  `cost_upstream` khớp giá — 42/43 pass (1 "fail" là do chính script hard-code `proxy_name=litellm`,
  không phải lỗi thật).

**H3. Đổi `default-model`, viết runner** — ✅ xong 2026-09-29
- `application.yml`: `default-model: ${CHAT_DEFAULT_MODEL:gpt-4o-mini}` — mặc định đã commit là
  `gpt-4o-mini`, override qua env khi cần test `conduit-pool`.
- **Phát hiện + sửa code:** `HttpProxyChatClient` cần đọc header `x-litellm-model-id` để lấy đúng
  model LiteLLM đã chọn khi dùng `conduit-pool` (JSON body chỉ trả tên nhóm, xem H1) — đã sửa
  `resolveReturnedModel` đọc header này trước, giữ nguyên logic Bifrost (`routing_info`) của Khoa.
- Viết lại hoàn chỉnh `experiments/scripts/run_experiment.py` theo D3 (gọi qua app Conduit thật,
  KHÔNG gọi thẳng proxy — sửa lại TODO cũ trong file vốn ghi nhầm theo đề xuất D3 đã bị bác):
  bootstrap 1 lần (creator+agent miễn phí+admin duyệt+buyer, lưu vào
  `.experiment_identity.json` — gitignored), gọi `POST /conversations` → SSE → `GET .../messages`
  lấy `model_used`/`credit_charged`/`latency_ms`, đọc thêm `usage_logs.cost_upstream` qua psql
  (API không lộ trường này), chấm tự động closed-QA, ghi từng record ngay khi có.
- Xong khi: chạy được với **1 prompt duy nhất** trên 1 proxy (`--limit 1 --runs 1`) và ra đúng file
  kết quả + đủ 3 dòng `messages`/`usage_logs`/`routing_decisions` — **verify thật, có bằng chứng**:
  `experiments/results/run_litellm_20260929T084350Z.json`, model chọn đúng `gpt-4o-mini`,
  `closed_qa_correct: true`.
- **Chưa làm:** dry-run 27 lượt đầy đủ (chờ xin xác nhận riêng), chạy thử qua Bifrost/Portkey (mới
  verify qua LiteLLM).
- **Ngoài ý muốn nhưng cần biết:** `docker exec ... psql` khi bootstrap nhận ra máy Hùng có
  `model_pricing` = 0 dòng (K2 là việc chèn tay trên máy Khoa, không phải migration) — đã tự chèn
  10 dòng đúng số liệu `docs/model-pricing-sources.md` để `cost_upstream` không về 0. **Khoa/ai dựng
  máy mới đều cần tự làm bước này** (chạy admin UI hoặc INSERT tay), không tự động theo migration.

**H4. Kiểm chứng `decision_rule.py`** — ✅ xong 2026-09-29
- Dùng dữ liệu giả (viết tay hoặc random có kiểm soát) cho từng nhánh của luật quyết định (loại
  <80%, chi phí, chênh <5% → p95, hòa → consistency) — không cần key thật.
- Xong khi: mỗi nhánh có ít nhất 1 test case biết trước kết quả, script cho ra đúng kết luận mong
  đợi. — `experiments/tests/test_decision_rule.py`, 16/16 test pass.

**H5 (chuẩn bị trước cho dry-run, làm khi chờ Khoa xong K1)** — ✅ xong 2026-09-30
- `experiments/scripts/dry_run.sh`: gộp quy trình chạy dry-run/thực nghiệm qua N proxy (restart
  backend đúng `CHAT_ACTIVE_PROXY` → chờ sẵn sàng → chạy `run_experiment.py` → proxy tiếp theo) —
  vốn phải làm tay 3 lần. Test cơ chế bằng `PROMPT_LIMIT=0` (không tốn tiền) qua LiteLLM + Portkey:
  restart đúng, bootstrap đúng, ghi kết quả đúng. Khi Khoa xong K1, chỉ cần 1 lệnh
  `PROMPT_LIMIT=3 RUNS=3 bash experiments/scripts/dry_run.sh` là chạy đủ 27 lượt (sau khi xin xác
  nhận, script không tự hỏi lại).
- `experiments/scripts/build_grading_sheets.py`: xuất bảng chấm mù cho 18 câu code+mở từ kết quả
  runner — tự loại closed-QA, tự tách lượt lỗi (0 điểm, D7, không đưa người chấm), xáo trộn ẩn danh,
  chia mẫu chấm kép 30% (D6) giữa Hùng/Khoa. Test bằng dữ liệu giả —
  `experiments/tests/test_build_grading_sheets.py`, 6/6 test pass, xác nhận đúng số 49/162 đã ghi
  sẵn trong `docs/eval-prompts.md`.
- Xong khi: cả 2 script chạy được cuối-đến-cuối bằng dữ liệu giả/lượt 0, sẵn sàng dùng ngay khi có
  dữ liệu thật — không cần viết gì thêm lúc chạy Phase E.

---

## Khoa

**K1. Bifrost: hoàn thiện `fallbacks` theo D2**
- Phần lớn đã xong tuần trước (K4: `fallbacks` chạy thật, `routing_info` đọc được). Còn thiếu:
  set `max_retries` theo D7 (hiện `max_retries: 0` mặc định), cấu hình chuỗi fallback đúng thứ tự
  D2 chọn cho **cả 5 model** (tuần trước mới test 1 cặp).
- Xong khi: chuỗi fallback đủ 5 model, retry giống LiteLLM/Portkey theo D7.

**K2. Review C03 với Hùng**
- Đọc lại `experiments/results/grading-sample.csv` dòng `o-0003`, giải thích lý do cho 0.5 điểm
  "không lỗi" (hay đồng ý đổi thành 1) — ghi vào cuối `docs/grading-rubric.md`.
- (K2 cũ "OpenAI top-up" đã xong — dùng chung 1 key với Hùng, chia tiền sau, không cần việc riêng.)

**K3. Ghi log thí nghiệm (D3, Phase D gộp vào tuần này)**
- Phối hợp với H3 (runner): đảm bảo 1 lượt chat qua app tạo đủ `messages` + `usage_logs` +
  `routing_decisions` (kèm `response_quality_score` — cột này hiện có ghi được từ chấm tự động
  closed-QA chưa? kiểm tra lại, nếu chưa thì đây là việc cần làm).
- Xong khi: 1 lượt chat thật qua runner của Hùng cho ra đủ 3 dòng ở 3 bảng, không thiếu cột nào.

**Nếu còn thời gian**
- **K4.** Bifrost Complexity Router: test thử xem có dùng được không (cần "Configure embedding"
  trước, xem `bifrost-routing-notes.md` mục 2) — chỉ làm nếu D2 quyết định có dùng (hiện đang
  **không dùng**, nên việc này ưu tiên thấp).

---

## Danh sách review chéo

| Sản phẩm | Người viết | Người phản biện | Phản biện cần làm gì |
|---|---|---|---|
| `docs/routing-policy.md` | Cả hai (J2) | — | Đọc chéo trước khi coi là chốt |
| Cấu hình LiteLLM thật | Hùng | Khoa | Dựng lại trên máy Khoa, thử 1 lượt |
| Cấu hình Portkey thật | Hùng | Khoa | Dựng lại trên máy Khoa, thử 1 lượt |
| Bifrost `fallbacks` đủ 5 model | Khoa | Hùng | Dựng lại trên máy Hùng, thử 1 lượt lỗi cưỡng ép |
| Runner + `decision_rule.py` kiểm chứng | Hùng | Khoa | Chạy lại trên máy Khoa với 1 prompt, đọc code `decision_rule.py` tìm 1 nhánh chưa test |

## Nếu bị chặn

| Tình huống | Làm gì |
|---|---|
| Chưa chốt được D2 | Đã chốt (29/09), không còn áp dụng |
| Portkey conditional rule phức tạp hơn dự kiến | Tạm dùng rule đơn giản nhất (1 điều kiện), ghi giới hạn vào `routing-policy.md` |
| Phase C (routing 3 proxy) chưa xong kịp giữa tuần | **Không cắt ngắn C để chạy D** — lùi runner/dry-run sang tuần sau, báo lại trong `log-*.md` |
| Runner viết xong nhưng dry-run 27 lượt chưa kịp xin xác nhận | Dừng ở "chạy được 1 prompt", để dry-run đầy đủ cho lần làm việc tiếp theo — không tự ý chạy 27 lượt |

## Nhật ký cuối tuần (điền vào Chủ nhật 04/10)

| Việc | Trạng thái (✅/🟨/⛔) | Ghi chú |
|---|---|---|
| J1–J3 | | |
| H1 | | |
| H2 | | |
| H3 | | |
| H4 | | |
| K1 | | |
| K2 | | |
| K3 | | |
