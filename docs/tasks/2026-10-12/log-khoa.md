# Log tuần 12/10 – 18/10/2026 — Khoa

Theo `docs/tasks/2026-10-12/tasks.md` (Design Y, `docs/experiment-design.md`). Pull `lhung` 15/10,
làm K1–K7 ngày 15–16/10. **Chưa chạy Phase 3** — có 1 vấn đề phải chốt trước (phát hiện A).

## Việc đã làm

| Việc | Kết quả | File | Hùng cần làm |
|---|---|---|---|
| **K1** — Bifrost Complexity Router + 3 CEL rule | ✅ Analyzer `semantic` (`text-embedding-3-small`), giữ 150 câu mẫu mặc định, `state: ready, loaded: 150`. Rule `design-y-SIMPLE/MEDIUM/COMPLEX` priority 5/6/7 → `gpt-4o-mini` / `claude-haiku` / `claude-sonnet`. Gọi thẳng Bifrost: câu dễ → `gpt-4o-mini`, câu đối chứng (shard live DB) → `claude-sonnet-5`, `routing_info` báo đúng model | `proxy-configs/bifrost/complexity-setup.sh` (mới, chạy lại được — tự đọc config hiện có rồi chỉ thêm khối `semantic`, tránh lỗi 400; rule trùng tên thì xoá tạo lại) | Chạy `BIFROST_URL=… bash proxy-configs/bifrost/complexity-setup.sh` sau `setup.sh`, gửi 2–3 câu, đối chiếu tier trong `/api/logs` |
| **K2** — Portkey theo `metadata.prompt_len` | ✅ `$lt 211` → `gpt-4o-mini`, `$gte 385` → `claude-sonnet`, default `claude-haiku` (ngưỡng H3, `routing-policy.md` mục 7). **Đã thử rủi ro "so sánh kiểu chuỗi"** bằng 3 target cùng là `gpt-4o-mini` (1 token/lượt): 93 / 300 / 1102 gửi dạng số **và** dạng chuỗi đều ra đúng tier → Portkey so theo **số** | `proxy-configs/portkey/config.json` | Gửi 1 prompt ngắn + 1 dài qua app, kiểm model trong DB |
| **K3** — backend gửi `prompt_len` + `max_tokens` | ✅ `max_tokens: 512` gửi kèm **mọi** request (`app.chat.max-tokens`, env `CHAT_MAX_TOKENS`) — D7 lần đầu được thực thi qua app (Bifrost/Portkey/LiteLLM đều cắt đúng ở 512). `prompt_len` = độ dài **tin nhắn user mới nhất** (đếm code point, khớp `len()` của Python dùng để đặt ngưỡng; khớp `message_history_count=1` của Bifrost), gửi qua header **`x-portkey-metadata`**, **chỉ khi proxy là Portkey** — không nhét `metadata` vào body để tránh bị chuyển tiếp sang provider | `ChatProxyProperties.java`, `HttpProxyChatClient.java`, `application.yml` | Đọc diff |
| **K4** — sửa `resolveReturnedModel` (Portkey) | ✅ Đọc header **`x-portkey-last-used-option-index`** (`config.targets[N]`, đã thấy tận mắt) → tên target N = alias trong `model_pricing`. Thiếu header thì trả id thô của provider (VD `gpt-4o-mini-2024-07-18`) chứ không đoán là alias đã gửi → lộ ra khi kiểm DB thay vì sai trong im lặng. Qua app: 93 ký tự → `gpt-4o-mini` $0.0000183, 315 → `claude-haiku` $0.000099, 1102 → `claude-sonnet` $0.000806 — cả 3 giá tính tay khớp DB | `HttpProxyChatClient.java`, `HttpProxyChatClientTest.java` (5 test mới) | Đọc diff |
| Kiểm Phase 1 | ✅ `e2e_workflow_test.sh` **43/43** với cả `portkey`, `bifrost`, `litellm` (`conduit-pool`). Unit test Java 9/9 | — | — |
| Runner + `dry_run.sh` (file của Hùng) | ✅ Thêm `--sets` / `--per-set` cho runner, `SETS` / `PER_SET` cho `dry_run.sh` — dry-run cần 1 item/bộ, Phase 3 chia đôi theo bộ (`--limit` cũ chỉ lấy N item đầu = toàn MMLU). Gõ sai tên bộ thì báo lỗi. `dry_run.sh` giờ **chấm (`grade_results.py --db`) trước khi gộp + áp luật** | `run_experiment.py`, `dry_run.sh` | Đọc diff |
| Sửa bộ chấm HumanEval (file của Hùng) | ✅ Phát hiện B. Luôn đặt đề gốc trước code model, giống harness chính thức. Test mới tái hiện đúng ca lỗi; 45/45 test Python pass | `graders.py`, `test_graders.py` | **Review kỹ** — đổi cách chấm |
| **K5** — dry-run 36 lượt | ✅ `mmlu_01`, `gsm8k_01`, `humaneval_01`, `ifeval_01` × 3 proxy × 3 lần, **36/36 thành công, 0 lỗi**. Chi phí **$0.0505** | `experiments/results/run_{litellm,bifrost,portkey}_20261015T17*.json`, gộp + luật: `experiments/results/dry-run-20261016-003021/` | — |
| **K6** — kiểm `routing_decisions` | ✅ 36/36 dòng: model nào cũng có trong `model_pricing`, **0 dòng sai giá** khi tính lại (token × giá), `predicted_cost` = `cost_upstream`, 0 lỗi. Tier suy được từ model | — | — |
| **K7** — `decision_rule.py` | ✅ Chạy ra bảng: chỉ Bifrost qua 80% → chọn Bifrost (4 item/proxy, **chỉ là kiểm hệ thống, không phải kết quả**) | `dry-run-20261016-003021/decision_rule_output.json` | — |

### Kết quả dry-run (sau khi sửa bộ chấm HumanEval)

| Proxy | Model đã chọn (12 lượt) | Đạt | Chi phí | Chi phí / câu đạt |
|---|---|---|---|---|
| LiteLLM | `gpt-4o-mini` ×12 | 9/12 (75%) | $0.00162 | $0.00018 |
| Bifrost | `gpt-4o-mini` ×7, `claude-haiku` ×2, `claude-sonnet` ×3 | 11/12 (91.7%) | $0.02178 | $0.00198 |
| Portkey | `gpt-4o-mini` ×6, `claude-sonnet` ×6 | 9/12 (75%) | $0.02708 | $0.00301 |

Ba proxy giờ chọn model **khác nhau thật** — Design Y chạy đúng như thiết kế.

## Phát hiện quan trọng

**A. ⛔ `claude-sonnet-5` mặc định có bước suy nghĩ (thinking) — với `max_tokens: 512` nó tiêu hết
token vào suy nghĩ và trả lời RỖNG, mà vẫn bị tính tiền.** Portkey → `mmlu_01` → `claude-sonnet`: 3/3
lượt 512 token ra, nội dung rỗng, chấm 0. Gọi **thẳng API Anthropic** cùng prompt: `stop_reason:
max_tokens`, `output_tokens_details.thinking_tokens: 512`, chỉ có 1 khối `thinking` → **không phải lỗi
Portkey**, proxy nào gửi câu khó sang Sonnet cũng dính. Hệ quả: nhánh nào định tuyến "thông minh" sang
model đắt (Bifrost COMPLEX, Portkey câu dài) bị **phạt oan** — vừa trả tiền 512 token vừa bị 0 điểm.
Làm lệch đúng giả thuyết H2/H3. **Phải chốt trước Phase 3** (xem "Cần chốt").

**B. Bộ chấm HumanEval chấm oan lời giải đúng (đã sửa).** `humaneval_01` (`factorize`): đề có `from
typing import List`, model viết lại cả hàm nhưng bỏ dòng import → bộ chấm chỉ chạy code của model →
`NameError`. Harness chính thức chạy *đề + câu trả lời + test* nên có sẵn import. Trước khi sửa:
LiteLLM 50% / Bifrost 66.7% / Portkey 75% và luật báo "không proxy nào đạt"; sau khi sửa: 75% / 91.7% /
75%. Một bug chấm điểm đủ đổi kết luận.

**C. Bifrost KHÔNG tất định ở `mmlu_01`:** lượt 1 → `gpt-4o-mini`, lượt 2–3 → `claude-haiku` (cùng
prompt). Trái với kết luận "phân loại tất định" ở đợt thử 09/10. `consistency_rate` Bifrost = 0.75. Có
thể là lượt đầu (warmup/cache embedding) — cần xem thêm ở Phase 3, nhưng **không được viết "tất định"
vào báo cáo** nếu chưa kiểm lại.

**D. Bifrost hiếm khi ra MEDIUM.** 4 prompt dài thử thẳng (2 IFEval 385/510 ký tự, 1 blog 401 ký tự, 1
câu shard DB) → toàn SIMPLE hoặc COMPLEX. Dry-run có 2 lượt MEDIUM (`mmlu_01`). Nên "cùng 1 prompt dài
qua 3 proxy → 3 model khác nhau" (đạt khi Phase 1) **không tìm được prompt nào thỏa**; thay bằng bằng
chứng từng proxy định tuyến đúng (bảng trên) — 3 proxy ra 3 **phân bố** model khác nhau.

**E. `decision_rule.py` chỉ in `pareto_data` của proxy qua bước 1.** Proxy bị loại không hiện số liệu
→ báo cáo Phase 3 phải tự lập bảng cho cả 3 proxy (như bảng trên), không chép nguyên output của luật.

**F. Môi trường:**
- Bộ chấm IFEval cần dữ liệu NLTK `punkt_tab`, **không có trong `requirements.txt`**. Thiếu thì
  verifier trả `followed: False` kèm lỗi → có thể chấm trượt IFEval hàng loạt. Cài:
  `python -c "import nltk; nltk.download('punkt_tab')"`.
- Backend không khởi động: `ClassFormatError: Invalid method Code length 0 … AgentPurchase` — file
  `.class` hỏng trong `target/` (build bị ngắt/IDE biên dịch chồng). `./mvnw clean compile` là hết.

## Chi phí API

| Đợt | Số lượt | Chi phí |
|---|---|---|
| Dry-run K5 (qua app) | 36 | $0.0505 |
| Kiểm Phase 1 qua app (3 Portkey + 1 Bifrost + 3 e2e) | 7 | $0.0061 |
| Gọi thẳng proxy/provider: K1 (2), dò tier Bifrost (3, 1 token), thử Portkey (7, 1 token `gpt-4o-mini`), tìm nguyên nhân A (2 lượt Sonnet) | 14 | ~$0.012 |
| **Tổng** | **57** | **~$0.069** |

Vượt ước tính "~6 lượt" của Phase 1 vì thêm phép thử rủi ro "so sánh kiểu chuỗi" và tìm nguyên nhân
phát hiện A; phần lớn là lượt 1 token. Khoa đã xác nhận phạm vi Phase 1 + dry-run 36 lượt trước khi chạy.

## Cần chốt / bàn cùng nhau — TRƯỚC Phase 3 _(đã giải quyết 17/10, xem mục Phase 3 bên dưới)_

> **Kết quả:** mục 1 → Hùng thử cả (a) và (b), cả hai đều không dùng được (2048 token cũng bị Sonnet
> suy nghĩ hết; tắt thinking cần tham số riêng của Anthropic mà backend không biết trước proxy chọn
> model nào; Sonnet còn từ chối `temperature: 0`) → **D12: bỏ Sonnet, tier đắt dùng `gpt-4o`**,
> `max_tokens` 1024. Mục 2 → Hùng duyệt. Mục 3 → nguyên nhân thật là analyzer quá hạn 1.5s, đã nâng 8s.

1. **Phát hiện A — xử lý `max_tokens` với Sonnet thế nào** (đụng D7, phải hai người chốt):
   - (a) Tăng `max_tokens` chung cho cả 3 proxy (VD 2048): công bằng, đơn giản; chi phí Sonnet tối đa
     ~$0.02/lượt thay vì ~$0.005; ước lại ngân sách 360 lượt.
   - (b) Tắt thinking cho Sonnet: tham số riêng của Anthropic, mỗi proxy chuyển tiếp khác nhau → phải
     kiểm cả 3 nhánh, dễ lệch.
   - (c) Giữ 512 và báo cáo như một giới hạn: kết quả chất lượng của các nhánh dùng Sonnet bị kéo thấp
     giả tạo → giả thuyết H2/H3 khó đọc.
   - Khoa nghiêng về **(a)**. Lưu ý thêm: `ifeval_08` đòi ≥ 350 từ (~460 token), sát 512 ngay cả với
     model không suy nghĩ.
2. **Bản sửa bộ chấm HumanEval (B)** — Hùng xác nhận đúng với harness chính thức.
3. **Phát hiện C** — có cần thêm lượt warmup cho Bifrost trước khi đo không (lượt đầu có thể khác).

## Phase 3 — phần Khoa: HumanEval + IFEval, 180 lượt (19/10)

Chạy sau khi pull bản sửa của Hùng (D12, D13, `temperature: 0`, `max_tokens: 1024`, timeout analyzer
8s). Khoa đồng ý D12 và D13.

### Chuẩn bị (đúng 6 bước Hùng giao, chỉnh cho máy Khoa)

| Bước | Kết quả |
|---|---|
| `git pull` (`lhung` → `dangkhoa`, fast-forward) | ✅ test Python 60/60, Java 9/9 |
| `complexity-setup.sh` | ✅ với `BIFROST_URL=http://localhost:18080` (máy Khoa remap port; **`:8080` là Tomcat** chiếm sẵn). `semantic.timeout=8s`, COMPLEX → `gpt-4o` |
| `docker compose up -d --force-recreate litellm` | ✅ `conduit-pool` 4 deployment, không còn Sonnet |
| Xoá `.experiment_identity.json` | ✅ runner tạo user mới, ví 1.000.000 |
| `requirements.txt` + `punkt_tab` | ✅ |
| `preflight.py` | ✅ 15/16 xanh, 0 chặn. **Phải sửa trước:** `preflight.py` gán cứng `localhost:8080` cho 3 mục Bifrost → trên máy Khoa gọi nhầm Tomcat. Thêm đọc `BIFROST_URL` (mặc định vẫn `:8080`). 1 cảnh báo ví là **báo động giả**: preflight đọc ví cũ lớn nhất trong DB, không biết file danh tính đã xoá |

Lệnh: `SPRING_DATASOURCE_URL=…5433… BIFROST_BASE_URL=http://localhost:18080/v1 PROXIES="litellm bifrost portkey" SETS="humaneval,ifeval" RUNS=3 bash experiments/scripts/dry_run.sh`

### Kết quả (20 item × 3 proxy × 3 lần, **180/180 thành công, 0 lỗi**)

| Proxy | Đạt | HumanEval | IFEval | Chi phí | Chi phí / câu đạt | p95 (luật) | Model đã chọn |
|---|---|---|---|---|---|---|---|
| LiteLLM | 53/60 (88.3%) | 30/30 | 23/30 | $0.00671 | $0.000127 | 6242 ms | `gpt-4o-mini` 100% |
| Bifrost | 55/60 (91.7%) | 30/30 | 25/30 | $0.04229 | $0.000769 | 5831 ms | mini 80% · haiku 10% · `gpt-4o` 10% |
| Portkey | 56/60 (93.3%) | 29/30 | 27/30 | $0.06969 | $0.001244 | 6887 ms | haiku 35% · `gpt-4o` 35% · mini 30% |

`decision_rule.py` trên **riêng nửa này**: cả 3 qua cổng 80%, chọn **LiteLLM** (rẻ nhất, cách xa >5%).
**Chưa phải kết luận** — phải gộp với 180 lượt MMLU + GSM8K của Hùng.

Dữ liệu: `experiments/results/run_{litellm,bifrost,portkey}_20261019T13*.json`, gộp + luật + 4 CSV:
`experiments/results/dry-run-20261019-210349/`.

### Kiểm dữ liệu

- `verify_results.py` từng file, `--expect 60`: ✅ cả 3 sạch. (Chạy trên `merged.json` thì báo 60 "trùng
  lượt" — sai đầu vào, script thiết kế cho file 1 proxy; không phải lỗi dữ liệu.)
- DB: 180 dòng `routing_decisions`, 0 model thiếu giá, **0 dòng sai giá** khi tính lại, 0 lỗi.
  Tính tay: Bifrost `ifeval_01` → `gpt-4o`, 33 vào + 1024 ra = $0.0103225 = DB.
- 1 lượt chạm trần 1024 token (Bifrost `ifeval_01` → `gpt-4o`) — vẫn đạt.

### Quan sát

1. **Ba proxy định tuyến khác nhau thật.** Portkey đẩy 70% sang haiku/4o vì HumanEval dài — đúng
   giả thuyết H3 (định tuyến theo *bộ đề* chứ không theo độ khó): chi phí/câu đạt gấp ~10 lần LiteLLM
   chỉ để thêm 3 câu đạt. Bifrost gửi 80% sang mini.
2. **Bifrost xếp `ifeval_01` (33 token đầu vào) vào COMPLEX → `gpt-4o`, sinh 876–1024 token, 9.8–13.3 s**
   — đúng giả thuyết H2 (xếp sai câu không khó lên COMPLEX, tốn tiền + chậm).
3. **H1 (LiteLLM dễ trượt cổng 80%) chưa xảy ra ở nửa này** — 88.3%. IFEval là chỗ nó yếu (23/30).
4. **⚠️ Hai script tính p95 khác nhau.** `decision_rule.py` nội suy tuyến tính (Bifrost 5831 ms),
   `export_tables.py` dùng `statistics.quantiles(n=20)` mặc định `exclusive` (Bifrost **9641 ms**).
   Lệch vì 3 lượt đột biến ở trên rơi đúng vùng p95 khi n=60. Lần này không ảnh hưởng (luật không tới
   bước 3), nhưng **CSV để vẽ biểu đồ và luật phải dùng cùng 1 cách** — đề nghị `export_tables.py` theo
   `decision_rule.py` (`method="inclusive"` cho ra đúng con số của luật).
5. **`temperature: 0` không đảm bảo lặp lại kết quả.** Cùng model, cùng prompt mà đạt/trượt khác nhau
   giữa 3 lần: Bifrost `ifeval_05` (trượt 1, 3), LiteLLM `ifeval_07` (trượt 1), Portkey `humaneval_08`
   (trượt 3). Không ảnh hưởng `consistency_rate` (đo model được chọn — 1.00 cả 3) nhưng khi viết báo
   cáo không được nói "temperature 0 → tất định".

### Chi phí

Phase 3 phần Khoa: **180 lượt, $0.1187**. Cả tuần (Khoa): 237 lượt, ~$0.19.

## Còn thiếu

- Gộp với 180 lượt của Hùng → `decision_rule.py` trên đủ 360 lượt → cùng viết `docs/experiment-results.md`.
- Điền dòng Phase 3 trong bảng nhật ký `tasks.md` khi cả hai xong.
