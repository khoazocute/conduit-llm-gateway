# Khảo sát 4 bộ benchmark + metric chuẩn (D10, chốt 2026-10-14)

Việc H1/H4 tuần 2026-10-12. Thiết kế thí nghiệm: `docs/experiment-design.md`.

Yêu cầu của thầy (họp 2026-10-03): *"dùng bộ prompt uy tín từ các research, bộ đánh giá cũng phải
uy tín, dùng metric"*. File này ghi lại **nguồn**, **metric chuẩn**, **chỗ lệch khỏi protocol gốc**,
và **mọi thứ cần để tái lập**.

Số liệu trong file này sinh từ `experiments/prompts/manifest.json` (do
`experiments/prompts/build_prompts.py` ghi lúc lấy mẫu) — **đừng sửa tay**, chạy lại script nếu cần.

---

## 1. Bốn bộ đã chọn

| Bộ | Đo năng lực gì | Metric chuẩn | Tự động hoá | Giấy phép |
|---|---|---|---|---|
| **MMLU** | Kiến thức học thuật đa lĩnh vực, trắc nghiệm 4 lựa chọn | accuracy | ✅ so chữ cái | MIT |
| **GSM8K** | Toán đố nhiều bước (cấp tiểu học/THCS) | exact match đáp án số cuối | ✅ trích số | MIT |
| **HumanEval** | Sinh code Python từ signature + docstring | **pass@1** | ✅ chạy test gốc | MIT |
| **IFEval** | Tuân thủ chỉ thị, sinh văn bản mở | **prompt-level strict** (đạt iff mọi ràng buộc đều theo) | ✅ verifier **chính thức** | Apache-2.0 |

**Lấy 10 item/bộ = 40 item**, mỗi item chạy 3 lần trên 3 proxy → **360 lượt**.

### Vì sao 4 bộ này

1. **Phủ 4 loại năng lực khác nhau** — kiến thức, suy luận toán, sinh code, tuân thủ chỉ thị. Đủ
   rộng để một proxy không thể "thắng nhờ may" ở một loại duy nhất.
2. **Cả 4 đều có metric chuẩn kiểm được bằng code** → không cần chấm tay, không cần trọng tài.
   Đây là điều kiện để 2 người làm xong trong thời gian còn lại.
3. **Có một bộ "sinh văn bản mở" mà vẫn chấm máy được** (IFEval) — giữ được loại prompt mở mà
   thiết kế cũ có, nhưng bỏ được rubric tự đặt.

### Đã loại MT-Bench — và vì sao điều đó quan trọng

Metric chuẩn của MT-Bench là **GPT-4 làm trọng tài** (LLM-as-judge) với prompt chấm đã công bố.
Phương án từng cân nhắc — *"lấy prompt MT-Bench rồi chấm bằng rubric 3 tiêu chí của nhóm"* —
**không hợp lệ** theo yêu cầu chuẩn-theo-paper: prompt thì uy tín nhưng **tiêu chí chấm là nhóm tự
đặt**, không thuộc paper nào. Hai lựa chọn còn lại là làm LLM-as-judge cho đúng (tốn thêm chi phí
và thêm một biến gây nhiễu là bias của judge) hoặc đổi bộ. Nhóm đổi bộ → **IFEval**.

**Kéo theo:** **D4** giải quyết xong (prompt code chấm `pass@1`, không rubric) và **D6** gần như
không còn cần (hết chấm tay → không còn ~49 output chấm kép, không còn % agreement). Mất một điểm
phương pháp nhưng bỏ được điểm chặn nhân lực lớn nhất.

---

## 2. Nguồn, phiên bản, mẫu đã lấy

Seed lấy mẫu: **20261014**. Ngày lấy: **2026-10-14**. Chạy lại cùng seed ra đúng 40 item này.

### MMLU
- **Paper:** Hendrycks et al. 2021, *Measuring Massive Multitask Language Understanding* (arXiv:2009.03300)
- **Nguồn dùng:** `cais/mmlu` trên HuggingFace, qua datasets-server API
  (`https://datasets-server.huggingface.co/rows?dataset=cais%2Fmmlu&config=all&split=test`)
- **Split:** `all/test` — **14042** item · lấy 10 · index: `1044, 3291, 5397, 7492, 8230, 8929, 12795, 12829, 12962, 14037`
- **sha256** (nối các response đã tải): `5ac0c0f23451…`
- *Dùng API thay vì tar gốc 166MB của Hendrycks — nội dung tương đương, tải nhẹ hơn nhiều.*

### GSM8K
- **Paper:** Cobbe et al. 2021, *Training Verifiers to Solve Math Word Problems* (arXiv:2110.14168)
- **Nguồn dùng:** `openai/grade-school-math`, `grade_school_math/data/test.jsonl`
- **Split:** `test` — **1319** item · lấy 10 · index: `21, 61, 82, 397, 406, 432, 901, 985, 1075, 1249`
- **sha256:** `3730d312f6e3…`
- Đáp án đúng nằm sau `####` trong field `answer` của dataset.

### HumanEval
- **Paper:** Chen et al. 2021, *Evaluating Large Language Models Trained on Code* (arXiv:2107.03374)
- **Nguồn dùng:** `openai/human-eval`, `data/HumanEval.jsonl.gz`
- **Bộ duy nhất** — **164** bài · lấy 10 · index: `25, 34, 44, 75, 105, 113, 131, 140, 143, 150`
- **sha256:** `b796127e635a…`
- `prompts.json` lưu kèm `entry_point` và **bộ test gốc** của từng bài để chạy `pass@1`.

### IFEval
- **Paper:** Zhou et al. 2023, *Instruction-Following Evaluation for Large Language Models* (arXiv:2311.07911)
- **Nguồn dùng:** `google-research/google-research`, `instruction_following_eval/data/input_data.jsonl`
- **Bộ duy nhất** — **541** prompt · lấy 10 · index: `31, 124, 180, 187, 287, 337, 448, 496, 534, 536`
- **sha256:** `67ffeee0fcb8…`
- `prompts.json` lưu kèm `instruction_id_list` và `kwargs` để chạy verifier.

---

## 3. Metric — định nghĩa dùng khi chấm

| Bộ | Tên trong `prompts.json` | Cách chấm 1 lượt |
|---|---|---|
| MMLU | `accuracy_letter` | Trích chữ cái (A/B/C/D) từ câu trả lời, so với `expected_answer`. Đạt = khớp |
| GSM8K | `exact_match_number` | Trích **số cuối cùng** trong câu trả lời, so với `expected_answer` (số sau `####` của dataset). Đạt = khớp |
| HumanEval | `pass_at_1` | Ghép code model sinh ra với **bộ test gốc** của bài, chạy trong sandbox. Đạt = test pass |
| IFEval | `ifeval_strict_prompt` | Chạy **verifier chính thức** cho từng `instruction_id`. **Đạt = mọi** ràng buộc đều theo (prompt-level strict). Ghi thêm `score` = tỷ lệ ràng buộc theo được (instruction-level) để báo cáo |

**Accuracy tổng của một proxy = tỷ lệ item đạt trên toàn bộ 40 item.** Khác thiết kế cũ (chỉ 12/30
item closed-QA vào cổng chất lượng) — giờ **40/40 item** đều có metric khách quan nên cổng ở bước 1
của luật quyết định phủ toàn bộ. Lượt lỗi tính vào mẫu số và coi là sai (D7).

### ⚠️ Cần Khoa đối chiếu lại với paper gốc (review chéo)

Các định nghĩa trên đủ dùng để code, nhưng **ba chỗ phải xác nhận từ paper/code gốc trước khi chạy
chính thức** — đây là phần review chéo của Khoa:

1. **IFEval có 4 biến thể metric** trong paper (prompt-level / instruction-level × strict / loose).
   Nhóm chọn **prompt-level strict** làm `passed` — lý do: cổng ở bước 1 của luật quyết định là nhị
   phân "item đạt / không đạt", khớp với 3 bộ còn lại. **Instruction-level strict vẫn được ghi** vào
   `score` của từng lượt để báo cáo. ✅ **Đã dùng verifier chính thức** — vendor nguyên văn ở
   `experiments/analysis/vendor/instruction_following_eval/` (Apache-2.0, 25 verifier, bộ đề cần 12
   loại, có test kiểm đủ). Khoa cần xác nhận lại tên gọi 2 biến thể này đúng như paper.
2. **`pass@1` của HumanEval** — paper định nghĩa `pass@k` kèm ước lượng không chệch khi sinh nhiều
   mẫu. Nhóm sinh **1 mẫu/lượt ở temperature 0**, nên `pass@1` ở đây là tỷ lệ bài pass trực tiếp.
   Cần xác nhận cách này khớp với cách paper báo `pass@1` greedy.
3. **Trích đáp án GSM8K** — "số cuối cùng trong câu trả lời" là quy ước phổ biến cho 0-shot, không
   phải quy định của paper. Cần kiểm trên 10 item thật xem có ca nào bị trích sai (vd. model viết
   đơn vị hoặc năm ở cuối câu).

---

## 4. Chỗ lệch khỏi protocol gốc — **phải nêu trong báo cáo**

**Tất cả đều 0-shot.** Protocol gốc: MMLU **5-shot**, GSM8K **8-shot CoT**. Lý do lệch: few-shot làm
prompt dài gấp nhiều lần → nhánh Portkey định tuyến theo `metadata.prompt_len` sẽ đẩy **mọi** câu
sang model đắt, heuristic mất sạch ý nghĩa (xem `docs/routing-policy.md` mục 7). Nhóm **không** so
với điểm công bố của các model, chỉ so **giữa 3 proxy trên cùng bộ đề** — nên nội bộ nhất quán là đủ.

| Bộ | Chỗ lệch |
|---|---|
| **MMLU** | 0-shot thay 5-shot. Giữ layout Hendrycks (câu hỏi + 4 lựa chọn A–D) nhưng **thêm 1 dòng chỉ thị** `"Answer with the letter only (A, B, C, or D)."` — cần cho chat model, vì protocol gốc thiết kế cho completion model có few-shot dẫn dắt định dạng |
| **GSM8K** | 0-shot thay 8-shot CoT. Prompt là câu hỏi **nguyên văn**, không thêm chỉ thị nào |
| **HumanEval** | Prompt gốc (signature + docstring) giữ nguyên, **thêm 1 dòng** `"Complete the function above. Reply with the complete function implementation only."` — cần cho chat model, vì protocol gốc là completion thuần |
| **IFEval** | Prompt **nguyên văn, tuyệt đối không thêm gì** — IFEval kiểm tra chính việc tuân thủ chỉ thị, thêm chữ nào cũng có thể phá ràng buộc đang được kiểm (vd. ràng buộc số từ, từ bị cấm) |

Hệ quả cần nhớ khi đọc kết quả: **con số accuracy ở đây không so được với bảng xếp hạng công bố**
của các model. Chúng chỉ dùng để so 3 proxy với nhau.

---

## 5. Tham số sinh — giống nhau cả 3 proxy (D7)

| Tham số | Giá trị | Lý do |
|---|---|---|
| `max_tokens` | **512** | Đủ dài để chấm được (câu trả lời 16 token thì không chấm nổi), đủ ngắn để chặn generation chạy dài và không chạm `REQUEST_TIMEOUT` 45s |
| `temperature` | **0** | Yêu cầu của `pass@1` greedy; dùng chung cả 4 bộ cho nhất quán |
| `num_retries` | 2 | D7 |
| `timeout` | 45s | D7 |

⚠️ `HttpProxyChatClient.complete()` hiện **chưa gửi `max_tokens`/`temperature`** — việc K3 của Khoa
(Phase 1). Trước khi có, D7 chưa thực sự được thực thi qua đường đi của app.

---

## 6. Tái lập

```bash
# Cài thư viện (lần đầu) — BẮT BUỘC cả bước tải nltk corpus, thiếu là verifier IFEval nổ
python -m pip install -r experiments/requirements.txt
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('punkt')"

# Sinh lại đúng 40 item (cùng seed -> cùng mẫu). Cache trong experiments/prompts/.cache/ (gitignored).
PYTHONIOENCODING=utf-8 python experiments/prompts/build_prompts.py

# Kiểm schema + trường bắt buộc để chấm
PYTHONIOENCODING=utf-8 python experiments/prompts/validate_prompts.py

# Bộ 30 prompt tiếng Việt (phép thử nhạy ngôn ngữ của Bifrost, không phải bộ đánh giá chính)
PYTHONIOENCODING=utf-8 python experiments/prompts/validate_prompts.py --vi

# Chấm offline file kết quả thô (sau khi runner chạy xong)
PYTHONIOENCODING=utf-8 python experiments/scripts/grade_results.py experiments/results/run_*.json --db
PYTHONIOENCODING=utf-8 python experiments/scripts/grade_results.py ... --skip pass_at_1   # phương án lùi
```

Mọi thứ cần để tái lập nằm trong `experiments/prompts/manifest.json`: URL nguồn, sha256 file đã tải,
tổng số row, seed, index đã chọn, tham số decoding, và ngưỡng `prompt_len` của Portkey.
