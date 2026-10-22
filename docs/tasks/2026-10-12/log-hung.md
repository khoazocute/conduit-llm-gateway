# Log Hùng — tuần 2026-10-12

## 2026-10-14 — Phase 0 + Phase 1 (làm sớm 1 ngày)

| Việc | Kết quả | File | Khoa cần làm gì |
|---|---|---|---|
| Phase 0 — chốt Design Y | `docs/experiment-design.md` là nguồn đúng cho bài toán. D2 sửa, thêm D10/D11. `CLAUDE.md` đổi 30 prompt/270 lượt → 40 item/360 lượt. Luật quyết định **không sửa** | `docs/experiment-design.md`, `docs/roadmap.md` mục 4, `CLAUDE.md` mục 2 | Đọc `experiment-design.md` trước khi làm K1–K4 |
| H1 — bộ 40 item | Tải 4 bộ từ nguồn chính thức, lấy 10 item/bộ, seed **20261014**. Tái lập được bằng `build_prompts.py` | `experiments/prompts/build_prompts.py`, `prompts.json`, `manifest.json` | — |
| H2 — validator | Viết lại cho schema 4 bộ; kiểm cả trường bắt buộc để chấm (`entry_point`+`test` cho HumanEval, `instruction_id_list`+`kwargs` cho IFEval). Thêm `--vi` cho bộ tiếng Việt | `experiments/prompts/validate_prompts.py` | — |
| H3 — ngưỡng `prompt_len` | **Chốt: < 211 rẻ · 211–384 trung · ≥ 385 đắt.** Tercile của phân bố 40 item → chia 13/13/14 | `docs/routing-policy.md` mục 7, `manifest.json` | **Dùng đúng 3 ngưỡng này cho K2**, map tier → model giống Bifrost |
| H4 — khảo sát benchmark | 4 bộ: paper gốc, URL, split, sha256, index đã chọn, metric, giấy phép, mọi chỗ lệch protocol | `docs/benchmark-survey.md` | **Review chéo: đối chiếu 3 chỗ ở mục 3** (biến thể IFEval, pass@1 greedy, cách trích số GSM8K) |
| H5 — pin Bifrost | `:latest` → **`v2.1.1`** (tag đã verify tồn tại). Container tạo lại, đang chạy đúng pin | `docker-compose.yml:59` | — |
| H6 — dọn | Xoá container `litellm-autorouter-test` (port 4001) + **3 rule `smoke-*`** trong Bifrost | — | Bifrost giờ **0 rule, analyzer disabled** — slate sạch cho K1 |

## Phát hiện quan trọng

**1. Bộ 30 prompt tiếng Việt được giữ lại dùng được, không xoá.** Đổi tên
`prompts.json` → `prompts-vi-30.json`. Nó là phép thử nhạy ngôn ngữ của Bifrost
(`experiment-design.md` mục 9 điểm 3), không phải rác.

**2. `decision_rule.py` đang chấm lại câu trả lời một lần nữa từ `prompts.json` — đã bỏ.** Mỗi
record vốn đã mang sẵn điểm chấm. Giờ `decision_rule.py` đọc `passed` (fallback
`closed_qa_correct` cho dữ liệu thô trước 14/10) và **không còn phụ thuộc `prompts.json`**. Đây
đúng là kiến trúc chấm offline mà Phase 2 cần: thu output và chấm điểm độc lập nhau.

Kèm 2 thay đổi ngữ nghĩa phải biết:
- `compute_closed_qa_accuracy` → **`compute_quality_accuracy`**, và key `closed_qa_accuracy` trong
  `pareto_data` → **`quality_accuracy`**. Lý do: giờ **cả 40 item** đều có metric khách quan, nên
  cổng chất lượng ở bước 1 phủ **40/40** thay vì 12/30 như trước. Ngưỡng vẫn **0.80**, không đổi.
- Thêm **`ungraded_runs`** vào `pareto_data`. Lượt thành công nhưng chưa chấm thì **không** âm thầm
  tính là sai — đếm riêng và hiện ra. Cần cho phương án lùi của Phase 3 (nếu pass@1 chưa xong thì
  HumanEval là "đã thu, chưa chấm").

Đã kiểm hồi quy trên dữ liệu dry-run 02/10: cho **đúng kết quả cũ** (cả 3 proxy accuracy 1.000,
chọn `litellm`). 20/20 test pass.

**3. Ngưỡng `prompt_len` của Portkey có điểm yếu đoán trước được, và nó làm sắc thêm H3.** Độ dài
prompt **tương quan với *loại bài*, không với *độ khó***: HumanEval hầu như không bao giờ rơi tier
rẻ, GSM8K và IFEval phần lớn rơi tier rẻ. Nên Portkey sẽ gần như **định tuyến theo bộ benchmark**
chứ không theo độ khó. Đã ghi vào `routing-policy.md` mục 7 — **không được trình bày trong báo cáo
như thể Portkey "định tuyến theo độ khó"**.

**4. Ngưỡng suy từ chính bộ đề — đã cân nhắc chuyện này có phải "mớm đáp án" hay không.** Kết luận:
không, vì chỉ dùng **phân bố độ dài đầu vào**, không dùng nhãn độ khó hay đáp án đúng. Người vận
hành thật cũng làm đúng việc đó. Nhưng **vẫn phải khai báo** trong báo cáo.

## Cần bàn cùng nhau

1. **`max_tokens` chưa từng được gửi.** `HttpProxyChatClient.complete()` chỉ gửi `model`,
   `messages`, `fallbacks` — **không có `max_tokens`** (`HttpProxyChatClient.java:92-100`). Nghĩa là
   D7 chưa bao giờ thực sự được thực thi qua đường đi của app. K3 phải thêm `max_tokens: 512` và
   `temperature: 0`. Hệ quả phụ: lỗi `max_tokens` của LiteLLM auto_router mà mình phát hiện **chỉ
   cắn sau khi K3 xong** — nên nó là phát hiện phụ để báo cáo, **không phải** căn cứ chính để bỏ
   auto_router (căn cứ chính là pin bảo mật `v1.83.14-stable`).

2. **Phase 2 còn 2 việc nặng của mình: H7 (4 bộ chấm) + H8 (runner đọc 4 nhóm, chấm offline).**
   Riêng `pass@1` cần sandbox chạy code model sinh ra — đây là chỗ rủi ro nhất của mốc 17/10. Phương
   án lùi đã chốt trong `tasks.md`: vẫn chạy đủ 360 lượt, chấm 3 bộ còn lại, HumanEval bù sau.

3. **`run_experiment.py` hiện sẽ ghi `passed: None` cho mọi item** vì `grade_closed_qa()` chỉ xử lý
   category `closed_qa` (không còn tồn tại trong bộ mới). Đúng theo kiến trúc chấm offline, nhưng
   nghĩa là **dry-run Phase 2 sẽ báo accuracy 0 và `ungraded_runs` = toàn bộ** cho tới khi H7 xong.
   Đừng tưởng là lỗi.

## Bẫy môi trường mới (đã ghi vào `tasks.md` mục 5)

- `git-bash` biến `/app/config.yaml` thành `C:/Program Files/Git/app/...` trong lệnh `docker` →
  phải `MSYS_NO_PATHCONV=1`.
- `grep -P` không dùng được (locale) → dùng `sed -n 's/.../p'`.
- Python in tiếng Việt ra console Windows ném `UnicodeEncodeError` (cp1252) — **không phải lỗi
  logic** → `PYTHONIOENCODING=utf-8 python ...`.
- GHCR **có** publish tag trần cho LiteLLM bản mới (`v1.105.0` có, `v1.105.0-stable` không) — ghi
  chú trong `CLAUDE.md` chỉ đúng cho nhánh v1.83.x.
- Docker Hub của Bifrost dùng tag **`v2.1.1`** (có tiền tố `v`), không có `2.1.1`.

---

## 2026-10-14 (chiều) — Phase 2 phần của Hùng, làm sớm 2 ngày

| Việc | Kết quả | File | Khoa cần làm gì |
|---|---|---|---|
| H7 — 4 bộ chấm | Đủ 4 metric, **24 test** (mỗi metric ≥2 ca đúng + ≥2 ca sai, có cả ca bẫy) | `experiments/analysis/graders.py`, `experiments/tests/test_graders.py` | Review: đối chiếu 3 chỗ ở `benchmark-survey.md` mục 3 |
| H8 — chấm offline | Runner bỏ chấm inline (ghi `passed: null`); script chấm riêng ghi `passed`/`score`/`grade_detail` vào file kết quả, `--db` nạp `response_quality_score` | `experiments/scripts/grade_results.py`, `run_experiment.py` | Dùng script này sau khi dry-run K5 |
| Dependency | `requirements.txt` + README vendor | `experiments/requirements.txt`, `experiments/analysis/vendor/README.md` | **Phải chạy 2 lệnh setup** trước khi chấm, xem bên dưới |

### Dùng verifier IFEval **chính thức**, không tự viết lại

Vendor nguyên văn 3 file của `google-research/instruction_following_eval` (Apache-2.0, giữ header)
vào `experiments/analysis/vendor/`. Lý do: thầy yêu cầu tiêu chí chấm chuẩn theo paper — tự viết lại
verifier thì metric không còn là metric của paper. Registry có 25 verifier, bộ đề cần **12 loại**,
có test kiểm đủ cả 12 đều build + chạy được (để không tới lúc chạy 360 lượt mới phát hiện thiếu).

**Khoa phải chạy 2 lệnh này trước khi chấm, thiếu là nổ:**
```bash
python -m pip install -r experiments/requirements.txt
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('punkt')"
```
Bước nltk là **bắt buộc**: 2 verifier tách câu (`length_constraints:number_sentences`,
`change_case:capital_word_frequency`) ném `LookupError` nếu thiếu corpus `punkt`.

### Hai quyết định nhỏ nhưng ảnh hưởng số liệu

**1. IFEval: `passed` dùng prompt-level strict, không phải instruction-level.** Paper có 4 biến
thể metric. Cổng ở bước 1 của luật quyết định là nhị phân "item đạt/không" nên phải chọn mức
prompt-level (đạt **iff mọi** ràng buộc đều theo) cho khớp 3 bộ còn lại. Instruction-level (tỷ lệ
ràng buộc theo được) **vẫn ghi** vào `score` từng lượt để báo cáo. Đã đổi tên metric
`ifeval_strict_instruction` → **`ifeval_strict_prompt`** cho đúng cái nó thực sự đo.

**2. Thêm `signature_prompt` vào item HumanEval.** Model có thể chỉ trả về *thân* hàm, không có
signature. Bộ chấm cần prompt gốc (chưa có dòng chỉ thị) để ghép lại rồi mới chạy test. Có test
riêng cho ca này.

### Phát hiện quan trọng

**Tự bắt được một lỗi của chính mình lúc kiểm lại.** Ngưỡng `prompt_len` ban đầu được ghi vào
`manifest.json` bằng một script riêng, nhưng `build_prompts.py` **ghi đè `manifest.json` mỗi lần
chạy** → lúc kiểm tái lập, ngưỡng bị xoá mất. Nếu không kiểm thì ai chạy lại script là ngưỡng biến
mất lặng lẽ. Đã sửa đúng gốc: chính `build_prompts.py` tính tercile và ghi kèm. Giá trị không đổi
(`< 211 / 211-384 / >= 385`).

**`pass@1` chạy code model sinh ra trong subprocess có timeout 15s + thư mục tạm — KHÔNG phải
sandbox đầy đủ** (không chặn mạng/filesystem). Harness chính thức của OpenAI cũng thực thi như vậy
và kèm cảnh báo tương tự. Đã ghi vào giới hạn trong `graders.py`; cần nêu trong báo cáo. Có test
kiểm vòng lặp vô hạn bị timeout chứ không treo.

**Phương án lùi đã chạy thử, không phải chỉ nói trên giấy.** `grade_results.py --skip pass_at_1`
cho kết quả: 7/9 chấm được, 2 lượt giữ `passed=null`, `decision_rule.py` tính accuracy trên 7 lượt
và báo `ungraded_runs=2` riêng — **không** âm thầm coi 2 lượt đó là sai. Nên nếu 17/10 mà sandbox
pass@1 có vấn đề thì vẫn chạy được đủ 360 lượt và bù chấm sau.

### Cần bàn cùng nhau

1. **Runner giờ ghi `passed: null` cho mọi lượt.** Chạy `decision_rule.py` **trước khi** chấm sẽ
   thấy accuracy = 0 và `ungraded_runs` = toàn bộ. **Không phải lỗi** — phải chấm trước, rồi mới
   áp luật quyết định. Thứ tự đúng: `run_experiment.py` → `grade_results.py` → `decision_rule.py`.
2. **Cách trích đáp án GSM8K là quy ước, không phải quy định của paper.** Lấy *số cuối cùng* trong
   câu trả lời. Có test cho ca bẫy (số ở bước trung gian, dấu phẩy hàng nghìn), nhưng vẫn nên kiểm
   tay trên 10 item thật khi có kết quả — model có thể viết đơn vị hoặc năm ở cuối câu.
3. Phần của mình cho 17/10 **đã xong hết**. Đường tới hạn giờ là K1–K4 của Khoa (nhất là
   `resolveReturnedModel`) rồi mới tới dry-run K5–K7.

---

## 2026-10-16 — Review K1–K7 của Khoa + sửa 4 lỗi, chốt D12

### Duyệt bản sửa HumanEval của Khoa: ĐÚNG

Tái hiện độc lập trên `humaneval_01` thật: bản cũ của tôi báo `NameError: name 'List' is not
defined` trên một **lời giải đúng** — đề có `from typing import List`, model không viết lại dòng đó
(mà sao phải viết lại), bộ chấm của tôi chỉ chạy code model nên thiếu import. Khoa sửa thành luôn
ghép đề gốc trước, đúng như harness chính thức (`prompt + completion + test`). Kiểm chiều ngược:
không gây **đạt oan**, vì đề chỉ là stub trả `None` nên test không pass nhờ đề. Đã merge.

Phần backend của Khoa (K3/K4) chất lượng cao: `promptLength` dùng `codePointCount` khớp `len()` của
Python; đọc `x-portkey-last-used-option-index` thay vì đoán alias; thiếu header thì trả id thô cho
lộ ra thay vì sai trong im lặng. `--sets`/`--per-set` giải đúng vấn đề `--limit` cũ chỉ lấy N item
đầu (= toàn MMLU). `dry_run.sh` chấm trước khi gộp — sửa đúng thứ tự mà tôi ghi trong log mà không
nối vào script.

### Lỗi 1 (của tôi, nặng nhất): bộ chấm MMLU CHẤM ĐẠT OAN

Pattern cuối `\b([ABCD])\b` bắt chữ cái ở **bất kỳ đâu** trong text. `claude-haiku` trả lời
`mmlu_01` bằng 1400+ ký tự lập luận rồi **bị cắt giữa câu** ("Actually, let me") — **chưa hề đưa ra
đáp án**. Nhưng text đầy `A[i]` và `Array A` (tên biến trong đề về cache) nên pattern bắt ra `'A'`,
trùng đáp án đúng → `passed=True`.

Chấm lại dry-run với **cả hai** bản sửa:

| Proxy | Khoa báo | Thật |
|---|---|---|
| LiteLLM | 9/12 (75%) | 9/12 (75%) |
| **Bifrost** | **11/12 (92%)** | **9/12 (75%)** |
| Portkey | 9/12 (75%) | 9/12 (75%) |

Cả ba bằng nhau. Kết luận "chỉ Bifrost qua 80% → chọn Bifrost" của K7 là **do bug này**. Sửa: bỏ hẳn
pattern "bất kỳ đâu", chỉ nhận đáp án rõ ràng, lấy cái **cuối** (đáp án chốt thường ở cuối), không
có thì trả `None` = không đạt. Kiểm: **không làm mất lượt đạt hợp lệ nào**. 2 test hồi quy.

### Lỗi 2 (của tôi): `--limit` mặc định 30 nhưng bộ đề 40 item

Chạy cả 4 bộ mà không truyền `--limit` → âm thầm bỏ mất **10 item IFEval cuối**. Sửa: mặc định 0 =
lấy hết. Kiểm: không `--sets` → 40 item; `mmlu,gsm8k` → 20; `humaneval,ifeval` → 20; `--per-set 1` → 4.

### Lỗi 3 (code cũ): chi phí ghi 0 trong im lặng

`ChatService.unitPrice()` trả `BigDecimal.ZERO` khi không khớp `model_pricing`. Nên lượt ghi sai tên
model được tính là **tốn $0** — mà bước 2 của luật quyết định là "chi phí trung bình thấp nhất", nên
proxy bị lỗi đó sẽ trông như **miễn phí và thắng**. Thêm `experiments/scripts/verify_results.py`
kiểm 5 thứ trước khi áp luật. Chạy trên dry-run của Khoa → **bắt ngay 3 lượt Portkey trả rỗng**.

### Lỗi 4 (cả hai bỏ sót): `temperature` chưa bao giờ được gửi

Tài liệu ghi `temperature: 0` (yêu cầu của protocol `pass@1`), nhưng backend và cả 3 config proxy
**không có chỗ nào gửi** → đang chạy ngẫu nhiên. Bằng chứng trong chính dry-run: LiteLLM
`ifeval_01`, cùng model cùng prompt, **đạt / trượt / đạt** qua 3 lần. Mỗi bộ chỉ 10 item nên nhiễu
này đủ sức lật kết quả.

### D12: tier đắt đổi sang `gpt-4o`, bỏ `claude-sonnet-5` khỏi mọi đường định tuyến

Phương án (a) của Khoa (tăng `max_tokens` lên 2048) **đã thử và chết**. Gọi thẳng Anthropic:

| Thử | Kết quả |
|---|---|
| Sonnet, `max_tokens: 2048` | **2048 token thinking, text RỖNG**, `stop_reason=max_tokens`, **$0.021** |
| Sonnet, `thinking: disabled` | trả `A` đúng, 3 token, **$0.00054** (rẻ hơn 39 lần) |
| Sonnet, `temperature: 0` | **HTTP 400 — "`temperature` is deprecated for this model"** |
| gpt-4o, `mmlu_01` | 1 token, `stop_reason=stop`, $0.00049 — không có bệnh |
| gpt-4o, `ifeval_08` (đòi ≥350 từ) | 467 token / 379 từ, `stop` — **512 đủ** |

Sonnet **nở suy nghĩ cho vừa hết ngân sách**, nên tăng `max_tokens` không bao giờ cứu được. Phương
án (b) tắt thinking **không dùng được cho kiến trúc này**: backend không biết trước proxy chọn model
nào (đó là điểm của Design Y) nên không gửi tham số riêng-Anthropic có điều kiện được; gửi vô điều
kiện thì model OpenAI nhận tham số lạ. `temperature` vướng **đúng cùng một chỗ**.

→ Đổi tier COMPLEX sang `gpt-4o` (cũng thuộc tầng đắt của pool, CLAUDE.md mục 2). Sonnet bị bỏ khỏi
**cả bốn** chỗ: CEL rule Bifrost, condition Portkey, `conduit-pool` LiteLLM, và **chuỗi `fallbacks`
Bifrost trong `application.yml`** (chỗ này là mìn: model rẻ lỗi thì Bifrost leo tới sonnet rồi 400).
Áp dụng như nhau cho cả 3 proxy nên vẫn công bằng. `max_tokens` **giữ 512**.

**Đây là một phát hiện của khoá luận, không chỉ là ghi chú cấu hình:** *đặt một reasoning model vào
pool thì mọi router chọn nó đều trả giá đầy đủ cho một câu trả lời trống, và không có cảnh báo nào.*

### Phát hiện C (Bifrost không tất định): phản biện đề xuất thêm warmup

Khoa hỏi có nên thêm lượt warmup. **Tôi nghĩ không nên.** Bifrost `mmlu_01` nhảy giữa **hai tier
liền kề** (SIMPLE lượt 1 → MEDIUM lượt 2–3). Mà đợt 09/10 tôi chạy GSM8K 3 lần trên analyzer **vừa
dựng mới** → SIMPLE cả 3, câu đối chứng 2 lần → COMPLEX cả 2. Nếu là warmup thì lượt 1 hôm đó cũng
phải lệch — nó không lệch. Cách giải thích khớp hơn: điểm của `mmlu_01` nằm **sát ngưỡng tier**
(`tier_boundaries` 0.2/0.4) nên dao động nhỏ đủ lật. Nếu đúng thì đó là **tính chất nội tại của cơ
chế**, thêm warmup chỉ che nó đi. Để nguyên, báo `consistency_rate` thật, ghi rõ **không xác nhận
được cơ chế** vì v2.1.1 không expose `complexity_score`.

Khoa đúng ở điểm quan trọng nhất: **không được viết "tất định" vào báo cáo** — kết luận 09/10 của
tôi chỉ đúng với 2 prompt đã thử, tôi đã tổng quát hoá quá.

### Phát hiện F (nltk): đính chính nhẹ

`punkt_tab` **có** trong `experiments/requirements.txt` (phần hướng dẫn đầu file) và
`benchmark-survey.md` mục 6. Nhưng điểm của Khoa vẫn đúng: dễ bỏ sót và thiếu thì IFEval trượt hàng
loạt. Nên biến thành kiểm trong code — việc còn mở.

### ⚠️ BƯỚC TRIỂN KHAI phải làm trước Phase 3 (cả hai máy)

Cấu hình Bifrost nằm trong volume, không trong git; config LiteLLM mount vào container. Nên sửa file
**chưa có hiệu lực** cho tới khi:

```bash
docker compose up -d --force-recreate litellm     # conduit-pool mới, không còn sonnet
bash proxy-configs/bifrost/complexity-setup.sh    # CEL rule COMPLEX -> gpt-4o
# rồi khởi động lại backend (temperature + chuỗi fallback mới)
```

Sau đó chạy `verify_results.py` trên dry-run mới trước khi áp luật quyết định.

### Còn mở

- Chưa verify end-to-end qua app (Docker tắt lúc làm). **Phải chạy lại dry-run nhỏ sau 3 bước trên.**
- `decision_rule.py` chỉ in `pareto_data` của proxy qua bước 1 (phát hiện E của Khoa) — nên sửa để
  in cả 3 proxy, báo cáo cần số của cả proxy bị loại.
- Java: 13/14 test pass; lượt lỗi duy nhất là `contextLoads` do Postgres chưa chạy, không liên quan.

---

## 2026-10-17 — Cổng kiểm tiền-bay trước Phase 3

Hùng yêu cầu kiểm hết mọi rủi ro để không phải chạy lại lần 2. Tìm ra **7 vấn đề**, trong đó
**3 cái sẽ làm sai kết quả mà không có lỗi nào báo ra**.

### ⛔ 1. Bifrost quá hạn embedding → định tuyến sai TRONG IM LẶNG (nặng nhất)

Analyzer đặt `timeout: 1.5s` cho lượt embedding. Bằng chứng trong `/api/logs`: lượt đầu sau
khi idle mất **1647 ms** → vượt hạn → `complexity_tier` **TRỐNG** → **không CEL rule nào khớp**
→ request rơi về model mà app xin (`gpt-4o-mini`), và được ghi nhận như một quyết định routing
bình thường. Một lượt khác mất **1465 ms** — sát hạn.

Đây chính là **phát hiện C của Khoa** ("Bifrost không tất định") và **tôi phản biện SAI hôm
16/10**: tôi đoán điểm nằm sát ngưỡng tier. Gọi **thẳng** Bifrost 6 lần (`max_tokens=1`, gần như
miễn phí) thì nó **tất định hoàn toàn** — `claude-haiku` cả 6 lần. Không phải nhiễu, không phải
warmup, mà là **quá hạn**.

Hậu quả nếu không sửa: Bifrost có những lượt âm thầm bị tính là "chọn `gpt-4o-mini`" → kéo
`consistency_rate` xuống và làm nó **trông rẻ hơn thực tế**. Cả hai đều là chỉ số trong luật chọn.

Sửa: `timeout` 1.5s → **8s** (không đổi chính sách định tuyến, chỉ cho analyzer đủ thời gian)
+ `preflight.py` kiểm mục này.

### ⛔ 2. Ví credit không đủ cho 360 lượt → chết giữa đợt, bẩn `error_rate`

Đo từ đợt 24 lượt: **692 credit/lượt** trung bình, cao nhất 1.595 → 360 lượt cần **~249.000**.
Ví của user thí nghiệm chỉ còn **155.681** → sẽ cạn khoảng **lượt 225**, và mọi lượt sau bị ghi
`status=error` — nhưng đó là **lỗi ví nội bộ cạn tiền**, không phải lỗi nhà cung cấp → bẩn
`error_rate` của đúng proxy đang chạy lúc đó.

Sửa: `CREDIT_GRANTED` 200.000 → **1.000.000** (credit là đơn vị nội bộ, để dư không tốn gì) +
`assert_enough_credit()` chặn **trước khi tiêu đồng nào** + mục kiểm trong `preflight.py`.

### ⛔ 3. `--proxy-name` chỉ là cái NHÃN, không ai kiểm

Runner ghi bất kỳ nhãn nào ta truyền. Backend đang chạy Portkey mà gõ `--proxy-name bifrost`
thì 120 bản ghi bị dán nhãn sai và **cả phép so sánh thành vô nghĩa, không lỗi nào báo**.
`dry_run.sh` an toàn vì set cả hai từ cùng biến, nhưng **Phase 3 hai người chạy tay** — đúng chỗ
dễ gõ lệch.

Sửa: backend **có** ghi proxy thật của nó vào `routing_decisions.proxy_name` → runner đọc lại
dòng vừa tạo ở **lượt đầu** và **dừng ngay** nếu lệch.

### 4. Bước chấm trong `dry_run.sh` chưa bao giờ chạy được

`grade_results.py` / `verify_results.py` chết với đường dẫn tuyệt đối (`Path().glob` không nhận
pattern tuyệt đối) — mà `dry_run.sh` truyền kiểu đó. Sửa cả hai.

### 5. `decision_rule.py` ném exception khi không proxy nào qua cổng

Chạy thật mà không ai đạt 80% thì mất luôn bảng số liệu, chỉ còn stack trace. Giờ đó là **một
kết quả**: `selected_proxy=None` + `no_proxy_passed_gate=True` + số liệu đủ cả 3 proxy. Kèm luôn
**phát hiện E của Khoa**: `pareto_data` in cho **tất cả** proxy, không chỉ proxy qua cổng.

### 6. Không có cách chạy tiếp → dứt giữa đợt là trả tiền hai lần

`roadmap.md` mục 7 ghi cách giảm rủi ro là "chạy tiếp từ lượt lỗi" nhưng chưa ai làm. Thêm
`--resume FILE`: bỏ qua lượt **đã thành công**, chạy lại lượt **lỗi** (lượt lỗi không tốn tiền và
mỗi item cần đủ 3 lần lặp). Tách thành `plan_runs()` + 5 test.

### 7. Cái bẫy tôi tự tạo, và nó đã nổ

`--limit 0` đổi nghĩa từ *"không chạy lượt nào"* sang *"lấy hết"*, nhưng header `dry_run.sh` vẫn
ghi `PROMPT_LIMIT=0` là cách test không tốn tiền. Bản vá chặn **bị lỗi cú pháp nên chưa áp**, mà
lệnh thử lại nằm ngay sau đó trong **cùng một lượt gọi** → chạy thật. **79 lượt ngoài ý muốn,
$0.00325.**

Bài học, đã sửa đúng gốc: **không bao giờ gộp "vá lỗi" và "thử xem vá có ăn không" vào cùng một
lệnh** — phải xác nhận bản vá đã áp trước, thành một bước riêng. Giờ `PROMPT_LIMIT=0` bị chặn kèm
hướng dẫn; test không tốn tiền dùng `NO_CALLS=1`. Dữ liệu dở dang chuyển vào
`experiments/results/_khong-phai-du-lieu-thi-nghiem/` kèm README (28/79 lượt lỗi là do bị kill).

### Những mặt đã kiểm và SẠCH

| Mặt | Cách kiểm | Kết quả |
|---|---|---|
| Sandbox chạy code HumanEval | Cả 10 bài với **lời giải chuẩn** của dataset | **10/10 đạt**; lời giải sai **10/10 trượt**; 0.7s, không treo |
| Bộ chấm MMLU sau khi sửa | Trên 10 câu trả lời haiku thật | **10/10 trích được đáp án**, không chấm trượt oan |
| `temperature: 0` | 17 item × 3 lần qua app | **17/17 cùng kết quả**, 0 dao động |
| `max_tokens: 1024` đủ chưa | haiku cả 10 item MMLU; `ifeval_08` (đòi ≥350 từ) trên haiku | **0/10 bị cắt**; `ifeval_08` 534 token / 366 từ, `end_turn`, **đạt** — dùng 52% ngân sách |
| Ghi đúng model + đúng tiền | 24 lượt qua app, cả 3 nhánh | **0 lượt** thành công nào bị ghi `cost<=0`; `verify_results` sạch |
| Phân bố model của Portkey | Tính trên cả 40 item (tất định) | **14 gpt-4o / 13 gpt-4o-mini / 13 haiku** — không tier nào bỏ trống |
| `routing_decisions` ghi cả lượt lỗi | Query DB | Có (`litellm|error|7`) → đếm vẫn khớp |
| Số bản ghi file vs DB | Đợt 24 lượt | **24 = 24** |
| Hai nửa Phase 3 có trùng item không | Test tự động | 20 + 20 = 40, **giao nhau rỗng** |
| Gõ sai tên bộ | Test tự động | Nổ, không âm thầm chạy sai |

### Chi phí ngày 16–17/10

| Việc | Lượt | Tiền |
|---|---|---|
| Tìm nguyên nhân Sonnet / haiku / gpt-4o | 24 | $0.056 |
| Sự cố `PROMPT_LIMIT=0` | 79 | $0.0033 |
| Cổng kiểm 2 nhánh (bifrost + portkey) | 24 | $0.0502 |
| Dò Bifrost tất định (`max_tokens=1`) | 6 | ~$0 |
| `ifeval_08` trên haiku (2 ngân sách) | 2 | $0.0055 |
| **Tổng** | **135** | **~$0.116** |

Chiếu từ 24 lượt = $0.0502 → **360 lượt ước $0.75**. Thời gian ~**30 phút** (≈4s/lượt + 3 lần
restart backend).

### Khoa cần làm trước khi chạy phần của mình

```bash
git pull
bash proxy-configs/bifrost/complexity-setup.sh    # nhận timeout 8s mới
docker compose up -d --force-recreate litellm      # conduit-pool không còn sonnet
rm -f experiments/scripts/.experiment_identity.json  # ví mới 1.000.000 credit
PYTHONIOENCODING=utf-8 python experiments/scripts/preflight.py   # phải xanh hết
```

### Còn lại — chưa kiểm được / chấp nhận

- **Hạn mức chi tiêu của API key**: không đọc được từ đây. Hùng nên xem console của provider
  trước khi chạy, vì hết hạn mức giữa đợt cũng gây lỗi hàng loạt.
- **Rate limit**: nhịp tự nhiên ~4s/lượt (≈15 lượt/phút) nên rủi ro thấp; runner không có nghỉ
  giữa lượt. Nếu gặp 429 thì lượt đó ghi `status=error` và `--resume` chạy lại được.
- **Giới hạn để ghi báo cáo:** `claude-haiku` chạm trần ngân sách trên một số item IFEval
  (`ifeval_01` chạm cả ở 1536) → **chi phí đo được của haiku trên IFEval bị quyết định bởi trần
  ta đặt**, không phải độ dài tự nhiên. Áp cùng trần cho cả 3 proxy nên vẫn công bằng.

## Review — Khoa (2026-10-19)

Đã pull bản `ef70d96`, kiểm lời trong tin nhắn với code, rồi chạy phần Phase 3 của Khoa (180 lượt,
`log-khoa.md` mục "Phase 3").

**Đồng ý:** D12 (bỏ Sonnet, tier đắt → `gpt-4o`) và D13 (luật dự phòng theo chi phí/câu đạt, đăng ký
trước khi chạy, không hạ ngưỡng 80%). Đã kiểm: không còn đường định tuyến nào tới Sonnet (Bifrost
COMPLEX → `gpt-4o`, Portkey `>=385` → `gpt-4o`, `conduit-pool` 4 deployment, fallbacks sạch); các chỗ còn
chữ "sonnet" chỉ là chú thích / alias gọi tay. Timeout 8s, `max_tokens` 1024, `temperature` 0 đều có.
Bộ đề: đối chiếu 40/40 item khớp nguyên văn với file gốc (MMLU qua `cais/mmlu`, GSM8K / HumanEval /
IFEval qua repo chính thức). Ngưỡng `prompt_len` suy từ tercile phân bố thật — hợp lý.

**Cần sửa / lưu ý:**

1. **Bộ chấm MMLU mới vẫn còn 1 kiểu chấm đạt oan** (nhẹ hơn lỗi cũ nhiều). Pattern
   `(?:final answer|answer|đáp án)\s*(?:is|:|là)?\s*…\(?([ABCD])\)?\b` chạy với `IGNORECASE`, nên chữ
   `a` thường bị bắt làm đáp án: `"To find the answer is a bit tricky…"` → **`A`**. Thử trên bản
   `lhung`. Rủi ro thấp vì đề bắt "letter only", nhưng là phần MMLU của Hùng — đề xuất chỉ nhận chữ in
   hoa (bỏ `IGNORECASE` cho nhóm chữ cái, vd. `(?i:final answer|answer|đáp án)…([ABCD])`) + 1 test.
2. **`preflight.py` gán cứng `localhost:8080` cho Bifrost** → máy remap port (máy Khoa: Bifrost
   `:18080`, `:8080` là Tomcat) thì 3 mục Bifrost kiểm nhầm dịch vụ. Khoa đã sửa: đọc `BIFROST_URL`,
   mặc định vẫn `:8080` (commit kèm).
3. **Hai cách tính p95 khác nhau.** `decision_rule.py` nội suy tuyến tính, `export_tables.py` dùng
   `statistics.quantiles(n=20)` mặc định `exclusive`. Nửa của Khoa: Bifrost **5831 ms vs 9641 ms**
   (3 lượt đột biến 9.8–13.3 s rơi đúng vùng p95 khi n=60). Đề nghị `export_tables.py` dùng
   `method="inclusive"` (ra đúng số của luật) để CSV vẽ biểu đồ khớp với luật quyết định.
4. **`temperature: 0` không cho kết quả lặp lại hoàn toàn**: Bifrost `ifeval_05`, LiteLLM `ifeval_07`,
   Portkey `humaneval_08` cùng model + cùng prompt mà đạt/trượt khác nhau giữa 3 lần. "17/17 nhất quán"
   ở đợt 17/10 không giữ ở quy mô 60 item/proxy — đừng viết "temperature 0 → tất định" vào báo cáo.
5. Nhỏ: `verify_results.py` chạy trên `merged.json` báo mọi lượt "trùng" (thiết kế cho file 1 proxy)
   — nên ghi rõ trong docstring hoặc gom theo `(proxy_name, prompt_id, run_index)`. `preflight.py` cảnh
   báo ví đọc ví lớn nhất của user `exp.buyer.*` cũ, không biết file danh tính đã xoá → báo động giả.

---

## Hùng — 19–20/10: chạy nửa còn lại, gộp 360, áp luật quyết định

| Việc | Kết quả | File |
|---|---|---|
| Chạy 180 lượt (MMLU + GSM8K × 3 proxy × 3 lần) | **180/180 thành công, 0 lỗi**, $0,07051 | `run_*_20261019T16*.json` |
| Chấm lại **cả 360** bằng `graders.py` mới nhất | 317/360 đạt (88,1%) | — |
| Gộp 360 + xuất bảng + áp luật quyết định | **chọn `litellm`**, quyết ở **bước 2** | `experiments/results/phase3-full-360/` |
| Viết báo cáo kết quả | 10 mục, có đối chiếu H1–H3 | **`docs/experiment-results.md`** |
| Sửa `verify_results.py` (lỗi Khoa nêu ở mục 5 review) | gom theo `(proxy_name, prompt_id, run_index)` | `experiments/scripts/verify_results.py` |
| Sửa `manifest.json` còn ghi `expensive: claude-sonnet` | → `gpt-4o`, khớp D12 và khớp dữ liệu đã chạy | `experiments/prompts/manifest.json` |

**Số chốt (360 lượt, 0 lỗi, tổng $0,18920):**

| Proxy | Độ chính xác | Chi phí TB/lượt | Chi phí/câu đạt | p95 | Nhất quán |
|---|---|---|---|---|---|
| `litellm` | 81,7% | **$0,000097** | **$0,000119** | 5001 ms | 1,00 |
| `bifrost` | 88,3% | $0,000601 | $0,000680 | 5629 ms | 1,00 |
| `portkey` | 94,2% | $0,000879 | $0,000933 | 5819 ms | 1,00 |

### Phát hiện quan trọng

1. **Luật 4 bước và chỉ số "chi phí/câu đạt" cho cùng một kết luận** — không có chỗ lệch phải giải
   trình. LiteLLM rẻ hơn 5,7–7,8× ngay cả khi đã phạt nó vì 22 câu làm sai.
2. **LiteLLM chọn `gpt-4o-mini` 120/120 lượt, không đổi model lần nào.** Nhánh này thực chất là
   **đường cơ sở `gpt-4o-mini`**, không đo được cơ chế định tuyến nào đang hoạt động.
3. **Chênh lệch độ chính xác là do định tuyến, nhân quả sạch.** 4 câu GSM8K mà mini làm sai thì sai
   **0/3 (tất định)**; mỗi lần proxy nâng model thì câu đó **đạt 3/3**. Portkey nâng 4/4 → 30/30,
   Bifrost 2/4 → 24/30, LiteLLM 0/4 → 18/30.
4. **Lợi thế của Portkey một phần là trùng hợp.** Cả 4 câu mini trượt đều dài ≥ 225 ký tự, mọi câu
   mini làm được mà Portkey để SIMPLE đều ≤ 177 — trên GSM8K độ dài câu đố tình cờ tỷ lệ với độ khó,
   nên ngưỡng `prompt_len` thuần cú pháp hoạt động như bộ phân loại độ khó. Không bảo đảm còn đúng
   trên dữ liệu thật.
5. **Bifrost đẩy 24/30 câu MMLU lên `gpt-4o` mà vẫn chỉ 27/30 — bằng đúng LiteLLM chạy toàn mini.**
   Tiền trả thêm cho MMLU không mua được điểm nào. Xác nhận phân loại lệch đo ở smoke test 09/10.
6. **Mục 4 review của Khoa (`temperature: 0` không tất định) đã được kiểm lại trên 360 lượt:** đúng
   3/120 nhóm = **2,5%**, và cả 3 nhóm đều dùng **cùng một model** → bất định phía provider, không
   phải định tuyến bất ổn. Đã đưa vào báo cáo thành **sàn nhiễu 2,5%**, kèm hệ quả: chênh lệch dưới
   ~2,5 đpt thì không kết luận được.
7. **Chấm lại 180 lượt của Khoa trên máy mình ra đúng từng con số** (88,3 / 91,7 / 93,3) — khác biệt
   duy nhất trong file là đường dẫn thư mục tạm của 2 máy. Tức 2 bản sửa bộ chấm ở `871e756` không
   làm lệch kết quả nửa của Khoa, và phép chấm **tái lập được độc lập**.

### Cần bàn cùng nhau

**Kết luận nhạy với thành phần bộ đề — đây là chỗ cần thống nhất trước khi báo cáo.** LiteLLM qua
cổng 80% **chỉ hơn 1,7 đpt**. Chi tiết:

| Nửa bộ đề | LiteLLM | Qua cổng? |
|---|---|---|
| MMLU + GSM8K (Hùng) | **75,0%** | **KHÔNG** |
| HumanEval + IFEval (Khoa) | 88,3% | Có |
| Gộp cả 4 bộ | **81,7%** | Có (sát sàn) |

Nguyên nhân là **HumanEval bão hòa** (mini đạt 30/30 kéo điểm lên). Phân tích leave-one-out:
**2/4 biến thể giữ LiteLLM, 2/4 loại nó** — bỏ MMLU → `bifrost` thắng, bỏ HumanEval → **`portkey`**
thắng (vì HumanEval là bộ đắt nhất của Portkey nhưng rẻ nhất của Bifrost, bỏ nó ra là đảo thứ tự
chi phí). Bảng đầy đủ ở mục 7 báo cáo.

⚠️ **Tự đính chính 2 chỗ mình nói sai lúc đầu, Khoa đọc bản đã sửa:**
1. Mình từng viết "bỏ HumanEval → bifrost". **Sai** — là **portkey**, lý do ở trên.
2. Mình từng gộp "1,7 đpt" với "sàn nhiễu 2,5%". **Không so được** — sàn nhiễu là tỷ lệ *item* bất
   định, 1,7 đpt là biên của một *tỷ lệ tổng hợp*. Thực tế **nhiễu không đủ làm LiteLLM trượt cổng**:
   nó dư 2 lượt (98 vs 96/120), cần **3 lượt** flip, mà chỉ có **1/40 item** bất định. Gộp theo
   **đa số 2/3** thì LiteLLM được 33/40 = **82,5%**, vẫn qua. Chỗ yếu thật là **cỡ mẫu**: CI95 =
   [74,7%; 88,6%] theo lượt, [69,7%; 93,7%] theo item — **đều chứa 80%**.

**Quan điểm của mình:** **không sửa luật, không sửa bộ đề** — sửa sau khi đã thấy số là mất tính
khách quan, đúng nguyên tắc đã ghi ở `CLAUDE.md` mục 2. Kết luận chính thức vẫn là LiteLLM. Nhưng
phải **ghi thẳng độ nhạy này vào giới hạn** (đã làm, mục 9 của báo cáo) và **giữ `fallbacks`** khi
tích hợp thật, vì LiteLLM không bao giờ tự nâng model khi gặp prompt khó. Khoa phản biện giúp chỗ này.

**Đề xuất D14 để bàn:** cả 360 lượt chỉ tốn **$0,189**, nên nâng lên **20 item/bộ** chỉ thêm ~$0,19
mà **thu hẹp CI ~1,4 lần** — đủ để biết LiteLLM thật sự trên hay dưới 80%. Đây là cách duy nhất xử lý
giới hạn cỡ mẫu mà không phải sửa luật hay sửa bộ đề. **Nhưng phải đăng ký D14 TRƯỚC khi chạy**:
"mở rộng lên 20 item/bộ theo đúng quy trình lấy mẫu + đúng luật 4 bước, lấy kết quả trên toàn mẫu mở
rộng làm kết luận cuối, bất kể nó nói gì". Chạy thêm rồi mới chọn bộ số có lợi thì thành "chạy tới
khi ra kết quả mình thích", tệ hơn là giữ 40 item và báo cáo trung thực.
