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
- **Trạng thái (2026-09-30):** fallback đã chạy được thật (test 1 cặp, 2026-09-26), nhưng **chưa đủ
  cả 5 model trong 1 chuỗi**, và `max_retries` vẫn ở mặc định `0` (chưa khớp D7) — việc của Khoa
  (K1), hạn cuối tuần 28/09–04/10.

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
2` mỗi target); Bifrost **chưa** (mặc định `max_retries: 0`, việc của K1).

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

## 6. Trạng thái cấu hình hiện tại (2026-09-30)

| Proxy | Cấu hình routing | Verify trực tiếp | Verify qua app thật (D3) |
|---|---|---|---|
| LiteLLM | ✅ `cost-based-routing`, D7 | ✅ 10/10 lượt (H1) | ✅ (`run_experiment.py`, H3) |
| Portkey | ✅ conditional, D7 | ✅ 3/3 lượt (H2) | ✅ (`e2e_workflow_test.sh`, 2026-09-30) |
| Bifrost | ⬜ fallback chưa đủ 5 model, chưa áp D7 | ✅ (tuần trước, 1 cặp) | ✅ (tuần trước, chưa có fallback/D7) | 

**Chặn dry-run 27 lượt:** chờ Khoa hoàn thiện Bifrost (K1) — chuỗi `fallbacks` đủ 5 model theo thứ
tự rẻ→trung→đắt (mục 2) + `max_retries=2` (mục 4).
