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

## Cần chốt / bàn cùng nhau — TRƯỚC Phase 3

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

## Còn thiếu

- Phase 3 (180 lượt HumanEval + IFEval) **chưa chạy** — chờ chốt mục 1.
- Review chéo phần Hùng (đối chiếu metric với paper, ngưỡng `prompt_len`): đã đối chiếu 40/40 item
  khớp nguyên văn với file gốc của MMLU / GSM8K / HumanEval / IFEval (15/10); ngưỡng `prompt_len` suy
  từ tercile phân bố thật — hợp lý. Ghi review chính thức vào `log-hung.md` sau.
