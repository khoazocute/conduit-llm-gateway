# Thiết kế thí nghiệm đánh giá 3 proxy (Design Y)

**Chốt 2026-10-14.** Đây là **nguồn đúng** cho bài toán thực nghiệm. Đọc file này là đủ hiểu đề bài —
không cần đọc lại lịch sử chat.

Thay thế cách đặt vấn đề cũ trong `docs/routing-policy.md` mục 1–2 (file đó vẫn giữ: **mục 5 của nó
là bằng chứng *vì sao* phải đổi**, đã gắn nhãn "thiết kế cũ").

---

## 1. Vấn đề của thiết kế cũ, và nguyên nhân thật

Dry-run 2026-10-02 (27 lượt API thật): **cả 3 proxy đều gọi `gpt-4o-mini`**, token vào y hệt nhau
(20.7), chênh lệch chi phí chỉ đến từ độ dài câu trả lời dao động ngẫu nhiên.

| Proxy | Model đã chọn | Token vào TB | Chi phí TB/lượt | p95 latency |
|---|---|---|---|---|
| litellm | `gpt-4o-mini` | 20.7 | $4.06e-05 | ~3681 ms |
| portkey | `gpt-4o-mini` | 20.7 | $4.62e-05 | ~2868 ms |
| bifrost | `gpt-4o-mini` | 20.7 | $4.99e-05 | ~2768 ms |

Hệ quả: **3/5 chỉ số trong luật quyết định đo *model* chứ không đo *proxy***
(`closed_qa_accuracy`, `avg_cost`, điểm rubric). Chỉ `p95_latency_ms` và `error_rate` đo proxy thật.

### Nguyên nhân là D2, KHÔNG phải bộ đề dễ

Đây là chỗ dễ chẩn đoán sai, phải ghi rõ:

1. Dry-run **chỉ chạy 3 câu** (`--limit 3`). 27 câu còn lại trong bộ 30 **chưa ai chạy**. Nên kết
   luận "bộ 30 câu quá dễ" là suy rộng từ 3 câu.
2. Quan trọng hơn: **D2 ép cả 3 proxy diễn đạt *cùng một* chính sách** ("ưu tiên model rẻ nhất, có
   dự phòng khi lỗi"). Khi cả 3 thực thi **đúng** cùng một chính sách thì tất yếu chọn cùng 1 model.
   Hội tụ là **hệ quả logic của D2**, không phải lỗi đo lường.
3. `cost-based-routing` của LiteLLM **không có đầu vào chất lượng nào** — nó chỉ đọc bảng giá. Prompt
   khó cỡ nào nó vẫn chọn model rẻ nhất.

→ **Đổi bộ đề không giải quyết được hội tụ.** Phải đổi chính sách.

---

## 2. Câu hỏi nghiên cứu (mới)

> Với **cùng một mục tiêu định tuyến** — *trả lời đạt yêu cầu, chi phí thấp nhất* — **cùng pool 5
> model**, **cùng bộ đề** và **cùng điều kiện vận hành**: trong ba proxy LiteLLM / Bifrost / Portkey,
> proxy nào cho **chi phí thấp nhất trên mỗi câu trả lời đạt**, và cái giá phải trả về **độ trễ** và
> **công cấu hình** là gì?

Khác câu hỏi cũ ở chỗ nào: câu cũ hỏi *"proxy nào định tuyến tốt hơn"* nhưng lại ép cả 3 làm **cùng
một việc** → tất yếu hòa. Câu mới hỏi *"mỗi proxy làm hết sức nó thì được gì, mất gì"*.

Khớp mục tiêu thầy nêu ở buổi họp 2026-10-03: *"đáp ứng được yêu cầu, tối ưu về chi phí"* — một phát
biểu về **đánh đổi**, chỉ có nội dung khi 3 proxy chọn model khác nhau. Và khớp lời thầy đã ghi ở D3:
*"áp dụng proxy đó cho dự án của em và đánh giá cái nào chạy ok nhất"*.

---

## 3. Biến

| Loại | Nội dung |
|---|---|
| **Độc lập** (thứ đang nghiên cứu) | Cơ chế định tuyến mà mỗi proxy **diễn đạt được ở bản OSS của nó** |
| **Phụ thuộc** (thứ đo) | accuracy / pass@1 theo metric chuẩn · chi phí/lượt · **chi phí/câu đạt** · p95 latency · error_rate |
| **Kiểm soát** (giữ y hệt) | pool 5 model · 40 item · 0-shot · 3 lần lặp · `num_retries=2` · `timeout=45s` · `max_tokens=512` · cùng testbed Conduit (D3) |

**Phòng ngự trước phản biện "mỗi proxy làm việc khác nhau thì so sánh sao công bằng":** vẫn kiểm soát
chung pool model, bộ đề, giới hạn token, timeout, retry, và cùng đi qua app Conduit thật. Thứ **duy
nhất** thay đổi là cơ chế mỗi proxy diễn đạt được — **đó là biến độc lập của thí nghiệm, không phải
nhiễu.**

---

## 4. Ba nhánh

| Proxy | Cơ chế | Version | Ai ra quyết định | Overhead đã đo | Logic rò vào app? |
|---|---|---|---|---|---|
| **LiteLLM** | `cost-based-routing` trên `conduit-pool` | **v1.83.14-stable** (pin giữ nguyên) | Proxy — theo **giá** | ~0 | Không |
| **Bifrost** | Complexity Router + 3 CEL rule | **v2.1.1** | Proxy — theo **độ khó** | **~257 ms/request** | Không |
| **Portkey** | `conditional` trên `metadata.prompt_len` | hiện tại | **Người + app** | ~0 | **Có** |

Ba hành vi khác nhau thật và dự đoán được trước:

- **LiteLLM** tối ưu chi phí một cách "mù" — luôn rẻ nhất, không xét chất lượng.
- **Bifrost** thích ứng theo độ khó **ở thời điểm chạy** (nhưng phân loại lệch, xem mục 7).
- **Portkey** xấp xỉ bằng một heuristic **tĩnh do nhóm viết**, và **buộc app phải tính và gửi**
  `metadata.prompt_len` — Portkey không tự đọc được độ dài prompt. Đó là một kết quả: **logic định
  tuyến của Portkey rò vào code ứng dụng**, hai proxy kia thì không.

### 4.1. Tại sao LiteLLM không dùng cơ chế theo độ khó

LiteLLM **có** Auto Router v2 (`auto_router/complexity_router`) nhưng nhóm **đã thử và bỏ** — xem
mục 7.2. Lý do chính: nó cần **≥ v1.94**, tức phải bỏ pin `v1.83.14-stable` vốn được pin vì **lý do
bảo mật** (supply chain attack ở v1.82.7/v1.82.8, `CLAUDE.md` mục 2). Đổi pin bảo mật lấy một feature
là nước lỗ.

---

## 5. Bộ đánh giá — 4 bộ, 0-shot

Theo yêu cầu "dùng bộ prompt uy tín từ research, bộ đánh giá cũng phải uy tín, dùng metric chuẩn":

| Bộ | Đo gì | Metric chuẩn | Số item |
|---|---|---|---|
| **MMLU** | kiến thức học thuật, trắc nghiệm | accuracy | 10 |
| **GSM8K** | toán đố nhiều bước | exact match đáp án số | 10 |
| **HumanEval** | sinh code | **pass@1** (chạy test thật, temperature 0) | 10 |
| **IFEval** | làm theo chỉ thị, sinh văn bản mở | tỷ lệ ràng buộc kiểm được bằng code | 10 |

**Tổng: 40 item × 3 proxy × 3 lần = 360 lượt.** (Thay con số "30 prompt / 270 lượt" trong thiết kế cũ.)

### 5.1. Đã loại MT-Bench

Metric chuẩn của MT-Bench là **GPT-4 làm trọng tài** với prompt đã công bố. Phương án *"lấy prompt
MT-Bench rồi chấm bằng rubric 3 tiêu chí của nhóm"* **không hợp lệ** theo yêu cầu chuẩn-theo-paper,
vì rubric đó nhóm tự đặt, không thuộc paper nào.

**IFEval thay vào:** vẫn là sinh văn bản mở, nhưng ràng buộc **kiểm được bằng code** ("viết đúng 3
đoạn", "không dùng chữ viết hoa"…) → có metric chuẩn tự động, **không cần trọng tài, không cần chấm tay**.

**Kéo theo:**
- **D4 giải quyết xong** — prompt code chấm `pass@1`, không dùng rubric.
- **D6 gần như không còn cần** — hết chấm tay thì không còn ~49 output chấm kép và không còn %
  agreement. Mất một điểm phương pháp, nhưng **bỏ được điểm chặn nhân lực lớn nhất** của Phase E.

### 5.2. Vì sao 0-shot (lệch khỏi protocol gốc)

Protocol chuẩn là **MMLU 5-shot** và **GSM8K 8-shot CoT**. Few-shot làm prompt **rất dài** → nhánh
Portkey định tuyến **theo độ dài prompt** sẽ đẩy **mọi** câu sang model đắt, bất kể dễ hay khó →
heuristic mất sạch ý nghĩa.

Nhóm **không cần** so sánh với điểm công bố của các model; chỉ cần so **giữa 3 proxy trên cùng bộ
đề**, nên nội bộ nhất quán là đủ. **Phải khai báo rõ trong báo cáo là đã lệch khỏi protocol gốc và vì sao.**

### 5.3. Phải ghi lại để tái lập

Với mỗi bộ: paper gốc · link dataset chính thức · **phiên bản/commit dataset** · split dùng (test
hay validation) · số item · **seed lấy mẫu** · template prompt · tham số decoding · giấy phép.
Ghi vào `docs/benchmark-survey.md`.

---

## 6. Luật quyết định — KHÔNG sửa

Luật 4 bước đã khóa trong `CLAUDE.md` mục 2, giữ **y nguyên cả ngưỡng 80%**:

1. Loại proxy có độ chính xác < 80%
2. Trong số còn lại, chọn proxy có **chi phí trung bình/prompt thấp nhất**
3. Nếu chênh lệch chi phí < 5%, ưu tiên **p95 latency** thấp hơn
4. Nếu vẫn hòa, ưu tiên **consistency rate** cao hơn qua 3 lần lặp

Luật này **vốn đúng** — nó chỉ vô nghĩa dưới D2. Dưới Design Y:

| Bước | Dưới D2 (hội tụ) | Dưới Design Y |
|---|---|---|
| 1. Loại <80% | Vô hiệu — cùng model nên cùng accuracy | **Cổng chất lượng có tác dụng thật.** LiteLLM chọn rẻ nhất một cách mù → chính nó dễ trượt |
| 2. Chi phí TB thấp nhất | Chọn theo nhiễu độ dài câu trả lời | **Phản ánh quyết định routing thật** |
| 3. p95 | Thực chất là bước quyết định | Tiêu chí phá hòa, đúng vai |
| 4. Consistency | Config tĩnh thắng hiển nhiên | Có nghĩa thật — phân loại độ khó có thể dao động |

Đúng công thức thầy phát biểu: *"đáp ứng được yêu cầu"* = bước 1, *"tối ưu về chi phí"* = bước 2.

**Tính hợp lệ của việc sửa thiết kế:** `CLAUDE.md` nói luật quyết định khóa trước khi chạy. **Phase E
chưa chạy.** Sửa **thí nghiệm** bây giờ, có lý do ghi lại, là hợp lệ; sửa **luật** sau khi đã thấy
kết quả thì mới là mất khách quan. Nhóm sửa thí nghiệm, **không sửa luật**.

### 6.1. Chỉ số diễn giải chính

**Chi phí trên mỗi câu trả lời đạt** = tổng chi phí / số câu đạt. *(Ý của Khoa.)* Nó gộp đúng hai vế
mục tiêu của thầy vào **một** con số và tự động phạt proxy rẻ-mà-sai.

Nó **chồng lên** bước 1–2 của luật và có thể cho kết quả khác (một proxy đạt 79% bị bước 1 loại
thẳng dù chi phí/câu đạt tốt nhất). Cách xử lý: **luật 4 bước là thủ tục chọn chính thức; chi phí/câu
đạt là chỉ số diễn giải.** Nếu hai thứ lệch nhau thì **nói thẳng chỗ lệch** — bản thân chỗ lệch là
một quan sát đáng viết.

### 6.2. Bắt buộc báo cáo kèm

**Bảng tỷ lệ model mà mỗi proxy đã chọn.** Không có bảng này thì con số accuracy vô nghĩa. Có nó thì
đọc được, ví dụ: *"Bifrost đẩy 40% câu sang `claude-sonnet`, đạt 95%, giá $0.0007/lượt; LiteLLM đẩy
100% sang `gpt-4o-mini`, đạt 82%, giá $0.00004/lượt."*

---

## 7. Giả thuyết đăng ký trước (khóa 2026-10-14, trước khi chạy)

Viết **trước** khi thấy số, để báo cáo không bị nghi là giải thích sau khi có kết quả. Suy từ dữ liệu
smoke test ở mục 8.

- **H1 — LiteLLM:** chi phí/lượt **thấp nhất**, accuracy **thấp nhất**; là **ứng viên dễ trượt cổng
  80%** vì không xét chất lượng.
- **H2 — Bifrost:** accuracy cao hơn LiteLLM ở câu khó nhưng **chi phí cao hơn đáng kể**; p95 cao hơn
  ~257 ms do lượt embedding; **sẽ xếp sai một phần câu trắc nghiệm tầm thường lên COMPLEX**.
- **H3 — Portkey:** nằm giữa, và kết quả **phụ thuộc ngưỡng `prompt_len` do nhóm đặt** → chứng minh
  "định tuyến thông minh" ở Portkey là **công của người, không của proxy**.

Khi có kết quả: đối chiếu từng giả thuyết, **khớp hay không khớp đều phải nói**.

---

## 8. Bằng chứng thử khả thi (đã chạy thật)

Dữ liệu thô: `experiments/results/bifrost-complexity-smoke-20261009/` và
`experiments/results/litellm-autorouter-smoke-20261014/`. Tổng **27 lượt API thật**, ~$0.038.

### 8.1. Bifrost Complexity Router — CHẠY ĐƯỢC, nhưng phân loại lệch

**Cấu hình:** `PUT /api/routing/complexity-analyzer-config` (⚠️ PUT **thay toàn bộ** — phải gửi lại
cả `keywords` + `tier_boundaries`) + `POST /api/routing/rules` map tier → model. **Không bị gate
Enterprise.** ⚠️ `priority` phải **duy nhất trong mỗi scope** — 3 rule cùng `priority: 5` → lỗi 500.

**Mặc định:** 150 câu mẫu (50/tier), **toàn tiếng Anh, miền DevOps** (*"How do we shard a live
database, keep rollback possible, and preserve read-your-writes?"*); `tier_boundaries` 0.2/0.4;
`min_similarity` = **0** (lấy câu mẫu gần nhất bất kể xa cỡ nào); câu mẫu được embed **một lần** rồi
cache → mỗi request chỉ tốn **1** lượt embedding cho câu người dùng.

**Kết quả** (10 lượt, tất cả `status=success`, `mechanism=semantic`, **không lượt nào bị bỏ qua**):

| Prompt | Bifrost | LiteLLM auto_router |
|---|---|---|
| Trắc nghiệm tầm thường (kiểu MMLU) | **COMPLEX** ❌ | SIMPLE ✅ |
| Toán đố (kiểu GSM8K) | SIMPLE (3/3) | SIMPLE (2/2) |
| Viết blog (kiểu MT-Bench) | MEDIUM | SIMPLE |
| Viết hàm số nguyên tố (kiểu HumanEval) | SIMPLE | MEDIUM |
| **Đối chứng dương: migrate live DB** | **COMPLEX** ✅ (2/2) | **MEDIUM** ⚠️ (2/2) |
| Tiếng Việt, câu dễ | SIMPLE ✅ | SIMPLE ✅ |
| Tiếng Việt, giải thích thuật toán + code | **SIMPLE** ❌ | **MEDIUM** ✅ |

- **Đối chứng dương đạt** ở Bifrost → cơ chế **thật sự phân biệt được**, không phải hỏng.
- **Tiếng Việt: dìm hết về SIMPLE.** `mechanism=semantic` chứ không phải `skipped` → nó *có* phân
  loại, chỉ luôn rơi đáy vì câu tiếng Việt nằm xa mọi câu mẫu tiếng Anh. **Sai trong im lặng** —
  không lỗi, không cảnh báo, câu trả lời vẫn bình thường.
- **Overhead ~257 ms/request** (trung vị; dải 246–353; lượt warmup đầu 642). Tắt analyzer thì còn
  **0.8–1.4 ms** → **toàn bộ overhead là lượt gọi embedding**, gấp ~200 lần overhead gốc của Bifrost.
- Phân loại **tất định** qua lượt lặp (3/3 và 2/2) → tốt cho bước 4 của luật quyết định.
- **Hạn chế đo lường:** `complexity_score` **không tồn tại** trong log v2.1.1 (tài liệu có nói tới)
  → không đo được độ tự tin, chỉ thấy tier rời rạc.

### 8.2. LiteLLM Auto Router — BỎ

Auto Router v2 có thật (`auto_router/complexity_router`, ship từ v1.94.x) và **chạy được** về chức
năng. Nhưng nó **bỏ qua giới hạn sinh token ở cả 3 đường cấu hình**, trên **cả 2 bản mới nhất**
(`v1.105.0` và `v1.106.0-rc.1`):

| Đặt giới hạn ở đâu | Token ra (xin 16) | `finish_reason` |
|---|---|---|
| `max_tokens` trong request | 627 | `stop` |
| `max_completion_tokens` trong request | 524 | `stop` |
| `max_tokens` ở mức deployment trong config | 520 | `stop` |
| **Đối chứng:** gọi thẳng `gpt-4o-mini` cùng container | **16** | `length` |

`finish_reason` là `stop` chứ không phải `length` → **phía gọi không có cách nào phát hiện** giới hạn
đã bị bỏ. Issue gửi upstream đã soạn: `docs/upstream-issues/litellm-autorouter-drops-max-tokens.md`.

⚠️ **Đính chính quan trọng, đừng ghi sai vào báo cáo:** `HttpProxyChatClient.complete()` hiện **không
gửi `max_tokens` bao giờ** (`HttpProxyChatClient.java:92-100`), nên D7 **chưa từng được thực thi** qua
đường đi của app. Lỗi này **chỉ cắn khi nhóm thực thi `max_tokens`**. Nó là **phát hiện phụ để báo
cáo, không phải căn cứ chính** để bỏ auto_router — căn cứ chính là pin bảo mật (mục 4.1).

**Phát hiện phụ 2:** LiteLLM **không expose tier** — không có trong response, không có trong log ở
mức mặc định (phải bật debug). Bifrost ghi sẵn `complexity_tier`/`complexity_mechanism`. Khác biệt về
khả năng quan sát, ảnh hưởng yêu cầu ghi `routing_decisions`.

**Hệ quả tích cực của việc bỏ:** không phải nâng LiteLLM, không phải dựng container riêng, và mất
luôn rủi ro "nâng bản làm hỏng cấu hình đang chạy".

---

## 9. Giới hạn — ghi từ đầu, không chờ bị hỏi

1. **Không tách được** *"proxy định tuyến thông minh"* khỏi *"model được chọn vốn tốt hơn"*. Cái được
   đo là **cả bó**: proxy + cơ chế nó diễn đạt được + model mix sinh ra. Và đó **chính là** thứ sẽ
   được tích hợp vào Conduit, nên bó đó là đối tượng đo hợp lý.
2. Bifrost chạy ở **150 câu mẫu mặc định**; nhóm **không** tự viết câu mẫu riêng — lý do: tránh tinh
   chỉnh bộ phân loại theo chính bộ test của mình. Không đo được năng lực Bifrost khi có câu mẫu riêng.
3. **Bộ đề tiếng Anh**, bắt buộc vì mục 8.1. Ràng buộc này **chỉ do Bifrost** (LiteLLM cost-based
   không đọc nội dung; Portkey chỉ đọc độ dài). Bộ 30 câu tiếng Việt (`docs/eval-prompts.md`) **đổi
   vai** thành **phép thử riêng cho chỗ nhạy ngôn ngữ** → cho phát biểu: *"complexity routing của
   Bifrost được hiệu chỉnh trên câu mẫu tiếng Anh; nhóm đo được mức suy giảm khi gặp tiếng Việt —
   quan trọng vì Conduit phục vụ người dùng Việt. Chọn Bifrost thì phải tự viết câu mẫu tiếng Việt,
   đó là công bảo trì thêm."*
4. **0-shot, lệch khỏi protocol gốc** — mục 5.2.
5. `complexity_score` không có ở Bifrost v2.1.1 → không báo được độ tự tin phân loại.
6. **Timeout 2 tầng:** D7 đặt 45s *mỗi lần thử* ở proxy, nhưng `HttpProxyChatClient.REQUEST_TIMEOUT`
   cũng cắt cả lượt ở 45s. Với `num_retries=2`, proxy có thể cần lâu hơn → backend bỏ cuộc trước.
   Áp dụng giống nhau cả 3 nên vẫn công bằng, nhưng phải ghi vào giới hạn.
7. **Quy mô mẫu:** 10 item/bộ → sai số của accuracy từng bộ còn lớn. Cộng dồn 40 item/proxy thì
   ngưỡng 80% ở bước 1 mới đọc được. Phải nêu khi diễn giải.

---

## 10. Việc phải làm để chạy được thiết kế này

Chi tiết + phân công: `docs/tasks/2026-10-12/tasks.md`.

| Hạng mục | Trạng thái |
|---|---|
| LiteLLM `cost-based-routing` | ✅ đã cấu hình + verify 10/10 lượt (H1) — **không đổi gì** |
| Bifrost: analyzer + 3 CEL rule map tier → model thật | ⬜ Khoa, Phase 1 |
| Bifrost: pin image `:latest` → `v2.1.1` | ⬜ Hùng, Phase 1 |
| Portkey: rule theo `metadata.prompt_len` | ⬜ Khoa, Phase 1 |
| Backend: gửi `metadata.prompt_len` + `max_tokens: 512` | ⬜ Khoa, Phase 1 |
| Backend: **sửa `resolveReturnedModel`** (`HttpProxyChatClient.java:151-157`) — nhánh Portkey đang trả thẳng alias đã gửi với lý do "Portkey là ánh xạ tĩnh 1:1"; **lý do đó không còn đúng** khi Portkey định tuyến động → sẽ **ghi sai model và sai giá** | ⬜ Khoa, Phase 1 — **bắt buộc** |
| Bộ 40 item (4 bộ, 0-shot, seed ghi lại) + sửa `validate_prompts.py` | ⬜ Hùng, Phase 1 |
| Ngưỡng `prompt_len`, suy từ phân bố thật, khóa trước khi chạy | ⬜ Hùng, Phase 1 |
| Bộ chấm 4 metric (dùng harness chính thức) | ⬜ Hùng, Phase 2 |
| `run_experiment.py`: 4 nhóm mới + **chuyển chấm sang offline** | ⬜ Hùng, Phase 2 |
| Dry-run 36 lượt trên thiết kế mới | ⬜ Khoa, Phase 2 |
| Chạy 360 lượt + chấm + `docs/experiment-results.md` | ⬜ cả hai, Phase 3 |

**Tier không cần ghi cột riêng** trong `routing_decisions`: map tier → model là **1:1** nên tier
**suy được từ `selected_model`**. Khỏi phải gọi `/api/logs` của Bifrost sau mỗi lượt.
