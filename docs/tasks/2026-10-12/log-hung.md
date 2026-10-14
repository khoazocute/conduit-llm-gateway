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
