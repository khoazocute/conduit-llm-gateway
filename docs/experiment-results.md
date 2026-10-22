# Kết quả thực nghiệm đánh giá 3 routing proxy

**Dữ liệu chính thức: 720/720 lượt gọi API thật** (80 item × 3 proxy × 3 lần), chạy 19–20/10/2026.
**Bài toán, biến, giả thuyết, giới hạn:** xem `docs/experiment-design.md`. File này chỉ báo cáo số.
**Cỡ mẫu:** 20 item/bộ theo **D14** (mở rộng từ 10, đăng ký trước khi chạy — xem mục 7).
**Chi phí toàn bộ thí nghiệm: $0,35354.**

---

## 1. Kết luận

> **Proxy được chọn để tích hợp vào Conduit: `litellm`.**
> Quyết định ở **bước 2** của luật 4 bước đã khóa (chi phí trung bình/prompt thấp nhất), **không**
> dùng luật dự phòng D13, **không** có hòa phải xét bước 3–4.

Cả 3 proxy **qua** cổng chất lượng 80% ở bước 1, nên bước 2 định đoạt. LiteLLM rẻ hơn Bifrost
**4,55 lần** và rẻ hơn Portkey **6,43 lần** — vượt xa ngưỡng 5% của bước 3, nên p95 latency và
consistency rate **không được dùng tới**.

Kết luận này **vững qua mọi phép kiểm độ nhạy** đã làm (mục 7): cả 4 biến thể leave-one-out đều
chọn LiteLLM, và chỉ số "chi phí/câu đạt" cho cùng kết luận kể cả ở tình huống bất lợi nhất.

**Cái giá phải nói rõ:** LiteLLM là proxy có **độ chính xác thấp nhất** (83,8% so với 87,5% và
92,1%), và nó **không hề định tuyến** — chọn `gpt-4o-mini` cho **240/240 lượt** (mục 3).

---

## 2. Bảng tổng hợp — các chỉ số của luật quyết định

| Proxy | Đạt | Độ chính xác | Lỗi | Chi phí TB/lượt | Chi phí/câu đạt | p95 latency | Nhất quán |
|---|---|---|---|---|---|---|---|
| `litellm` | 201/240 | **83,8%** | 0,0% | **$0,0001233** | **$0,000147** | **6348 ms** | **1,00** |
| `bifrost` | 210/240 | 87,5% | 0,8% | $0,0005616 | $0,000636 | 7166 ms | 0,975 |
| `portkey` | 221/240 | **92,1%** | 0,0% | $0,0007929 | $0,000861 | 6887 ms | **1,00** |

### Áp luật 4 bước, từng bước

| Bước | Luật | Kết quả |
|---|---|---|
| 1 | Loại proxy có độ chính xác < 80% | Không loại ai (83,8% / 87,5% / 92,1%) → còn cả 3 |
| 2 | Chọn chi phí TB/prompt thấp nhất | **`litellm` $0,0001233** → **CHỌN** |
| 3 | Nếu chênh chi phí < 5% thì xét p95 | **Không áp dụng** (chênh 355% và 543%) |
| 4 | Nếu vẫn hòa thì xét consistency | **Không áp dụng** |

**Quy ước tính (D7), nhắc lại để đọc đúng bảng:** lượt lỗi **không** tính phí và **không** vào chi
phí trung bình (tính ở $0 sẽ thưởng cho proxy hay lỗi), nhưng **có** tính là 1 trong 3 lần lặp, **có**
vào độ trễ (người gọi vẫn phải chờ hết khoảng đó rồi mới nhận lỗi), và `error_rate` báo riêng.
Consistency coi lượt lỗi là **một lựa chọn riêng biệt** (quyết định của Khoa 03/10: lỗi tự nó là một
dạng mất nhất quán của quyết định routing, không phải trường hợp trung lập) — đó là lý do Bifrost
được 0,975 chứ không phải 1,00.

---

## 3. Tỷ lệ model mỗi proxy đã chọn (bảng BẮT BUỘC)

Không có bảng này thì con số độ chính xác ở mục 2 vô nghĩa — nó đo **cả bó** (proxy + cơ chế định
tuyến + model được chọn), không đo riêng "proxy thông minh" (`docs/experiment-design.md` mục 6.2).

| Proxy | Model | Tầng | Số lượt | Tỷ lệ | Độ chính xác của riêng model đó |
|---|---|---|---|---|---|
| `litellm` | `gpt-4o-mini` | SIMPLE | 240 | **100%** | 84% |
| `bifrost` | `gpt-4o-mini` | SIMPLE | 137 | 57% | 84% |
| `bifrost` | `gpt-4o` | COMPLEX | 57 | 24% | 100% |
| `bifrost` | `claude-haiku` | MEDIUM | 44 | 18% | 86% |
| `bifrost` | *(lượt lỗi)* | — | 2 | 1% | — |
| `portkey` | `claude-haiku` | MEDIUM | 102 | 42% | 94% |
| `portkey` | `gpt-4o-mini` | SIMPLE | 75 | 31% | 92% |
| `portkey` | `gpt-4o` | COMPLEX | 63 | 26% | 89% |

**LiteLLM `cost-based-routing` chọn `gpt-4o-mini` cho 240/240 lượt — không đổi model dù một lần.**
Nó xếp hạng theo **giá**, không có đầu vào chất lượng nào, nên prompt khó cỡ nào cũng ra model rẻ
nhất. Nghĩa là **nhánh LiteLLM trong thí nghiệm này thực chất là đường cơ sở `gpt-4o-mini`**, không
đo được một cơ chế định tuyến đang hoạt động. Đây là phát hiện quan trọng nhất của cả thí nghiệm và
nó **không phụ thuộc** vào cổng 80% hay cỡ mẫu.

---

## 4. Độ chính xác theo từng bộ benchmark

| Proxy | MMLU | GSM8K | HumanEval | IFEval | Tổng |
|---|---|---|---|---|---|
| `litellm` | 48/60 | **45/60** | 57/60 | 51/60 | 201/240 (83,8%) |
| `bifrost` | 54/60 | 51/60 | 57/60 | **48/60** | 210/240 (87,5%) |
| `portkey` | **57/60** | 54/60 | 56/60 | **54/60** | 221/240 (92,1%) |

- **GSM8K là chỗ phân biệt rõ nhất** (45 → 51 → 54) — cơ chế ở mục 5.
- **HumanEval gần bão hòa** (57/57/56): không phân biệt được 3 proxy, nhưng **kéo điểm trung bình
  của cả ba lên**, LiteLLM được lợi nhiều nhất vì nó yếu nhất ở các bộ khác.
- **IFEval là bộ duy nhất Bifrost thua LiteLLM** (48 so với 51) — và cũng là bộ Bifrost đắt nhất.

---

## 5. Cơ chế: vì sao độ chính xác chênh nhau

### Bifrost trả giá đắt nhất cho bộ dễ nhất

| Bifrost | SIMPLE | MEDIUM | COMPLEX |
|---|---|---|---|
| **MMLU** | 3 | 6 | **51** |
| GSM8K | 42 | 18 | — |
| HumanEval | 57 | 3 | — |
| IFEval | 35 | 17 | 6 |

Bifrost Complexity Router đẩy **51/60 lượt MMLU (85%) lên tầng COMPLEX** — `gpt-4o`, model đắt nhất
pool — để đổi lấy 54/60 so với 48/60 của LiteLLM chạy toàn `gpt-4o-mini`. Tức **6 câu đúng thêm, trả
giá model đắt nhất cho 85% một bộ trắc nghiệm 4 đáp án**. Đây là xác nhận thực nghiệm cho phân loại
lệch đã đo ở smoke test 09/10: nó coi câu trắc nghiệm ngắn là "phức tạp".

Ngược lại, HumanEval — bộ **thật sự** cần suy luận — thì Bifrost cho **57/60 lượt vào SIMPLE**.
Phân loại của nó gần như **ngược** với độ khó thật.

### Lợi thế của Portkey một phần là trùng hợp

Portkey định tuyến theo **độ dài prompt**, ngưỡng do **nhóm tự đặt** (<211 ký tự → rẻ, ≥385 → đắt;
suy từ tercile phân bố độ dài 40 item đầu, khóa 14/10 và **giữ nguyên** qua đợt mở rộng theo D14).

Trên GSM8K, **độ dài câu đố chữ tình cờ tỷ lệ với độ khó số học**, nên một ngưỡng độ dài thuần cú
pháp lại hoạt động như một bộ phân loại độ khó — ở 40 item đầu, **cả 4 câu `gpt-4o-mini` làm sai đều
dài ≥ 225 ký tự** còn mọi câu nó làm được mà Portkey để ở SIMPLE đều ≤ 177 ký tự. Đó là **sự trùng
hợp có lợi trên bộ đề này**, không phải năng lực của Portkey, và **không có gì bảo đảm còn đúng trên
dữ liệu người dùng thật của Conduit**.

Trên HumanEval, Portkey không cho **câu nào** vào SIMPLE (30 MEDIUM + 30 COMPLEX) vì prompt code vốn
dài — nên nó trả giá cao nhất ở bộ mà `gpt-4o-mini` vốn đã làm được 57/60.

---

## 6. Chỉ số diễn giải: chi phí trên mỗi câu trả lời đạt

Chỉ số này gộp cả hai vế mục tiêu ("đạt yêu cầu" + "chi phí thấp") vào một số, nên nó là phép thử xem
kết luận ở mục 2 có phải hệ quả của một luật đo lệch hay không.

| Proxy | Chi phí/câu đạt | So với litellm | Bất lợi nhất cho LiteLLM¹ |
|---|---|---|---|
| `litellm` | **$0,000147** | — | **$0,000163** |
| `bifrost` | $0,000636 | đắt gấp **4,3×** | $0,000588 |
| `portkey` | $0,000861 | đắt gấp **5,8×** | $0,000809 |

¹ Phép thử khắt khe nhất: đặt LiteLLM ở **đáy** khoảng tin cậy 95% của nó (độ chính xác thấp nhất có
thể) và hai proxy kia ở **đỉnh** khoảng tin cậy của chúng (cao nhất có thể).

**Kể cả trong tình huống bất lợi nhất đó, LiteLLM vẫn rẻ hơn 3,6× so với Bifrost và 5,0× so với
Portkey** trên mỗi câu trả lời đạt. **Hai cách tính cho cùng một kết luận**, nên không có chỗ nào
phải giải trình thêm: ngay cả khi đã phạt LiteLLM vì 39 câu nó làm sai, nó vẫn rẻ nhất một khoảng
lớn hơn sai số lấy mẫu rất nhiều. Độ chính xác cao hơn của Portkey **không bù được** chi phí.

---

## 7. Độ vững của kết luận

### 7.1. Ổn định khi tăng cỡ mẫu

| Cỡ mẫu | litellm | bifrost | portkey | Proxy được chọn |
|---|---|---|---|---|
| 360 lượt (40 item) | 81,7% | 88,3% | 94,2% | `litellm` |
| 540 lượt (60 item) | 81,1% | 88,9% | 92,8% | `litellm` |
| **720 lượt (80 item)** | **83,8%** | **87,5%** | **92,1%** | **`litellm`** |

Thứ tự 3 proxy **không đổi** qua cả ba mốc, và proxy được chọn **không đổi**. Biên của LiteLLM tới
cổng 80% **rộng ra** khi thêm dữ liệu: dư 2 lượt ở 360 → **dư 9 lượt** ở 720.

### 7.2. Leave-one-out: bỏ lần lượt từng bộ đề

| Bỏ bộ | litellm | bifrost | portkey | Proxy được chọn |
|---|---|---|---|---|
| — (cả 4 bộ) | 83,8% | 87,5% | 92,1% | **`litellm`** |
| MMLU | 85,0% | 86,7% | 91,1% | **`litellm`** |
| GSM8K | 86,7% | 88,3% | 92,8% | **`litellm`** |
| HumanEval | 80,0% | 85,0% | 91,7% | **`litellm`** |
| IFEval | 83,3% | 90,0% | 92,8% | **`litellm`** |

**Cả 4/4 biến thể đều chọn LiteLLM.** Đây là thay đổi quan trọng nhất mà đợt mở rộng mang lại: ở cỡ
mẫu 40 item, **2/4 biến thể đổi hẳn proxy được chọn** (bỏ MMLU → Bifrost, bỏ HumanEval → Portkey).
Ở 80 item, độ nhạy đó **biến mất**.

⚠️ Biến thể "bỏ HumanEval" cho LiteLLM **đúng 80,0%** — qua cổng vì luật là "loại nếu **< 80%**",
nhưng sát sàn. Phải ghi rõ, không làm tròn thành "an toàn".

### 7.3. Chỗ KHÔNG phân giải được: cổng 80% và cỡ mẫu

| Proxy | Độ chính xác | CI95 (theo 80 item) | Phân biệt được với ngưỡng 80%? |
|---|---|---|---|
| `litellm` | 83,8% | [75,7%; 91,8%] | **KHÔNG** — khoảng chứa 80% |
| `bifrost` | 87,5% | [80,3%; 94,7%] | Có |
| `portkey` | 92,1% | [86,2%; 98,0%] | Có |

Khoảng tin cậy lấy **item** làm đơn vị, vì 3 lần lặp trên cùng một item **không độc lập**.

**Nói thẳng:** với 80 item, **không khẳng định được** ở mức tin cậy 95% rằng độ chính xác thật của
LiteLLM ≥ 80%. Và **không thể chữa bằng cách chạy thêm**: để nửa-rộng của khoảng tin cậy xuống dưới
biên 3,8 đpt cần **~400 item ≈ 3.600 lượt**; để phân biệt được một biên 1 đpt cần **~5.000 item ≈
45.000 lượt** — ngoài tầm với ở mọi mức kinh phí của khóa luận.

Vì vậy báo cáo phải **tách rạch ròi hai phát biểu**:

- ✅ **"LiteLLM rẻ nhất trên mỗi câu trả lời đạt"** — **vững**, khoảng cách 3,6–5,0× lớn hơn sai số
  lấy mẫu rất nhiều, và không cần ngưỡng nào để phát biểu.
- ⚠️ **"LiteLLM đạt ≥ 80%"** — **không phân giải được** ở cỡ mẫu này. Điểm ước lượng (83,8%) nằm
  trên ngưỡng và cả 4 biến thể leave-one-out đều giữ nó, nhưng khoảng tin cậy vẫn phủ 80%.

### 7.4. Sàn nhiễu

`temperature=0` **không** cho kết quả lặp lại hoàn toàn (nó chỉ là "nỗ lực tối đa" phía provider).
Đo trên 720 lượt: **7/240 nhóm (proxy, item) đổi đáp án giữa 3 lần lặp = 2,92%**. Tách ra:

- **5/240 = 2,08%** là đổi đáp án thật: cùng một model, cả 3 lượt đều thành công, mà kết quả khác
  nhau → **bất định phía provider**, không phải định tuyến bất ổn.
- **2/240 = 0,83%** là do 2 lượt lỗi của Bifrost (mục 9), không phải đổi đáp án.

Hệ quả: chênh lệch **nhỏ hơn ~2,9 đpt** giữa 2 proxy thì không kết luận được. Các khoảng cách ở mục 2
— litellm↔bifrost 3,7 đpt và bifrost↔portkey 4,6 đpt — đều **lớn hơn** sàn này nên vẫn đọc được,
nhưng **không nhiều**: đây là lý do thứ tự *độ chính xác* giữa 3 proxy nên được phát biểu thận trọng,
trong khi thứ tự *chi phí* (4,6–6,4×) thì không có vấn đề gì.

**6 trong 7 ca rơi vào IFEval** (ca còn lại là HumanEval; MMLU và GSM8K **không có ca nào**). Hợp lý:
IFEval chấm theo ràng buộc định dạng ở mức *prompt-level strict* — đạt chỉ khi **mọi** ràng buộc đều
được tuân thủ — nên chỉ cần model lỡ một ràng buộc là cả item trượt, khiến nó nhạy hơn hẳn với dao
động nhỏ so với các bộ có đáp án đúng/sai rạch ròi. Đáng ghi vào phần giới hạn của bộ đánh giá.

### 7.5. Tái lập độc lập

Hùng chấm lại toàn bộ 180 lượt của Khoa trên máy mình bằng bản `graders.py` mới nhất và ra **đúng
từng con số** Khoa báo (88,3% / 91,7% / 93,3%); khác biệt duy nhất trong file là đường dẫn thư mục
tạm của hai máy. Phép chấm **tái lập được trên máy khác**.

---

### 7.6. Kết luận phụ thuộc vào ngưỡng chất lượng, và vì sao điều đó không phải thiên vị

**Câu hỏi dễ bị đặt ra:** "LiteLLM được chọn vì ngưỡng 80% đặt vừa đúng để nó qua?" Câu này đáng trả
lời bằng số, không bằng lời đảm bảo. Tính lại luật 4 bước (kể cả luật dự phòng khi không proxy nào
qua cổng) trên 720 lượt, với các mức ngưỡng khác nhau:

| Ngưỡng chất lượng (loại nếu thấp hơn) | Proxy qua cổng | Proxy được chọn |
|---|---|---|
| ≤ 83,75% (gồm cả 80%) | cả ba | **`litellm`** |
| trên 83,75% đến 87,5% | bifrost, portkey | `bifrost` |
| trên 87,5% đến 92,1% | chỉ portkey | `portkey` |
| trên 92,1% | không ai | `litellm` (luật dự phòng: rẻ nhất trên mỗi câu đúng) |

Tức là **kết luận đổi theo ngưỡng**: đặt yêu cầu 85% thì chọn Bifrost, đặt 90% thì chọn Portkey. Đây
là thuộc tính của luật đã khóa, không phải lỗi, nhưng phải nói rõ.

**Ngưỡng không được chọn theo kết quả.** Có thể kiểm chứng bằng lịch sử git:

- Luật 4 bước và ngưỡng 80% nằm trong **commit đầu tiên của repo, `9d6dfd7` (11/09/2026)**, ở cả
  `CLAUDE.md` lẫn `experiments/analysis/decision_rule.py` (`0.80`).
- Kết quả 720 lượt được commit ở `b55ed56` (20/10/2026), **hơn 5 tuần sau**. Ngưỡng ra đời trước cả
  bộ đề hiện tại (chốt 14/10) và trước cả thiết kế thí nghiệm hiện tại.
- Bộ chấm (`experiments/analysis/graders.py` và verifier IFEval vendored) **không đổi** từ commit
  `871e756` đến khi chấm xong 720 lượt, nên toàn bộ 720 lượt được chấm bằng một phiên bản duy nhất.
- Khi đứng trước khả năng ngưỡng 80% bất tiện, nhóm đã đăng ký trước luật dự phòng (D13) và ghi rõ
  *"không hạ ngưỡng 80%"* trước khi chạy Phase 3.

**Giới hạn của lập luận trên, nói thẳng:** ngưỡng 80% được đặt cho thiết kế cũ (bộ 30 prompt tự soạn)
rồi giữ nguyên khi chuyển sang 4 bộ benchmark chuẩn. Giữ nguyên là có chủ đích (đổi sau khi thấy số
mới là mất khách quan), nhưng **chưa có ai kiểm chứng rằng 80% là mức yêu cầu đúng cho người dùng của
Conduit**. Đó là câu hỏi về yêu cầu sản phẩm, không phải câu hỏi mà thí nghiệm này trả lời được.

**Cách diễn giải đúng của kết quả:** *"Với yêu cầu chất lượng 80%, mô hình rẻ nhất trong pool đã đủ
đạt, nên trả thêm tiền cho định tuyến thông minh là không đáng."* Muốn chất lượng cao hơn 83,75% thì
phải chấp nhận một proxy đắt hơn, và bảng trên cho biết đổi lấy proxy nào ở mỗi mức.

Một dữ kiện hỗ trợ cách diễn giải này, đo trên cùng 720 lượt (**lưu ý: không so sánh công bằng được**
giữa các model, vì mỗi proxy gửi những câu khác nhau cho từng model): `gpt-4o-mini` đạt 85,2%
(385/452 lượt), `claude-haiku` 91,8% (134/146), `gpt-4o` 94,2% (113/120).

## 8. Đối chiếu 3 giả thuyết đã đăng ký trước

Viết **trước khi** chạy (`docs/experiment-design.md` mục 7), giữ nguyên văn để báo cáo không bị nghi
là giải thích sau khi đã thấy số.

| | Giả thuyết | Kết quả trên 720 lượt | Phán định |
|---|---|---|---|
| **H1** | LiteLLM: chi phí/lượt **thấp nhất**, độ chính xác **thấp nhất**, **ứng viên dễ trượt cổng 80%** | Rẻ nhất ✅ (4,6–6,4×) · thấp nhất ✅ (83,8%) · **qua cổng với dư 9 lượt** ❌ | **Đúng 2/3** |
| **H2** | Bifrost: chính xác hơn LiteLLM ở câu khó nhưng đắt hơn đáng kể; p95 cao hơn ~257 ms; **sẽ xếp sai câu trắc nghiệm tầm thường lên COMPLEX** | Chính xác hơn ✅ (87,5 > 83,8) · đắt hơn 4,55× ✅ · p95 cao hơn **+818 ms** chứ không ~257 ms ⚠️ · **51/60 lượt MMLU lên COMPLEX** ✅ | **Đúng 3/4, 1 lệch độ lớn** |
| **H3** | Portkey: **nằm giữa**; kết quả **phụ thuộc ngưỡng `prompt_len` nhóm đặt** | **Không nằm giữa** ❌ — **chính xác nhất (92,1%) và đắt nhất** · phụ thuộc ngưỡng ✅ (mục 5 chứng minh trực tiếp) | **Đúng 1/2** |

### Về chỗ lệch của H2

Con số ~257 ms đo ở smoke test 09/10 là **chi phí riêng của lượt embedding** (bật/tắt analyzer trên
cùng một model). Còn +818 ms ở đây là **hiệu p95 giữa hai proxy**, trong đó Bifrost còn gửi 42% lượt
sang `claude-haiku`/`gpt-4o` — vốn chậm hơn `gpt-4o-mini` — và có 2 lượt lỗi tính vào độ trễ. Hai con
số **không đo cùng một thứ**; chỗ lệch này không phủ định phép đo cũ, nhưng cũng **không** dùng làm
bằng chứng cho "overhead của Bifrost là 818 ms" được.

---

## 9. Lượt lỗi

**2/720 lượt lỗi, cả hai của Bifrost** (`error_rate` 0,8%; LiteLLM và Portkey 0,0%):

| Item | Lần lặp | Độ trễ | Ghi chú |
|---|---|---|---|
| `ifeval_16` | run1 | 3.904 ms | run2, run3 **thành công và đạt** (`gpt-4o-mini`) |
| `ifeval_17` | run1 | 10.616 ms | run2, run3 **thành công và đạt** (`claude-haiku`) |

Không phải timeout (timeout cấu hình 45s). Cả hai rơi vào **run1 của hai item liền nhau**, ngay sau
khi backend restart sang `active-proxy=bifrost` — nghi là hiện tượng thoáng qua lúc khởi động, nhưng
**chưa xác định được nguyên nhân**: trường `error` trong record **rỗng**, không ghi lại được thông
điệp lỗi. Đây là **một khoảng trống logging cần sửa** trước khi dùng `error_rate` làm căn cứ cho bất
kỳ kết luận nào về độ bền.

---

## 10. Giới hạn

1. **Cổng 80% không phân giải được cho LiteLLM** ở cỡ mẫu này, và không chữa được bằng chạy thêm
   (mục 7.3). Đây là **thuộc tính của thiết kế** (độ chính xác thật của LiteLLM nằm gần ngưỡng), không
   phải thiếu sót thực thi.
2. **Nhánh LiteLLM không đo được cơ chế định tuyến** vì nó chọn cùng một model 240/240 lượt — nhánh
   này thực chất là **đường cơ sở `gpt-4o-mini`**. So sánh "3 cơ chế định tuyến" do đó thực tế là so
   sánh "1 model cố định vs 2 cơ chế".
3. **Lợi thế của Portkey một phần là trùng hợp** giữa độ dài prompt và độ khó trên GSM8K (mục 5), và
   ngưỡng do nhóm đặt — không chuyển giao được sang dữ liệu thật.
4. **Chưa đo ở tải cao.** 720 lượt chạy tuần tự; không đo hành vi khi nghẽn hay khi provider sập —
   mà **failover** lại chính là thứ Bifrost mạnh nhất. Chọn LiteLLM theo chi phí ở tải thấp **không**
   chứng minh nó bền hơn khi có sự cố.
5. **Chỉ 2 lượt lỗi trong cả đợt, và không rõ nguyên nhân** (mục 9) nghĩa là nhánh dự phòng/retry của
   cả 3 proxy **gần như chưa được kích hoạt**. `error_rate` ở đây **không** đủ để so sánh độ bền —
   đã bù bằng **phép thử tiêm lỗi (D15)** ngay dưới, và kết quả cho thấy thứ tự độ bền **ngược** với
   thứ tự chi phí.
6. **HumanEval gần bão hòa** nên đóng góp rất ít vào việc phân biệt 3 proxy, trong khi vẫn kéo điểm
   trung bình của cả ba lên.
7. **Bifrost chạy ở 150 câu mẫu mặc định** (tiếng Anh, miền DevOps); nhóm không tự viết câu mẫu riêng
   để tránh tinh chỉnh bộ phân loại theo chính bộ test của mình. Bộ đề **bắt buộc tiếng Anh** vì
   Bifrost dìm **mọi** prompt tiếng Việt về SIMPLE (đã đo) — ràng buộc này **chỉ do Bifrost**.
8. **0-shot, lệch khỏi protocol gốc** (MMLU chuẩn 5-shot, GSM8K 8-shot CoT), vì few-shot làm prompt
   rất dài và sẽ đẩy mọi câu của nhánh Portkey sang model đắt. Nhóm không so với điểm công bố, chỉ so
   **giữa 3 proxy trên cùng bộ đề**.

### Phép thử tiêm lỗi provider (D15) — đo cái giá của lựa chọn đã chốt

Giới hạn 4–5 ở trên là chỗ yếu thật của thí nghiệm chính: nó chạy ở điều kiện **không có sự cố**, tức
bỏ qua đúng thứ Bifrost mạnh nhất. Nên nhóm đo thêm một phép thử bổ sung, **đăng ký trước khi chạy**
(D15, `docs/roadmap.md` mục 4, commit `417b055`).

⚠️ **Phép thử này KHÔNG dùng để chọn lại proxy.** Luật 4 bước đã khóa, đã áp trên 720 lượt, kết luận
là `litellm` (mục 1). Đây là bằng chứng cho phần giới hạn — nói rõ **cái giá** của lựa chọn đó.

**Thiết kế:** một lỗi duy nhất — `OPENAI_API_KEY` không hợp lệ — tiêm **đồng thời** vào container
`litellm`, container `bifrost`, và **môi trường tiến trình backend** (Portkey OSS nhận cả config lẫn
key từ backend qua header `x-portkey-config`, không đọc env container nó). Key Anthropic và Gemini
**giữ hợp lệ**, nên proxy nào chuyển được sang `claude-haiku`/`gemini-flash` thì thành công. Item: 5
item GSM8K chọn theo luật *"id nhỏ nhất trong số 36 item mà **cả 3 proxy** đều chọn một model OpenAI
và nhất quán 3/3 lần ở 720 lượt"* → `gsm8k_01, 03, 06, 08, 12`, bảo đảm **phơi nhiễm lỗi bằng nhau**.
45 lượt, **$0,00971**.

| Proxy | Phục hồi | Model đã trả lời thay thế | Độ trễ khi phục hồi | Độ trễ khi thất bại |
|---|---|---|---|---|
| `litellm` | **0/15 (0%)** | — | — | **40.488 ms** |
| `bifrost` | **13/15 (87%)** | `claude-haiku` ×12, `gemini-flash` ×1 | **5.932 ms** | 45.046 ms (đụng timeout) |
| `portkey` | **0/15 (0%)** | — | — | **330 ms** |

**Đối chiếu 3 dự đoán đã đăng ký trước: 2 đúng, 1 SAI.**

- **P1 — LiteLLM phục hồi: SAI.** Nhóm dự đoán `conduit-pool` có 4 deployment trong cùng một model
  group nên router sẽ retry sang deployment khác. Thực tế **0/15**, và nó tiêu **40 giây** cho các
  lượt retry rồi vẫn thất bại — tức retry chỉ quay lại các deployment OpenAI, không hề sang
  Anthropic/Gemini. Đây là **chẩn đoán quan trọng nhất của phép thử**: `num_retries=2` ở mức model
  group **không** thay cho `fallbacks`, và nó biến sự cố provider thành **vừa không phục hồi vừa bắt
  người dùng chờ 40 giây** — xấu hơn cả thất bại nhanh.
- **P2 — Bifrost phục hồi: ĐÚNG**, 87%, chuyển sang `claude-haiku` trong ~6 giây. Hai lượt thất bại
  còn lại **không** phải lỗi định tuyến mà là **đụng đúng timeout 45s** (45.076 và 45.016 ms) trong
  lúc đang chuyển; lượt lặp thứ ba của chính item đó phục hồi được qua `gemini-flash` ở 24 giây. Tức
  cơ chế failover của Bifrost **có hoạt động**, chỉ đôi khi chậm hơn ngân sách thời gian đã đặt.
- **P3 — Portkey không phục hồi: ĐÚNG**, 0/15, nhưng nó **thất bại rất nhanh — 330 ms**. Cấu hình
  Design Y dùng `strategy.mode=conditional` với `retry.attempts: 2` trên từng target, **không có**
  `fallback` và **không có** `on_status_codes`, nên nó trả lỗi gần như tức thì thay vì thử provider
  khác.

**Đọc ra một đánh đổi mà thí nghiệm chính không thấy được:** ở điều kiện có sự cố, ba proxy rơi vào ba
chế độ khác nhau — Bifrost **phục hồi** (~6 s), Portkey **thất bại nhanh** (330 ms, trả quyền quyết
định lại cho ứng dụng), còn LiteLLM **thất bại chậm** (40 s, không phục hồi) — tức tệ nhất ở cả hai
chiều. Nói cách khác: **proxy được chọn vì rẻ nhất lại là proxy xử lý sự cố kém nhất trong cấu hình đã
đánh giá.** Điều này **không** đảo kết luận (luật đã khóa, và chi phí ở điều kiện bình thường chênh
4,5–6,4×), nhưng nó biến đề nghị "giữ `fallbacks`" ở dưới từ một lời khuyên thận trọng thành một
**yêu cầu đã được kiểm chứng bằng số**.

**Phép thử cũng xác nhận lại khoảng trống logging ở mục 9 một cách độc lập:** **0/32** lượt lỗi ghi
được bất kỳ thông điệp lỗi nào. Hai lần quan sát riêng biệt cùng chỉ vào một chỗ.

**Giới hạn của chính phép thử này** (đăng ký trước, không phải thêm sau khi thấy số):

1. Đây là **lỗi xác thực (401)**, không phải 5xx hay mất kết nối. Một proxy có thể **cố ý** không
   failover khi gặp 401 vì retry một key sai là vô nghĩa — nên kết quả **không** suy ra được hành vi
   khi provider sập thật.
2. Phép thử đo **đúng những cấu hình đã đánh giá**, không đo **trần năng lực** của 3 proxy. Portkey
   OSS *có* hỗ trợ `strategy: fallback`; nhóm không cấu hình vì Design Y dùng `conditional` để biểu
   đạt chính sách định tuyến. LiteLLM cũng *có* `fallbacks`; nhóm **cố ý** chưa bật để không ảnh hưởng
   tính công bằng của thí nghiệm chính.
3. **5 item là cỡ rất nhỏ** — chỉ đủ phân biệt "có/không phục hồi", **không** đủ so sánh định lượng
   thời gian phục hồi.

### Đề nghị cho phần tích hợp vào Conduit

Chọn `litellm` theo đúng luật, **nhưng BẮT BUỘC cấu hình `fallbacks` cho `conduit-pool` trước khi dùng
thật.** Đây không còn là lời khuyên thận trọng mà là **yêu cầu đã kiểm chứng bằng số**: phép thử tiêm
lỗi cho thấy LiteLLM ở cấu hình hiện tại **phục hồi 0/15** khi provider chính không dùng được, và tiêu
**40 giây** mỗi lượt trước khi báo lỗi. `num_retries=2` ở mức model group **không** thay cho
`fallbacks` — retry chỉ quay lại các deployment cùng provider. Log hiện vẫn báo
`Available Model Group Fallbacks=None`; việc này trước đây **cố ý** chưa làm để không ảnh hưởng tính
công bằng của thí nghiệm, giờ thí nghiệm đã xong thì phải làm.

Thêm hai lý do nữa để không bỏ cơ chế dự phòng: (a) LiteLLM **không bao giờ tự nâng model** khi gặp
prompt khó — 240/240 lượt cùng một model, (b) cổng 80% không phân giải được.

**Sau khi bật `fallbacks`, nên chạy lại phép thử tiêm lỗi** (`experiments/scripts/fault_injection.sh`,
45 lượt, ~$0,01) để xác nhận LiteLLM đã phục hồi được — đây là phép kiểm hồi quy rẻ cho đúng khuyết
điểm vừa đo được.

Ngoài ra nên **sửa khoảng trống logging ở mục 9** trước khi dựa vào `error_rate` cho bất cứ quyết định
vận hành nào.

---

## 11. Ghi chú phương pháp: đợt mở rộng cỡ mẫu (D14)

**Phải ghi rõ để người đọc tự đánh giá:** quyết định mở rộng từ 10 lên 20 item/bộ được đưa ra **SAU
khi đã thấy kết quả 360 lượt**, vì kết quả đó cho thấy cổng 80% không phân giải được (LiteLLM 81,7%,
biên 1,7 đpt) và 2/4 biến thể leave-one-out đổi proxy được chọn.

Mở rộng sau khi đã thấy số là chỗ dễ mất khách quan nhất, nên **D14 được đăng ký vào
`docs/roadmap.md` mục 4 và commit TRƯỚC khi gọi lượt API nào** (commit `2eb45ae`), kèm 5 ràng buộc:

1. **Kết luận cuối lấy trên toàn bộ 720 lượt**, áp đúng luật 4 bước không sửa + D13, **bất kể nó nói
   gì** — kể cả nếu đổi proxy được chọn. Không công bố chọn lọc bộ số có lợi. *(Đã giữ: kết quả 720
   là kết luận chính thức ở mục 1; các mốc 360 và 540 vẫn báo cáo đầy đủ ở mục 7.1.)*
2. **Cùng quy trình lấy mẫu**: cùng seed `20261014`, cùng `seed_offset` từng bộ, chỉ đổi `k` từ 10 →
   20. Đã kiểm thực nghiệm: 10 index cũ của **cả 4 bộ** là **tập con thật** của mẫu k=20, nên 360 lượt
   đã chạy **vẫn hợp lệ** và chỉ phải chạy 40 item mới. Đây là *tăng k của cùng một phép lấy mẫu*,
   không phải lấy mẫu mới.
3. **Không gán lại ID item.** 40 item cũ giữ nguyên ID; item mới đánh `*_11..*_20`. Sinh lại thẳng với
   `N_PER_SET=20` sẽ **dịch 36/40 ID** (vd. `mmlu_01` nhảy từ `source_index` 1044 sang 917) và ghép
   360 lượt cũ với đề khác — sai âm thầm, không báo lỗi.
4. **Không tính lại ngưỡng `prompt_len` của Portkey** (giữ 211/385 khóa 14/10): ngưỡng là một phần
   **cấu hình của nhánh Portkey**, tính lại theo phân bố 80 item là đổi nhánh giữa thí nghiệm, khiến 2
   đợt **không gộp được**.
5. Mọi tham số khác giữ y nguyên: `max_tokens=1024`, `temperature=0`, `num_retries=2`, `timeout=45s`,
   0-shot, pool model, cấu hình 3 proxy.

**Đính chính một khẳng định sai khi đề xuất D14:** lúc đề xuất, lý do nêu ra là mở rộng sẽ "đủ để biết
LiteLLM thật sự trên hay dưới 80%". **Sai** — tính lại thì phân biệt được biên đó cần ~5.000 item
(mục 7.3). Mở rộng **thực sự** mang lại một thứ khác và quan trọng hơn: **xóa bỏ độ nhạy
leave-one-out** (2/4 biến thể đổi proxy → 0/4), tức làm kết luận vững trước thành phần bộ đề.

### Ai chạy phần nào

| Đợt | MMLU + GSM8K | HumanEval + IFEval |
|---|---|---|
| 360 lượt đầu (item 01–10) | Hùng | Khoa |
| 360 lượt mở rộng (item 11–20) | Hùng | **Hùng** (máy Khoa không tham gia đợt này) |

Kế hoạch ban đầu là mỗi người chạy phần mình. Ở đợt mở rộng, cả hai nửa chạy trên máy Hùng — **không
ảnh hưởng số liệu** (cùng bộ đề, cùng cấu hình, cùng script) nhưng **mất một lớp kiểm chứng độc lập**.
Bù lại bằng việc Khoa chấm lại dữ liệu trên máy mình (phép chấm đã chứng minh tái lập được — mục 7.5).

---

## 12. Tái lập kết quả

Dữ liệu thô (720 lượt, đã chấm) và bảng đã xuất đều trong repo — **không cần gọi lại API**:

```
experiments/results/run_{litellm,bifrost,portkey}_20261019T13*.json  # 180 lượt, item 01-10, HumanEval+IFEval (Khoa)
experiments/results/run_{litellm,bifrost,portkey}_20261019T16*.json  # 180 lượt, item 01-10, MMLU+GSM8K (Hùng)
experiments/results/run_{litellm,bifrost,portkey}_20261020T0*.json   # 360 lượt, item 11-20 (đợt mở rộng D14)
experiments/results/d14-full-720/merged.json                         # 720 lượt đã gộp
experiments/results/d14-full-720/tables/*.csv                        # 4 bảng CSV
experiments/results/d14-full-720/decision_rule_output.json           # kết quả áp luật
```

```bash
# chấm lại (offline, miễn phí) -> kiểm toàn vẹn -> xuất bảng -> áp luật quyết định
PYTHONIOENCODING=utf-8 python experiments/scripts/grade_results.py experiments/results/run_*_202610{19T1,20T0}*.json
PYTHONIOENCODING=utf-8 python experiments/scripts/verify_results.py experiments/results/d14-full-720/merged.json --expect 720
PYTHONIOENCODING=utf-8 python experiments/analysis/export_tables.py experiments/results/d14-full-720/merged.json -o experiments/results/d14-full-720/tables
PYTHONIOENCODING=utf-8 python experiments/analysis/decision_rule.py experiments/results/d14-full-720/merged.json
```

Tham số cố định cả 3 proxy: `max_tokens=1024` · `temperature=0` · `num_retries=2` · `timeout=45s` ·
0-shot · pool 3 model thực dùng (`gpt-4o-mini` / `claude-haiku` / `gpt-4o`; `claude-sonnet` bị loại
theo D12, `gemini-flash` không nằm trong nhánh nào) · seed lấy mẫu `20261014` · 20 item/bộ (D14).

---

## 13. Danh sách kiểm cuối phần đánh giá (22/10/2026)

Mục này để phiên làm việc sau không phải suy luận lại phần nào đã xong.

**Đã kiểm, đạt:**

| Mục | Kết quả |
|---|---|
| Luật quyết định và ngưỡng 80% khóa trước kết quả | Có từ commit `9d6dfd7` (11/09), kết quả ở `b55ed56` (20/10) |
| Bộ chấm không đổi trong lúc chấm | 0 commit chạm `graders.py` / `vendor/` từ `871e756` đến nay |
| Dữ liệu 720 lượt toàn vẹn | `verify_results.py`: sạch; 240 lượt mỗi proxy; 0 lượt chưa chấm |
| Thứ tự và proxy được chọn ổn định | Không đổi qua 360 / 540 / 720 lượt; 4/4 leave-one-out |
| Hai công cụ phân tích khớp nhau | `decision_rule.py` và `export_tables.py` cùng p95 trên cả 3 proxy |
| Test tự động của phần thí nghiệm | 68/68 pass |

**Chưa kiểm, cần làm (không chặn kết luận):**

| Mục | Vì sao còn mở | Ai |
|---|---|---|
| Đếm dòng `routing_decisions` theo `proxy_name` cho 19–20/10, so với 720 + 45 | Cần bật Docker/Postgres; `CLAUDE.md` mục 2 yêu cầu mọi lượt phải được ghi vào bảng này | Hùng |
| Đối chiếu tổng chi phí (~$0,36) với dashboard OpenAI và Anthropic | Chỉ đọc được từ console của nhà cung cấp, không đọc được từ máy | Hùng |
| Bật `fallbacks` cho LiteLLM rồi chạy lại phép thử sự cố (D15, 45 lượt, ~$0,01) | Chưa bật; đây là phép kiểm hồi quy đã đăng ký | Hùng |
| Khoảng trống ghi log lỗi (mục 9): trường `error` rỗng ở 0/32 lượt lỗi | Chưa truy nguyên nhân | Khoa |

Nếu đối chiếu chi phí với dashboard cho thấy chênh lệch, cách xử lý là **tính lại chi phí offline từ
`model_pricing`**, không chạy lại thí nghiệm. Kết luận chỉ đổi nếu giá sai lệch hơn khoảng 4,5 lần
(tỷ lệ giữa chi phí của LiteLLM và Bifrost), điều khó xảy ra với bảng giá lấy từ trang giá chính thức.

**Dữ liệu và công cụ của phần đánh giá được coi là đóng.** Thay đổi sau thời điểm này chỉ nên là
bổ sung (ví dụ kết quả phép thử hồi quy D15), không sửa số liệu hay luật đã áp.
