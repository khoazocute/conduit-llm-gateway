# Routing policy — mục tiêu chung cho 3 proxy (J2, Phase C)

> ⚠️ **Mục 1–2 và mục 5 là THIẾT KẾ CŨ (D2 bản 2026-09-29), giữ lại làm bằng chứng *vì sao* phải
> đổi — không phải mô tả thiết kế đang chạy.** Thiết kế đang chạy là **Design Y** (D2 sửa
> 2026-10-14): mỗi proxy dùng cơ chế mạnh nhất mà bản OSS của nó cho phép. **Nguồn đúng:
> `docs/experiment-design.md`.** Phần còn giá trị trực tiếp cho thiết kế mới: **mục 3** (giới hạn
> từng proxy) và **mục 7** (ngưỡng `prompt_len` của Portkey, chốt 2026-10-14).

Tổng hợp từ `docs/litellm-routing-notes.md`, `docs/bifrost-routing-notes.md`,
`docs/portkey-routing-notes.md` (đã đọc kỹ + verify sống cả 3 tính đến 2026-09-30). Đọc file này
**trước khi** phân tích kết quả Phase E — có vài chỗ dễ hiểu nhầm nếu không biết giới hạn của
từng proxy trước.

## 1. Mục tiêu chung — THIẾT KẾ CŨ (D2 bản 2026-09-29, đã bị D2 sửa 2026-10-14 thay thế)

> Ưu tiên model rẻ nhất đủ tốt, có phương án dự phòng khi lỗi.

Mỗi proxy biểu đạt mục tiêu này bằng cơ chế **riêng của nó** — không proxy nào bị ép làm giống
proxy khác. Đây chính là thứ đang được đánh giá (proxy nào biểu đạt được mục tiêu tốt hơn, rẻ hơn,
ổn định hơn), không phải thứ cần đồng nhất.

**Đã loại khỏi vòng so sánh chính:** Bifrost Complexity Router (tự phân loại độ khó câu hỏi rồi
định tuyến theo tier) — mặc dù là tính năng có sẵn (không vi phạm phạm vi đề tài, xem CLAUDE.md
mục 1), nhưng LiteLLM/Portkey không có cơ chế tương đương, dùng sẽ làm lệch so sánh. Ghi nhận là
hạn chế/khác biệt trong báo cáo, không bật khi chạy Phase E.

## 2. Cách mỗi proxy biểu đạt mục tiêu — THIẾT KẾ CŨ (xem `docs/experiment-design.md` mục 4)

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

## 5. Phân tích dưới THIẾT KẾ CŨ (D2) — giữ làm bằng chứng vì sao phải đổi

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

**Hùng bổ sung (2026-10-09) — phân tích soạn cho buổi họp GVHD 2026-10-03, xem
`docs/meetings/2026-10-03.md`:**

7. **Chỉ 2/5 chỉ số trong luật quyết định thật sự phân biệt được proxy.** Dry-run xác nhận điểm 4:
   ở lượt bình thường cả 3 proxy gọi cùng `gpt-4o-mini`. Hệ quả cho từng chỉ số:

   | Chỉ số | Phân biệt được proxy? | Thật ra đang đo gì |
   |---|---|---|
   | `closed_qa_accuracy` | Không | **Model** — cùng model thì cùng độ chính xác |
   | `avg_cost` | Không | **Model** — cùng giá; chênh lệch chỉ là nhiễu độ dài câu trả lời (29–106 token ra) |
   | Điểm rubric (162 output) | Không | **Model** — cùng lý do |
   | `p95_latency_ms` | **Có** | **Proxy** — overhead mỗi proxy khác nhau thật (LiteLLM ~3681 ms vs ~2800 ms) |
   | `error_rate` | **Có** | **Proxy** — khác biệt lớn nhất khi có lỗi xảy ra |

   Nghĩa là bước 1 và bước 2 của luật quyết định (`closed_qa_accuracy` ≥ 80%, rồi `avg_cost` thấp
   nhất) hiện **không** chọn theo năng lực proxy. Nếu Phase E giữ nguyên điều kiện này, bước 2 sẽ
   chọn theo nhiễu và bước 3 (p95, ngưỡng hòa 5%) mới là bước quyết định thật.

8. **4 trục đánh giá, và chỉ 2 trục cần tới 270 lượt.** Tách rõ để báo cáo không nhập nhằng giữa
   "đo bằng số" và "kết luận bằng quan sát":

   | Trục | Đo bằng gì | Cần 270 lượt? |
   |---|---|---|
   | 1. **Năng lực biểu đạt** — proxy tự diễn đạt được chính sách tới đâu, hay phải ta khai tay | Quan sát khi cấu hình (mục 2 + 3 của tài liệu này) | Không — đã xong ở Phase C |
   | 2. **Overhead độ trễ** | `p95_latency_ms` | **Có** |
   | 3. **Hành vi khi lỗi** | `error_rate` + kịch bản ép lỗi | **Có** |
   | 4. **Chi phí vận hành** — cấu hình/theo dõi/sửa lỗi dễ hay khó | Kinh nghiệm triển khai thật | Không |

   Trục 1 và 4 là nơi 3 proxy khác nhau rõ nhất, nhưng **không** nằm trong luật quyết định (luật
   chỉ nhận chỉ số tự động hoá được). Phải nêu cả 4 trục trong báo cáo, đừng để người đọc hiểu
   rằng kết luận chỉ dựa trên 270 lượt.

9. **Kịch bản ép lỗi: thiết kế thế nào mới đo được điều muốn đo.**

   a. **Lượt ép lỗi mà proxy tự chuyển model và trả lời được thì vẫn là `status=success`.**
      `error_rate` đo *"người dùng có nhận được câu trả lời không"*, không đo *"có model nào bị lỗi
      không"* — nếu không thì proxy làm tốt việc dự phòng lại bị trừ điểm vì đã làm đúng việc của
      nó. Khớp D7: chỉ lượt lỗi **sau khi hết retry và hết chuỗi** mới tính là lỗi.

   b. **Ghi đúng sự thật về lượt ép lỗi Bifrost 2026-10-01** (sửa một cách hiểu sai đã từng xuất
      hiện khi trao đổi): chuỗi của Bifrost **đủ 5 model đúng thứ tự giá**
      (`application.yml` → `app.chat.proxy-fallback-chains.bifrost`), Gemini **đã** được đăng ký
      (`proxy-configs/bifrost/setup.sh` tự tạo provider) và **đã được thử đúng thứ tự** — nó lỗi
      tạm thời sau 2 lần retry nên Bifrost mới đi tiếp sang `claude-haiku`. **Không** phải vì chuỗi
      thiếu Gemini hay cấu hình sai thứ tự. Nguồn: `docs/tasks/2026-09-28/log-khoa.md` (K1, phát
      hiện 4) + `docs/bifrost-routing-notes.md` mục 8.

   c. **Ép lỗi 1 model là chưa đủ sắc.** Cả LiteLLM và Bifrost đều nhắm model rẻ nhất còn sống, nên
      khi chỉ `gpt-4o-mini` chết thì cả hai cùng rơi về `gemini-flash` → chi phí lại bằng nhau, y
      như lúc không lỗi. Phải ép lỗi **2 model** (`gpt-4o-mini` **và** `gemini-flash`):

      - **LiteLLM** còn 3 deployment sống trong `conduit-pool` → tự đi tiếp, ta không khai gì thêm.
        ⚠️ **Chưa ai thử** — đừng giả định `conduit-pool` tự fallback (`log-khoa.md` phát hiện 8).
      - **Bifrost** sống được bao xa tùy chuỗi dài bao nhiêu — muốn sống hết phải tự tay liệt kê
        đủ 5 model (và hiện đã liệt kê đủ, xem 9b).
      - **Portkey** lỗi ngay từ bước đầu (rule 1-1, không có dự phòng — điểm 5).

      Phát biểu rút ra cho báo cáo: *"Bifrost đạt được kết quả y hệt LiteLLM, nhưng chỉ vì nhóm đã
      liệt kê sẵn cả 5 model bằng tay. Khác biệt không nằm ở kết quả, mà nằm ở lượng cấu hình phải
      viết và phải bảo trì mỗi khi pool model thay đổi."* → đây là bằng chứng cho trục 1 (điểm 8).

   d. **Cảnh báo đo lường:** Gemini free tier hay lỗi tạm (rủi ro đã ghi ở `roadmap.md` mục 7) và
      nó chính là **mắt xích thứ 2** của chuỗi. Nếu Gemini tự chết trong lúc chạy kịch bản ép lỗi
      thì không tách được *"proxy bỏ qua Gemini vì cấu hình sai thứ tự"* khỏi *"Gemini tự chết"* →
      phải kiểm tra độ ổn định Gemini **trước**, và ghi lại log của proxy (Bifrost `/api/logs` có
      `fallback_index`) để chứng minh thứ tự thật đã đi.

   e. **Phép thử bổ sung rất rẻ (3 lượt, ~$0.0001) cho trục 1 — "đổi giá, không chỉ ép lỗi":**
      giả lập nhà cung cấp hạ giá để model khác thành rẻ nhất, rồi gửi 1 lượt/proxy.

      | Proxy | Phải sửa ở đâu khi giá đổi |
      |---|---|
      | LiteLLM | Cập nhật bảng giá → **tự chọn lại**. 1 điểm sửa |
      | Bifrost | Cập nhật bảng giá, **rồi còn phải sửa thứ tự chuỗi**. 2 điểm sửa |
      | Portkey | Cập nhật bảng giá, **rồi còn phải sửa rule**. 2 điểm sửa |

      Rủi ro vận hành đo được: quên điểm sửa thứ hai thì Bifrost/Portkey **định tuyến sai mà không
      báo lỗi gì** — vẫn trả lời bình thường, chỉ là đắt hơn cần thiết.

## 6. Trạng thái cấu hình hiện tại (2026-09-30)

| Proxy | Cấu hình routing | Verify trực tiếp | Verify qua app thật (D3) |
|---|---|---|---|
| LiteLLM | ✅ `cost-based-routing`, D7 | ✅ 10/10 lượt (H1) | ✅ (`run_experiment.py`, H3) |
| Portkey | ✅ conditional, D7 | ✅ 3/3 lượt (H2) | ✅ (`e2e_workflow_test.sh`, 2026-09-30) |
| Bifrost | ✅ `fallbacks` đủ 5 model theo giá, D7 (2026-10-01) | ✅ chuỗi + ép lỗi | ✅ `e2e_workflow_test.sh` 43/43 + `run_experiment.py` 1 prompt + 1 lượt ép lỗi (2026-10-01) |

**Dry-run 27 lượt đã chạy 2026-10-02** (`dry_run.sh` đã sửa để LiteLLM dùng `conduit-pool`): 27/27
thành công và đúng, cả 3 proxy đều gọi `gpt-4o-mini` — đúng như mục 5 điểm 4 dự đoán, chênh lệch chi
phí giữa 3 proxy chỉ đến từ độ dài câu trả lời (số liệu: `docs/tasks/2026-09-28/log-khoa.md` phát
hiện 6). Còn mở: `decision_rule.py` tính lượt lỗi `cost = 0` vào chi phí trung bình (phần review
cuối `docs/tasks/2026-09-28/log-hung.md`, điểm 3) — dry-run không có lượt lỗi nên chưa ảnh hưởng.

## 7. Ngưỡng `metadata.prompt_len` cho Portkey (chốt 2026-10-14, H3 — **khóa trước khi chạy**)

Nhánh Portkey của Design Y định tuyến theo **độ dài prompt**, vì Portkey **không có** cơ chế tự
phân loại nào. Giới hạn kỹ thuật: điều kiện của Portkey chỉ khớp `metadata.*` / `params.*`, kiểu
nguyên thủy, khóa tối đa 2 đoạn — nên **không đọc được** `params.messages[0].content.length`.
**App phải tự tính độ dài rồi gửi kèm `metadata.prompt_len`** (việc K3 của Khoa). Bản thân điều đó
là một kết quả: **logic định tuyến của Portkey rò vào code ứng dụng**, LiteLLM/Bifrost thì không.

### Ngưỡng

| `metadata.prompt_len` (ký tự) | Tier | Model |
|---|---|---|
| `< 211` | rẻ | `gpt-4o-mini` |
| `211` – `384` | trung | `claude-haiku` |
| `>= 385` | đắt | `gpt-4o` |

Dùng `$lt` / `$gte`. Map tier → model **giống hệt Bifrost** để hai nhánh so được ngang hàng.

> ⚠️ **Tier đắt dùng `gpt-4o`, KHÔNG dùng `claude-sonnet` (đổi 2026-10-16).** `claude-sonnet-5`
> bật thinking mặc định và **nở phần suy nghĩ cho vừa hết `max_tokens` rồi trả về RỖNG** — đo
> trực tiếp qua Anthropic: `max_tokens 512` → 512 thinking token, `2048` → 2048 thinking token,
> cả hai lần `stop_reason=max_tokens`, text rỗng, **vẫn bị tính tiền đầy đủ** ($0.021 cho lượt
> 2048). Tăng ngân sách không cứu được. Nó còn **từ chối tham số `temperature`** (HTTP 400
> *"temperature is deprecated for this model"*) nên không áp được greedy decoding mà protocol
> `pass@1` yêu cầu. `gpt-4o` cũng thuộc **tầng đắt** của pool (CLAUDE.md mục 2) và không có cả
> hai vấn đề: `mmlu_01` → 1 token, trả đúng định dạng, `stop_reason=stop`.
>
> `claude-sonnet-5` đã bị bỏ khỏi **cả ba** đường định tuyến (CEL rule của Bifrost, condition của
> Portkey, `conduit-pool` của LiteLLM) — áp dụng như nhau nên vẫn công bằng. Ghi thành phát hiện
> + giới hạn trong báo cáo.

### Ngưỡng suy từ đâu

**Tercile của phân bố độ dài thật của chính 40 item** (`experiments/prompts/manifest.json`, seed
20261014):

| | min | p25 | median | p75 | max |
|---|---|---|---|---|---|
| cả 40 item | 93 | 190 | 315 | 500 | 1102 |

Kết quả chia: **13 rẻ / 13 trung / 14 đắt**.

**Vì sao dùng tercile chứ không phải số tròn tự đặt:** đặt số tròn theo cảm tính rất dễ dẫn tới một
tier nhận **0 item** → nhánh Portkey suy biến thành "luôn chọn 1 model" và không đo được gì.
Tercile đảm bảo cả 3 tier đều có lưu lượng.

**Đây là hiệu chỉnh trên ĐẦU VÀO, không phải trên đáp án** — chỉ dùng phân bố độ dài prompt, không
dùng nhãn độ khó hay đáp án đúng. Người vận hành thật cũng làm đúng việc này (xem phân bố độ dài
traffic rồi đặt ngưỡng). Vẫn phải khai báo trong báo cáo là ngưỡng suy từ chính bộ đề.

### Điểm yếu dự đoán trước — làm sắc thêm giả thuyết H3

Độ dài prompt **tương quan với *loại bài*, không với *độ khó***:

| Bộ | min | median | max | Xu hướng ở ngưỡng trên |
|---|---|---|---|---|
| mmlu | 170 | 445 | 1102 | trải cả 3 tier |
| gsm8k | 103 | 225 | 510 | **phần lớn rơi tier rẻ** |
| humaneval | 233 | 476 | 893 | **hầu như không bao giờ rẻ** |
| ifeval | 93 | 209 | 510 | **phần lớn rơi tier rẻ** |

Nghĩa là Portkey sẽ gần như **định tuyến theo bộ benchmark** chứ không theo độ khó: bài HumanEval đi
model trung/đắt, phần lớn GSM8K và IFEval đi model rẻ. Đây là **điểm yếu nội tại của heuristic do
người viết**, và chính là nội dung giả thuyết **H3** (`docs/experiment-design.md` mục 7). Phải nêu
trong báo cáo, **không** được trình bày như thể Portkey "định tuyến theo độ khó".
