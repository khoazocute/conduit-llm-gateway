# Log Hùng — tuần 2026-11-09 (hạn nộp bản nháp 27/11)

## 10/11

| Task | Kết quả | Commit | File chính | Khoa cần làm |
|---|---|---|---|---|
| **TASK-72** | Baseline D18 chạy đúng thiết kế đã đăng ký: 3 nhánh × 80 item × 1 lần qua app (`litellm`, `CHAT_DEFAULT_MODEL` = model). 240/240 lượt đúng model. **Chi phí thực $0,2553 / 241 lượt tính phí** (trần $0,40) | (commit này) | `experiments/results/d18-baseline-20261110/`, `experiments/analysis/baseline_report.py`, `experiments/tests/test_baseline_report.py`, `docs/experiment-results.md` mục 14 | Review mục 14 + chạy lại `baseline_report.py` (offline, miễn phí) |

Test phần thí nghiệm: 72 → **83/83** (thêm 11 test cho `baseline_report.py`, dữ liệu giả).

Số chính (chi tiết `experiment-results.md` mục 14):

| Điểm | Độ chính xác | Chi phí TB/lượt | Đường biên |
|---|---|---|---|
| Chỉ `gpt-4o-mini` | 85,0% | $0,000122 | có |
| Chỉ `claude-haiku` | 91,3% | $0,001164 | không |
| Chỉ `gpt-4o` | 91,3% | $0,001896 | không |
| Cận trên (oracle, 3 model) | 97,5% | $0,000326 | — |

## Phát hiện quan trọng

1. **LiteLLM không nằm trên đường biên Pareto**: nhánh "chỉ `gpt-4o-mini`" vừa rẻ hơn 1% vừa đúng hơn
   1,25 đpt. Cả hai chênh lệch đều dưới sàn nhiễu (2,9 đpt), và là cùng một model, nên thực chất đây là
   một điểm. Đã ghi nguyên văn theo D18 mục 8, **không** chọn lại proxy.
2. **Portkey trội chặt cả hai baseline đắt**: ngang độ chính xác của "chỉ `gpt-4o`" mà chỉ tốn 42% chi phí.
   Đây là bằng chứng định tuyến có ích ở mức chính xác cao.
3. **Bifrost hơn "chỉ `gpt-4o-mini`" 2,5 đpt, dưới sàn nhiễu, với chi phí gấp 4,6 lần.**
4. **Cận trên cách xa mọi proxy**: 97,5% với 41% chi phí của Portkey, chỉ cần chuyển 10/80 item. Dùng
   cho phần thảo luận và hướng phát triển.
5. **Kiểm đo đúng đạt**: nhánh mini lệch kết quả đa số của LiteLLM 3/80 item (ngưỡng 4).
6. **1 lượt lỗi phía máy chạy** (`humaneval_12` của haiku, `WinError 1455`: hết bộ nhớ ảo khi chạy
   backend + Docker + runner cùng lúc). Model đã trả lời và đã tính phí trước khi runner lỗi, nên
   chạy lại tốn thêm $0,0007. Lần sau chạy đợt dài thì tắt bớt ứng dụng khác.

## Cần bàn cùng nhau

- Biểu đồ `tables/cost_accuracy.png` dùng cho mục 5.2.6. Khoa xem có muốn thêm điểm nào không trước khi chèn vào Doc.
