# Routing policy — mục tiêu chung cho 3 proxy (J2, Phase C)

Tổng hợp từ `docs/litellm-routing-notes.md`, `docs/bifrost-routing-notes.md`,
`docs/portkey-routing-notes.md` (đã đọc kỹ + verify sống cả 3 tính đến 2026-09-30). Đọc file này
**trước khi** phân tích kết quả Phase E — có vài chỗ dễ hiểu nhầm nếu không biết giới hạn của
từng proxy trước.

## 1. Mục tiêu chung (D2, đã chốt 2026-09-29 — `docs/roadmap.md` mục 4)

> Ưu tiên model rẻ nhất đủ tốt, có phương án dự phòng khi lỗi.

Mỗi proxy biểu đạt mục tiêu này bằng cơ chế **riêng của nó** — không proxy nào bị ép làm giống
proxy khác. Đây chính là thứ đang được đánh giá (proxy nào biểu đạt được mục tiêu tốt hơn, rẻ hơn,
ổn định hơn), không phải thứ cần đồng nhất.

**Đã loại khỏi vòng so sánh chính:** Bifrost Complexity Router (tự phân loại độ khó câu hỏi rồi
định tuyến theo tier) — mặc dù là tính năng có sẵn (không vi phạm phạm vi đề tài, xem CLAUDE.md
mục 1), nhưng LiteLLM/Portkey không có cơ chế tương đương, dùng sẽ làm lệch so sánh. Ghi nhận là
hạn chế/khác biệt trong báo cáo, không bật khi chạy Phase E.

## 2. Cách mỗi proxy biểu đạt mục tiêu

### LiteLLM — tự động, có "trí thông minh" thật
- Cơ chế: `routing_strategy: cost-based-routing`, gom 5 model vào 1 alias `conduit-pool`
  (`proxy-configs/litellm/config.yaml`). LiteLLM tự tính giá từng deployment rồi chọn rẻ nhất **cho
  từng lượt gọi** — đây là cơ chế "tự quyết định" duy nhất trong 3 proxy.
- Cần khai tường minh `input_cost_per_token`/`output_cost_per_token` (khớp
  `docs/model-pricing-sources.md`) — bảng giá nội bộ của LiteLLM sai cho
  `gemini/gemini-flash-latest`, không khai sẽ ra quyết định sai (phát hiện H1, 2026-09-29).
- **Không làm được:** chọn model theo độ khó/loại prompt (không có bộ phân loại nội dung) — chỉ
  nhìn giá, không nhìn câu hỏi.

### Bifrost — không tự chọn giữa nhiều model, chỉ có fallback tĩnh
- **Không có khái niệm "1 alias gom nhiều model"** như LiteLLM — muốn "chọn giữa 5 model" phải tự
  làm ở tầng gọi. Cách công bằng nhất mô phỏng mục tiêu D2: khai `fallbacks` — chuỗi dự phòng cố
  định theo thứ tự **rẻ → trung → đắt**, "first success wins" khi provider chính lỗi.
- Weighted routing (chia tải theo `weight`) **không dùng được cho việc này** — nó chỉ chia tải giữa
  nhiều provider phục vụ **cùng 1 model** (multi-cloud), không phải chọn giữa 5 model khác nhau.
- **Thứ tự chuỗi theo giá thật** (`docs/model-pricing-sources.md`), không theo tầng trong CLAUDE.md
  (tầng "đắt" có 2 model, CLAUDE.md không nói cái nào trước): `gpt-4o-mini` → `gemini-flash` →
  `claude-haiku` → `claude-sonnet` → `gpt-4o`. Model chính = model app gửi; 4 model còn lại gửi kèm
  `fallbacks` theo đúng thứ tự trên (`app.chat.proxy-fallback-chains.bifrost` trong `application.yml`).
- **Trạng thái (2026-10-01, K1 xong):** chuỗi đủ 5 model + `max_retries=2`, timeout 45s mỗi provider
  (`proxy-configs/bifrost/setup.sh`). Test sống qua app với OpenAI bị ép lỗi 401: Bifrost thử
  gpt-4o-mini (lỗi) → gemini-flash (retry 2 lần, lỗi tạm thời) → claude-haiku (thành công), app ghi
  đúng `selected_model = claude-haiku` và giá của claude-haiku.

### Portkey — rule tĩnh do người tự viết, không có "alias" sẵn
- Không có model pool (LiteLLM) hay weighted-provider (Bifrost) — chỉ có `strategy.mode:
  "conditional"` khớp `params.model` theo alias → đúng target/model thật. Mô phỏng D2 bằng cách:
  5 condition (1/alias) trỏ đúng model thật, `default` rơi về model rẻ nhất (`gpt-4o-mini`).
- **Không có cost-based/latency-based tự động** — mọi quyết định là rule tĩnh do người viết, không
  tự đo giá/độ trễ. "Routing thông minh" ở Portkey thực chất là cấu hình cứng.
- Portkey OSS **không tự thay `$VAR`** trong config như LiteLLM (`os.environ/VAR`) — phải tự thay
  bằng giá trị thật trước khi gửi header `x-portkey-config` (phát hiện H2).
- **Trạng thái (2026-09-30):** đã nối dây vào app thật, verify sống — sẵn sàng cho dry-run.

## 3. Bảng so sánh nhanh (giới hạn từng proxy)

| | LiteLLM | Bifrost | Portkey |
|---|---|---|---|
| Chọn model theo cost tự động | ✅ `cost-based-routing` | ❌ Enterprise-only | ❌ rule tĩnh, không tự đo giá |
| Gom nhiều model thành 1 alias | ✅ `conduit-pool` | ❌ không có khái niệm này | ⚠️ mô phỏng bằng conditional (tĩnh) |
| Failover khi lỗi | ⚠️ chưa cấu hình `fallbacks` | ✅ `fallbacks`, test sống | ➖ chưa cấu hình (static nên ít cần) |
| Chọn theo độ khó câu hỏi | ❌ | ✅ Complexity Router (Beta) — **không dùng** (mục 1) | ❌ |
| Tự nhận key từ `.env`/container | ✅ | ✅ (trừ Gemini, phải khai tay) | ❌ (phải tự thay `$VAR` mỗi request) |
| Model thật nằm ở đâu trong response | header `x-litellm-model-id` | `extra_fields.routing_info` | ➖ top-level `model` sai — dùng thẳng alias đã gửi |

## 4. Độ bền — áp dụng giống nhau cả 3 (D7, đã chốt 2026-09-29)

`num_retries=2`, `timeout=45s`. LiteLLM đã áp (`router_settings`); Portkey đã áp (`retry.attempts:
2` mỗi target); Bifrost đã áp 2026-10-01 (`max_retries: 2`, `default_request_timeout_in_seconds:
45` cho openai/anthropic/gemini — `proxy-configs/bifrost/setup.sh`).

Lượt lỗi sau khi hết retry: ghi `messages`+`usage_logs.status=error`+`routing_decisions` (không
tính phí), tính là 1 trong 3 lần lặp, không chạy bù.

## 5. Ảnh hưởng tới cách diễn giải kết quả Phase E — đọc trước khi phân tích

1. **LiteLLM cost-based gần như luôn chọn tầng rẻ** (GPT-4o-mini/Gemini Flash) → độ chính xác
   closed-QA của LiteLLM sẽ gần bằng độ chính xác riêng của 2 model đó, dễ qua ngưỡng 80% nhưng
   *không* phản ánh việc đánh đổi cost-quality thật giữa 5 model. Đây là đặc tính của strategy,
   không phải lỗi proxy — ghi rõ trong báo cáo, đừng diễn giải nhầm thành "LiteLLM thông minh hơn".
2. **Bifrost/Portkey đều dùng cấu hình tĩnh (không ngẫu nhiên)** → gần như chắc chắn có
   **consistency rate cao nhất** ở bước 4 của quy tắc quyết định. "Ổn định hơn" ở đây **không có
   nghĩa là "định tuyến thông minh hơn"** — chỉ là ít biến động hơn vì không có gì để dao động.
3. Vì 3 cơ chế khác bản chất nhau (1 cái tự quyết định thật, 2 cái là cấu hình tay), nếu kết quả
   cuối chọn LiteLLM vì rẻ nhất, cần nêu rõ trong báo cáo: đây là do LiteLLM **có khả năng tự động
   hoá** việc chọn rẻ nhất mà 2 proxy kia không có — sự khác biệt về **năng lực biểu đạt**, không
   chỉ là "proxy X nhanh hơn/rẻ hơn proxy Y" ở cùng một phép so sánh ngang hàng.

**Khoa bổ sung (2026-10-01) — cần 2 người thống nhất trước dry-run:**

4. **Khi không có lỗi, cả 3 proxy đều dùng `gpt-4o-mini`.** LiteLLM tự chọn rẻ nhất (10/10 lượt ở H1),
   Bifrost dùng `gpt-4o-mini` làm model chính, Portkey `default` cũng trỏ `gpt-4o-mini`. Vậy ở lượt
   bình thường, 3 proxy gọi **cùng 1 model** → chênh lệch chi phí/chất lượng gần như bằng 0; thứ thật
   sự khác nhau là **overhead độ trễ của proxy** và **cách xử lý lượt lỗi**. Nên nói rõ trong báo cáo,
   và có thể nên hỏi GVHD xem phép so sánh như vậy đã đủ trả lời câu hỏi nghiên cứu chưa.
5. **Portkey chưa có phương án dự phòng.** D2 yêu cầu "có phương án dự phòng khi lỗi" cho cả 3, nhưng
   config Portkey chỉ ánh xạ mỗi alias → 1 target (+ retry). Khi `gpt-4o-mini` lỗi: Bifrost chuyển
   model, Portkey trả lỗi luôn → Portkey bị tính thêm lượt lỗi chỉ vì thiếu cấu hình, không phải vì
   kém hơn. Nếu thêm `strategy.mode: fallback` cho Portkey thì phải sửa luôn
   `HttpProxyChatClient.resolveReturnedModel` (nhánh Portkey đang trả thẳng alias đã gửi — sẽ ghi sai
   model và sai giá khi có fallback).
6. **Timeout 2 tầng.** D7 đặt 45s *mỗi lần thử* ở proxy, nhưng backend (`HttpProxyChatClient.
   REQUEST_TIMEOUT`) cũng cắt cả lượt ở 45s. Với `num_retries=2` + chuỗi fallback, proxy có thể cần
   lâu hơn 45s → backend bỏ cuộc trước khi proxy kịp chuyển model. Lượt test ép lỗi của Bifrost mất
   12.3s nên chưa chạm, nhưng 1 lượt Gemini 503 từng mất 19s. Áp dụng giống nhau cho cả 3 proxy nên
   vẫn công bằng, nhưng cần ghi vào phần giới hạn.

## 6. Trạng thái cấu hình hiện tại (2026-09-30)

| Proxy | Cấu hình routing | Verify trực tiếp | Verify qua app thật (D3) |
|---|---|---|---|
| LiteLLM | ✅ `cost-based-routing`, D7 | ✅ 10/10 lượt (H1) | ✅ (`run_experiment.py`, H3) |
| Portkey | ✅ conditional, D7 | ✅ 3/3 lượt (H2) | ✅ (`e2e_workflow_test.sh`, 2026-09-30) |
| Bifrost | ✅ `fallbacks` đủ 5 model theo giá, D7 (2026-10-01) | ✅ chuỗi + ép lỗi | ✅ `e2e_workflow_test.sh` 43/43 + `run_experiment.py` 1 prompt + 1 lượt ép lỗi (2026-10-01) |

**Dry-run 27 lượt không còn bị chặn bởi Bifrost** (K1 xong 2026-10-01). Còn 2 việc nên xử lý trước khi
chạy, chi tiết ở phần review cuối `docs/tasks/2026-09-28/log-hung.md`: (a) `dry_run.sh` chưa đặt
`CHAT_DEFAULT_MODEL=conduit-pool` cho LiteLLM nên routing thật của LiteLLM không được dùng;
(b) `decision_rule.py` tính lượt lỗi `cost = 0` vào chi phí trung bình → thưởng cho proxy hay lỗi.
