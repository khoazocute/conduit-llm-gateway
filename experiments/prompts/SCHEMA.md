# Schema của `prompts.json`

30 prompt, phân theo 3 nhóm (CLAUDE.md mục 2): `closed_qa` (12, gồm kiến thức +
toán + logic), `code` (6), `open_ended` (12).

Chỉ `closed_qa` có đáp án đúng/sai khách quan → cần trường đáp án để chấm tự động.
`code` và `open_ended` chấm rubric 3 tiêu chí thủ công (chấm mù) → không có đáp án.
(`code` chấm rubric là phương án D4 đang đề xuất, chờ chốt; nếu D4 đổi sang chạy test
thì thêm `expected_answer`/`match_type` cho `code`, validator đã chấp nhận.)

Luật khớp cài ở `experiments/analysis/grading.py`; kiểm tra file bằng
`python experiments/prompts/validate_prompts.py`, test luật bằng
`python -m unittest discover -s experiments/tests -v`.

## `closed_qa`

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | string | Định danh duy nhất, vd `cq_01`, `code_01` |
| `prompt` | string | Nội dung prompt gửi cho model |
| `expected_answer` | string | Đáp án đúng dùng để so khớp tự động |
| `match_type` | `"exact" \| "contains" \| "regex"` | Cách so khớp `expected_answer` với response |

## `open_ended`

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | string | Định danh duy nhất, vd `oe_01` |
| `prompt` | string | Nội dung prompt gửi cho model |

Không có `expected_answer` — chấm bằng rubric 3 tiêu chí (on-task / độ dài phù hợp /
không lỗi), mỗi tiêu chí 0–1 điểm, chấm mù (ẩn tên proxy), 30% mẫu chấm bởi 2 người
độc lập để báo cáo % agreement (xem CLAUDE.md mục 2).
