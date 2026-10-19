# Kết quả thực nghiệm đánh giá 3 routing proxy (Phase 3)

**Ngày chạy:** 19/10/2026 · **Dữ liệu:** 360/360 lượt gọi API thật, 0 lượt lỗi
**Bài toán, biến, giả thuyết, giới hạn:** xem `docs/experiment-design.md` (file này chỉ báo cáo số).
**Người chạy:** Hùng 180 lượt (MMLU + GSM8K), Khoa 180 lượt (HumanEval + IFEval).

---

## 1. Kết luận

> **Proxy được chọn để tích hợp vào Conduit: `litellm`.**
> Quyết định ở **bước 2** của luật 4 bước đã khóa (chi phí trung bình/prompt thấp nhất), **không**
> phải do dự phòng D13, **không** có hòa phải xét tiếp bước 3–4.

Cả 3 proxy đều **qua** cổng chất lượng 80% ở bước 1, nên bước 2 định đoạt. LiteLLM rẻ hơn Bifrost
**6,2 lần** và rẻ hơn Portkey **9,0 lần** — chênh lệch này lớn hơn ngưỡng 5% của bước 3 rất nhiều,
nên p95 latency và consistency rate **không được dùng tới**.

**Phải nói thẳng cái giá của lựa chọn này:** LiteLLM là proxy có **độ chính xác thấp nhất** (81,7%,
chỉ hơn cổng 80% đúng **1,7 điểm phần trăm**) và nó qua cổng **chỉ nhờ gộp đủ 4 bộ đề** — trên nửa
bộ đề của Hùng (MMLU + GSM8K) nó chỉ đạt **75,0% và sẽ bị loại**. Mục 7 phân tích rủi ro này.

---

## 2. Bảng tổng hợp — các chỉ số của luật quyết định

| Proxy | Đạt | Độ chính xác | Lỗi | Chi phí TB/lượt | Chi phí/câu đạt | p95 latency | Độ trễ TB | Nhất quán |
|---|---|---|---|---|---|---|---|---|
| `litellm` | 98/120 | **81,7%** | 0,0% | **$0,000097** | **$0,000119** | 5001 ms | 2230 ms | 1,00 |
| `bifrost` | 106/120 | 88,3% | 0,0% | $0,000601 | $0,000680 | 5629 ms | 2681 ms | 1,00 |
| `portkey` | 113/120 | **94,2%** | 0,0% | $0,000879 | $0,000933 | 5819 ms | **2168 ms** | 1,00 |

Chi phí tổng cả đợt: **$0,18920** (litellm $0,01167 = 6,2% · bifrost $0,07209 = 38,1% ·
portkey $0,10544 = 55,7%).

### Áp luật 4 bước, từng bước

| Bước | Luật | Kết quả |
|---|---|---|
| 1 | Loại proxy có độ chính xác < 80% | Không loại ai (81,7% / 88,3% / 94,2%) → còn cả 3 |
| 2 | Chọn chi phí TB/prompt thấp nhất | **`litellm` $0,000097** — thấp nhất → **CHỌN** |
| 3 | Nếu chênh chi phí < 5% thì xét p95 | **Không áp dụng** (chênh 518% và 803%) |
| 4 | Nếu vẫn hòa thì xét consistency | **Không áp dụng** |

---

## 3. Tỷ lệ model mỗi proxy đã chọn (bảng BẮT BUỘC)

Không có bảng này thì con số độ chính xác ở mục 2 vô nghĩa — nó đo **cả bó** (proxy + cơ chế định
tuyến + model được chọn), không đo riêng "proxy thông minh" (`docs/experiment-design.md` mục 6.2).

| Proxy | Model | Tầng | Số lượt | Tỷ lệ | Độ chính xác của riêng model đó |
|---|---|---|---|---|---|
| `litellm` | `gpt-4o-mini` | SIMPLE | 120 | **100%** | 82% |
| `bifrost` | `gpt-4o-mini` | SIMPLE | 69 | 57% | 84% |
| `bifrost` | `gpt-4o` | COMPLEX | 30 | 25% | 100% |
| `bifrost` | `claude-haiku` | MEDIUM | 21 | 18% | 86% |
| `portkey` | `gpt-4o` | COMPLEX | 42 | 35% | 90% |
| `portkey` | `claude-haiku` | MEDIUM | 39 | 32% | 100% |
| `portkey` | `gpt-4o-mini` | SIMPLE | 39 | 32% | 92% |

**LiteLLM `cost-based-routing` chọn `gpt-4o-mini` cho 120/120 lượt — không hề đổi model dù một lần.**
Đúng như dự đoán: nó xếp hạng theo **giá**, không có đầu vào chất lượng nào, nên prompt khó cỡ nào
cũng ra model rẻ nhất. Nghĩa là **nhánh LiteLLM trong thí nghiệm này thực chất đo `gpt-4o-mini`**,
chứ không đo một cơ chế định tuyến đang hoạt động.

---

## 4. Độ chính xác theo từng bộ benchmark

| Proxy | MMLU | GSM8K | HumanEval | IFEval | Tổng |
|---|---|---|---|---|---|
| `litellm` | 27/30 | **18/30** | 30/30 | 23/30 | 98/120 (81,7%) |
| `bifrost` | 27/30 | 24/30 | 30/30 | 25/30 | 106/120 (88,3%) |
| `portkey` | 27/30 | **30/30** | 29/30 | 27/30 | 113/120 (94,2%) |

Hai điều đọc ra ngay:

- **MMLU không phân biệt được 3 proxy** (27/30 cho cả ba) và **HumanEval gần như bão hòa** (30/30,
  30/30, 29/30). Toàn bộ khác biệt giữa 3 proxy đến từ **GSM8K** (18 → 24 → 30) và **IFEval**
  (23 → 25 → 27).
- Bifrost đẩy **24/30 câu MMLU lên tầng COMPLEX** (`gpt-4o`, model đắt nhất pool) nhưng vẫn chỉ được
  **27/30 — bằng đúng LiteLLM chạy toàn bộ bằng `gpt-4o-mini`**. Tiền trả thêm cho MMLU **không mua
  được điểm nào**. Đây là xác nhận thực nghiệm cho phân loại lệch đã đo ở smoke test 09/10.

---

## 5. Cơ chế: vì sao độ chính xác chênh nhau

GSM8K là chỗ 3 proxy tách nhau rõ nhất, và quan hệ nhân quả ở đây **sạch**:

| Item | `prompt_len` | litellm (mini) | bifrost | portkey |
|---|---|---|---|---|
| gsm8k_05 | 277 | SIMPLE **0/3** | SIMPLE **0/3** | MEDIUM **3/3** |
| gsm8k_07 | 340 | SIMPLE **0/3** | MEDIUM **3/3** | MEDIUM **3/3** |
| gsm8k_09 | 225 | SIMPLE **0/3** | SIMPLE **0/3** | MEDIUM **3/3** |
| gsm8k_10 | 510 | SIMPLE **0/3** | MEDIUM **3/3** | COMPLEX **3/3** |

Bốn câu `gpt-4o-mini` làm sai thì nó sai **0/3 — tất định**, không phải nhiễu. Và **mỗi lần** proxy
nâng lên model mạnh hơn thì câu đó **đạt 3/3**. Tức là chênh lệch độ chính xác ở mục 2 **không** do
may rủi, mà **toàn bộ** do quyết định định tuyến: Portkey nâng cả 4/4 câu → 30/30; Bifrost nâng 2/4 →
24/30; LiteLLM nâng 0/4 → 18/30.

**Nhưng Portkey nâng đúng 4 câu đó không phải vì nó "hiểu" câu khó.** Nó định tuyến theo **độ dài
prompt**, ngưỡng do **nhóm tự đặt** (<211 ký tự → rẻ, ≥385 → đắt; suy từ tercile phân bố độ dài 40
item, khóa 14/10). Cả 4 câu mini trượt đều dài **≥ 225 ký tự**, còn mọi câu mini làm được mà Portkey
để ở SIMPLE đều **≤ 177 ký tự**. Trên bộ GSM8K, **độ dài câu đố chữ tình cờ tỷ lệ với độ khó số
học** — nên một ngưỡng độ dài thuần cú pháp lại hoạt động như một bộ phân loại độ khó. Đó là **sự
trùng hợp có lợi trên bộ đề này**, không phải năng lực của Portkey, và **không có gì bảo đảm nó còn
đúng trên dữ liệu người dùng thật của Conduit**.

---

## 6. Chỉ số diễn giải: chi phí trên mỗi câu trả lời đạt

Chỉ số này gộp cả hai vế mục tiêu ("đạt yêu cầu" + "chi phí thấp") vào một số, nên nó là phép thử
xem kết luận ở mục 2 có phải là hệ quả của một luật đo lệch hay không:

| Proxy | Chi phí/câu đạt | So với litellm |
|---|---|---|
| `litellm` | **$0,000119** | — |
| `bifrost` | $0,000680 | đắt gấp **5,7×** |
| `portkey` | $0,000933 | đắt gấp **7,8×** |

**Hai cách tính cho cùng một kết luận.** Luật 4 bước và chỉ số diễn giải **không lệch nhau**, nên
không có chỗ nào phải giải trình thêm: ngay cả khi tính giá cho từng *câu đúng* (tức là đã phạt
LiteLLM vì 22 câu nó làm sai), LiteLLM vẫn rẻ nhất một khoảng rất lớn. Độ chính xác cao hơn của
Portkey **không bù được** chi phí cao hơn.

---

## 7. Đối chiếu 3 giả thuyết đã đăng ký trước

Ba giả thuyết này viết **trước khi** chạy (`docs/experiment-design.md` mục 7), ghi lại đúng nguyên
văn để báo cáo không bị nghi là giải thích sau khi đã thấy số.

| | Giả thuyết | Kết quả | Phán định |
|---|---|---|---|
| **H1** | LiteLLM: chi phí/lượt **thấp nhất**, độ chính xác **thấp nhất**, **ứng viên dễ trượt cổng 80%** | Rẻ nhất ✅ (6–9×) · thấp nhất ✅ (81,7%) · **nhưng vẫn qua cổng** | **Đúng 2/3** |
| **H2** | Bifrost: chính xác hơn LiteLLM ở câu khó nhưng đắt hơn đáng kể; p95 cao hơn ~257 ms; **sẽ xếp sai câu trắc nghiệm tầm thường lên COMPLEX** | Chính xác hơn ✅ (88,3 > 81,7) · đắt hơn 6,2× ✅ · p95 cao hơn **nhưng +628 ms** chứ không phải ~257 ms ⚠️ · **xếp 24/30 câu MMLU lên COMPLEX mà điểm không tăng** ✅ | **Đúng 3/4, 1 lệch độ lớn** |
| **H3** | Portkey: **nằm giữa**; kết quả **phụ thuộc ngưỡng `prompt_len` nhóm đặt** | **Không nằm giữa** ❌ — nó **chính xác nhất (94,2%) và đắt nhất** · phụ thuộc ngưỡng ✅ (mục 5 chứng minh trực tiếp) | **Đúng 1/2** |

### Về chỗ lệch của H2: p95 cao hơn 628 ms, không phải 257 ms

Con số ~257 ms đo ở smoke test 09/10 là **chi phí riêng của lượt embedding** (bật/tắt analyzer trên
cùng một model). Còn +628 ms ở đây là **hiệu p95 giữa hai proxy**, trong đó Bifrost còn gửi 43% lượt
sang `claude-haiku`/`gpt-4o` — vốn chậm hơn `gpt-4o-mini`. Hai con số **không đo cùng một thứ**, nên
chỗ lệch này **không** phủ định phép đo cũ; nhưng cũng **không** dùng nó làm bằng chứng cho "overhead
của Bifrost là 628 ms" được. Muốn tách bạch thì phải chạy cùng một model qua cả hai proxy — ngoài
phạm vi đợt này.

### H1 sai ở đâu, và vì sao chỗ sai đó đáng lo

H1 đoán LiteLLM sẽ trượt cổng 80%. Nó **không trượt — nhưng chỉ vừa đủ, và chỉ nhờ cách gộp bộ đề**:

| Nửa bộ đề | Độ chính xác LiteLLM | Qua cổng 80%? |
|---|---|---|
| MMLU + GSM8K (Hùng) | **75,0%** | **KHÔNG** |
| HumanEval + IFEval (Khoa) | 88,3% | Có |
| **Gộp cả 4 bộ** | **81,7%** | **Có (hơn 1,7 đpt)** |

Nguyên nhân: **HumanEval bão hòa** — `gpt-4o-mini` đạt 30/30, kéo điểm trung bình của LiteLLM lên.
Nếu bỏ HumanEval khỏi bộ đánh giá, LiteLLM còn 68/90 = **75,6%** và **bị loại ở bước 1**, khi đó
proxy được chọn sẽ là **`bifrost`** (rẻ hơn Portkey). Nghĩa là **kết luận của thí nghiệm này nhạy
với thành phần bộ đề** — phải ghi vào giới hạn, không được che. Luật quyết định **không được sửa sau
khi đã thấy số**, nên kết luận chính thức vẫn là LiteLLM; nhưng đây là lý do mục 9 đề nghị
**giữ cơ chế dự phòng** thay vì coi LiteLLM là lựa chọn an toàn tuyệt đối.

---

## 8. Độ tin cậy của phép đo

| | Kết quả |
|---|---|
| Lượt lỗi (`usage_logs.status=error`) | **0/360 (0,0%)** cả 3 proxy |
| Consistency rate (chọn **cùng model** qua 3 lần lặp) | **1,00** cả 3 proxy — định tuyến **tất định** |
| Sàn nhiễu (đáp án **đổi** giữa 3 lần lặp, dù `temperature=0`) | **3/120 nhóm = 2,5%** |

Ba nhóm đổi đáp án: `bifrost/ifeval_05` (1/3), `litellm/ifeval_07` (2/3), `portkey/humaneval_08`
(2/3). Cả ba đều dùng **đúng một model** trong cả 3 lần lặp, nên đây **không** phải định tuyến bất
ổn mà là **tính bất định phía provider** (`temperature=0` chỉ là "nỗ lực tối đa", không bảo đảm).
Hệ quả: mọi chênh lệch **nhỏ hơn ~2,5 điểm phần trăm** giữa 2 proxy thì **không kết luận được**.
Khoảng cách litellm↔bifrost (6,6 đpt) và bifrost↔portkey (5,9 đpt) đều **lớn hơn** sàn này nên vẫn
đọc được; nhưng khoảng cách **1,7 đpt** giữa LiteLLM và cổng 80% thì **nằm trong sàn nhiễu** — xem
mục 7.

Bản chấm được **tái lập độc lập**: Hùng chấm lại toàn bộ 180 lượt của Khoa trên máy mình bằng bản
`graders.py` mới nhất (sau 2 bản sửa ở commit `871e756`) và ra **đúng từng con số** Khoa báo
(88,3% / 91,7% / 93,3%); khác biệt duy nhất trong file là đường dẫn thư mục tạm của 2 máy.

---

## 9. Giới hạn (bổ sung cho `docs/experiment-design.md` mục 9)

1. **Kết luận nhạy với thành phần bộ đề.** Bỏ HumanEval thì LiteLLM bị loại và proxy được chọn đổi
   thành Bifrost (mục 7). 10 item/bộ là cỡ mẫu nhỏ.
2. **Nhánh LiteLLM không đo được cơ chế định tuyến** vì nó chọn cùng một model 120/120 lượt — nhánh
   này thực chất là **đường cơ sở `gpt-4o-mini`**. Đó là một kết quả, nhưng nó làm so sánh "3 cơ chế
   định tuyến" trở thành so sánh "1 model cố định vs 2 cơ chế".
3. **Lợi thế của Portkey một phần là trùng hợp** giữa độ dài prompt và độ khó trên GSM8K (mục 5), và
   ngưỡng là do nhóm đặt — không chuyển giao được sang dữ liệu thật.
4. **Chưa đo ở tải cao.** 360 lượt chạy tuần tự, không đo hành vi khi nghẽn hay khi provider sập —
   mà **failover** lại chính là thứ Bifrost mạnh nhất. Chọn LiteLLM theo chi phí ở tải thấp
   **không** chứng minh nó bền hơn khi có sự cố.
5. **0 lượt lỗi trong cả đợt** nghĩa là nhánh dự phòng/retry của **cả 3 proxy chưa hề được kích
   hoạt** — `error_rate` bằng nhau ở 0% là do không có sự cố nào, không phải do cả 3 chống lỗi tốt
   như nhau.

### Đề nghị cho phần tích hợp vào Conduit

Chọn `litellm` theo đúng luật, **nhưng** không bỏ cơ chế dự phòng: vì (a) LiteLLM qua cổng chỉ 1,7
đpt — nằm trong sàn nhiễu, (b) nó không đổi model bao giờ nên không tự nâng cấp khi gặp prompt khó,
và (c) giới hạn 4–5 ở trên. Cụ thể nên cấu hình `fallbacks` cho `conduit-pool` (hiện log còn báo
`Available Model Group Fallbacks=None`) — việc này trước đây **cố ý** chưa làm để không ảnh hưởng
tính công bằng của thí nghiệm, giờ thí nghiệm đã xong thì làm được.

---

## 10. Tái lập kết quả

Dữ liệu thô (360 lượt, đã chấm) và bảng đã xuất đều trong repo — **không cần gọi lại API**:

```
experiments/results/run_{litellm,bifrost,portkey}_20261019T13*.json   # 180 lượt Khoa (HumanEval + IFEval)
experiments/results/run_{litellm,bifrost,portkey}_20261019T16*.json   # 180 lượt Hùng (MMLU + GSM8K)
experiments/results/phase3-full-360/merged.json                       # 360 lượt đã gộp
experiments/results/phase3-full-360/tables/*.csv                      # 4 bảng CSV
```

```bash
# chấm lại (offline, miễn phí) -> gộp -> xuất bảng -> áp luật quyết định
PYTHONIOENCODING=utf-8 python experiments/scripts/grade_results.py experiments/results/run_*_20261019T1*.json
PYTHONIOENCODING=utf-8 python experiments/scripts/verify_results.py experiments/results/phase3-full-360/merged.json --expect 360
PYTHONIOENCODING=utf-8 python experiments/analysis/export_tables.py experiments/results/phase3-full-360/merged.json -o experiments/results/phase3-full-360/tables
PYTHONIOENCODING=utf-8 python experiments/analysis/decision_rule.py experiments/results/phase3-full-360/merged.json
```

Tham số cố định cả 3 proxy: `max_tokens=1024` · `temperature=0` · `num_retries=2` · `timeout=45s` ·
0-shot · pool 4 model thực dùng (`gpt-4o-mini` / `claude-haiku` / `gpt-4o`; `claude-sonnet` bị loại
theo D12, `gemini-flash` không nằm trong nhánh nào) · seed lấy mẫu `20261014`.
