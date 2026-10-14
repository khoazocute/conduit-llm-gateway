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
