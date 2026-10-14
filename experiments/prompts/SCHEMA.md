# Schema của `prompts.json`

**Đổi 2026-10-14 (D10).** Bộ đánh giá chính là **4 bộ benchmark công khai, 0-shot, 10 item/bộ =
40 item**. Thiết kế: `docs/experiment-design.md` mục 5 · khảo sát nguồn + metric:
`docs/benchmark-survey.md`.

Sinh bằng `build_prompts.py` (seed cố định) — **đừng sửa tay**:

```bash
PYTHONIOENCODING=utf-8 python experiments/prompts/build_prompts.py   # sinh prompts.json + manifest.json
PYTHONIOENCODING=utf-8 python experiments/prompts/validate_prompts.py
```

Mọi thứ cần tái lập (URL nguồn, sha256, split, seed, index đã chọn, tham số decoding, ngưỡng
`prompt_len` của Portkey) nằm ở `manifest.json`.

## 4 nhóm, mỗi nhóm đúng 10 item

| Nhóm | `metric` | Trường bắt buộc riêng |
|---|---|---|
| `mmlu` | `accuracy_letter` | `expected_answer` ∈ {A,B,C,D} |
| `gsm8k` | `exact_match_number` | `expected_answer` là một số |
| `humaneval` | `pass_at_1` | `entry_point`, `test` (bộ test gốc, phải chứa `def check(`), `signature_prompt` |
| `ifeval` | `ifeval_strict_prompt` | `instruction_id_list` (list không rỗng), `kwargs` (list) |

## Trường chung của mọi item

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | string | Định danh duy nhất, vd `mmlu_01`, `humaneval_07` |
| `prompt` | string | Nội dung gửi cho model, **0-shot** (xem chỗ lệch protocol ở `benchmark-survey.md` mục 4) |
| `metric` | string | Metric chuẩn của bộ đó — phải khớp bảng trên |
| `source_index` | int | Index trong dataset gốc, để tái lập mẫu |

Trường tuỳ bộ: `subject` (mmlu), `source_id` + `signature_prompt` (humaneval), `source_key` (ifeval).

`signature_prompt` = prompt gốc chưa thêm dòng chỉ thị — bộ chấm cần nó để ghép lại khi model
chỉ trả về thân hàm.

## Chấm điểm diễn ra ở đâu

**Offline, sau khi chạy** — không phải trong runner. `run_experiment.py` chỉ thu output và ghi
`passed: null`; `experiments/scripts/grade_results.py` điền `passed` / `score` / `grade_detail` theo metric
của từng bộ (bộ chấm: `experiments/analysis/graders.py`). Lý do:
`pass_at_1` phải chạy code trong sandbox và IFEval phải chạy verifier, nên thu output và chấm điểm
tách nhau — nếu một bộ chấm chưa xong thì vẫn chạy được thí nghiệm và bù chấm sau.

`decision_rule.py` đọc `passed` của từng record (fallback `closed_qa_correct` cho dữ liệu thô trước
2026-10-14) và **không** tự chấm lại. Lượt thành công nhưng chưa chấm được đếm riêng ở
`pareto_data.ungraded_runs`, **không** âm thầm tính là sai.

## `prompts-vi-30.json` — bộ cũ, schema cũ, vẫn dùng

Bộ 30 prompt tiếng Việt tự soạn (12 `closed_qa` + 6 `code` + 12 `open_ended`, trường
`expected_answer` + `match_type` ∈ {exact, contains, regex}). **Không còn là bộ đánh giá chính**,
nhưng giữ lại làm **phép thử nhạy ngôn ngữ của Bifrost** (`docs/experiment-design.md` mục 9 điểm 3).

Validate bằng: `python experiments/prompts/validate_prompts.py --vi`
