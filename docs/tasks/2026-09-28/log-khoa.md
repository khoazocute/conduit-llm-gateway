# Log tuần 28/09 – 04/10/2026 — Khoa

Điền dần trong tuần, mỗi mục việc xong thì thêm 1 dòng vào bảng, không cần viết văn xuôi dài nếu
không có gì đặc biệt. Commit kèm code, không paste vào chat — Hùng tự đọc qua `git pull`.

## Việc đã làm

| Việc | Kết quả | File/commit | Hùng cần làm |
|---|---|---|---|
| Merge `lhung` → `dangkhoa` | ✅ Lấy H1–H5 + J2 trước khi làm K1 (K1 sửa cùng file `HttpProxyChatClient`), không conflict | commit merge | — |
| **K1** — Bifrost `fallbacks` theo D2 + retry theo D7 | ✅ Chuỗi đủ 5 model **theo giá thật**: `gpt-4o-mini` → `gemini-flash` → `claude-haiku` → `claude-sonnet` → `gpt-4o`; backend gửi kèm `fallbacks` mỗi request (model chính = model app gửi, 4 model còn lại theo thứ tự). Bifrost `max_retries: 2`, timeout 45s cho cả 3 provider. Unit test 4/4. Qua app: lượt thường 43/43 (`gpt-4o-mini`); **ép OpenAI lỗi 401** → Bifrost thử gpt-4o-mini → gemini-flash (retry 2, lỗi tạm) → **claude-haiku** thành công, app ghi đúng `selected_model` + giá claude-haiku, 43/43 | `application.yml`, `ChatProxyProperties.java`, `HttpProxyChatClient.java`, `ChatProxyPropertiesTest.java`, `proxy-configs/bifrost/setup.sh`, `proxy-configs/bifrost/fallback-test.sh`, `docs/bifrost-routing-notes.md` mục 8 | Review chéo: `BIFROST_URL=… bash proxy-configs/bifrost/setup.sh` (máy Hùng bỏ `BIFROST_URL`), rồi `fallback-test.sh break` → chat qua app với `CHAT_ACTIVE_PROXY=bifrost` → `fallback-test.sh restore` |
| **K3** — `response_quality_score` | ✅ Trước đây **không nơi nào ghi cột này**. Runner giờ ghi ngay sau khi chấm closed-QA (1 đúng / 0 sai) vào `routing_decisions`, và lưu `message_id` vào file kết quả để nạp điểm chấm mù (18 câu code+mở, tổng rubric / 3) sau. Verify: 1 prompt qua Bifrost và 1 qua LiteLLM `conduit-pool` → đủ 3 dòng ở 3 bảng, mọi cột có giá trị, `response_quality_score = 1` | `experiments/scripts/run_experiment.py`, `experiments/results/run_bifrost_20261001T153150Z.json`, `run_litellm_20261001T153711Z.json` | Đọc thay đổi trong runner (file của Hùng): `record_quality_score`, `message_id`, `elapsed_ms` |
| **K2** — C03 | ✅ Lý do cho 0.5: phương án "dấu chấm phẩy" trong câu trả lời là sai (chạy thử: `print` thành lệnh trong thân hàm, sau `return`, không bao giờ chạy). Đề xuất giữ 0.5 + quy ước cho prompt "nêu lỗi" | `docs/grading-rubric.md` mục 7 | Đồng ý hoặc phản biện, ghi kết luận cuối vào mục 7 |
| **J2** — đọc `routing-policy.md` | 🟨 Đồng ý mục 1–4 và 3 điểm của mục 5. **Bổ sung 3 điểm** (mục 5, điểm 4–6) + cập nhật trạng thái Bifrost (mục 2, 4, 6) | `docs/routing-policy.md` | Đọc mục 5 điểm 4–6; nếu đồng ý thì J2 xong |
| **J3** — review chéo phần của Hùng | ✅ LiteLLM, Portkey, runner, `decision_rule.py` đều dựng lại và chạy được trên máy Khoa. Tìm được 4 điểm cần xử lý trước dry-run | `docs/tasks/2026-09-28/log-hung.md` mục "Review — Khoa" | Đọc review |
| Regression | ✅ `e2e_workflow_test.sh` 43/43 qua **cả 3 proxy**, `e2e_test.sh` 48/48, test Python 22/22, `validate_prompts.py` OK | — | — |
| Sửa `dry_run.sh` trước dry-run (02/10) | ✅ (1) LiteLLM chạy `CHAT_DEFAULT_MODEL=conduit-pool` (review điểm 1); (2) `.env` CRLF → bỏ `\r` khi `source`, không thì mọi key dính `\r`; (3) chỉ dừng tiến trình giữ cổng 8081 thay vì mọi `java.exe` (tránh tắt Java language server của IDE) | `experiments/scripts/dry_run.sh` | Đọc diff (file của Hùng) |
| **Dry-run 27 lượt** (02/10) | ✅ 3 prompt (`cq_01`–`cq_03`, closed-QA) × 3 proxy × 3 lần. **27/27 thành công, 27/27 đúng**, mọi lượt đủ 3 bảng + `response_quality_score`. Cả 27 lượt đều `gpt-4o-mini` (không lượt nào phải fallback). `decision_rule.py` chọn **LiteLLM** — nhưng xem phát hiện 6, chênh lệch là nhiễu | `experiments/results/run_{litellm,bifrost,portkey}_20261002T16*.json` | Đọc phát hiện 6–7 |

## Phát hiện quan trọng

1. **`decision_rule.py` thưởng cho proxy hay lỗi.** Lượt lỗi có `cost = 0` được tính vào chi phí trung
   bình. Dữ liệu giả: proxy B đắt hơn A 2%/lượt và lỗi 4/36 lượt → chi phí TB của B thấp hơn → **luật
   chọn B**. Có thể làm sai kết luận chính của khóa luận nếu không sửa trước Phase E.
2. **`dry_run.sh` không dùng routing thật của LiteLLM** (không đặt `CHAT_DEFAULT_MODEL=conduit-pool`)
   → dry-run sẽ đo LiteLLM như 1 proxy chuyển tiếp thường.
3. **Khi không lỗi, cả 3 proxy đều gọi `gpt-4o-mini`** → thí nghiệm thực chất đo overhead độ trễ và cách
   xử lý lỗi, không đo việc chọn model (`routing-policy.md` mục 5, điểm 4).
4. **Bifrost tự retry rồi mới fallback:** trong lượt ép lỗi, Gemini lỗi tạm thời, Bifrost retry đúng 2
   lần rồi mới chuyển sang Claude Haiku — log Bifrost (`/api/logs`) ghi rõ `fallback_index` và
   `number_of_retries` từng bước, dùng được làm bằng chứng cho báo cáo.
5. **Cấu hình Bifrost không nằm trong git** (SQLite trong volume) → giờ có `setup.sh` dựng lại; giữ
   nguyên khi tạo lại container.
6. **Dry-run xác nhận phát hiện 3 bằng số thật — chênh lệch chi phí giữa 3 proxy là nhiễu.** Kết quả:

   | Proxy | Đúng | Chi phí TB/lượt | Token vào TB | Token ra TB | p95 (runner) | p95 (backend) |
   |---|---|---|---|---|---|---|
   | LiteLLM | 9/9 | $4.06e-05 | 20.7 | 62.4 | 4155 ms | 3681 ms |
   | Portkey | 9/9 | $4.62e-05 | 20.7 | 71.8 | 3187 ms | 2868 ms |
   | Bifrost | 9/9 | $4.99e-05 | 20.7 | 78.0 | 3087 ms | 2768 ms |

   Cùng model, cùng giá, **token vào y hệt nhau** — chi phí chỉ khác vì độ dài câu trả lời
   `gpt-4o-mini` dao động ngẫu nhiên (29–106 token ra). LiteLLM "rẻ nhất" 19% là may, không phải nhờ
   routing; với 9 lượt/proxy, lần chạy khác có thể ra proxy khác. Nếu Phase E vẫn như vậy, bước 2 của
   luật quyết định sẽ chọn theo nhiễu → cần bàn (xem mục "Cần bàn").
7. **LiteLLM chậm nhất** (p95 backend 3681 ms so với ~2800 ms), có thể do bước tính giá của
   `cost-based-routing` — mẫu 9 lượt còn nhỏ, chưa kết luận. Độ trễ runner cao hơn backend 300–500 ms
   (đúng điểm review 2), nhưng đều nhau giữa 3 proxy nên thứ hạng không đổi.

## Cần bàn / chốt cùng nhau

- Cách tính "chi phí trung bình/prompt" ở bước 2 của luật quyết định: trên lượt thành công, hay trên
  mọi lượt (lượt lỗi = 0)? — phát hiện 1.
- Portkey có cần thêm fallback để khớp D2 không (`routing-policy.md` mục 5, điểm 5).
- Có nên hỏi GVHD về phát hiện 3 không (cả 3 proxy cùng 1 model ở lượt bình thường). **Dry-run đã
  xác nhận bằng số thật (phát hiện 6)** — câu hỏi cụ thể: khi 3 proxy gọi cùng model, chênh lệch chi
  phí chỉ là nhiễu độ dài câu trả lời; có nên so chi phí theo **token vào** / chi phí của **model được
  chọn**, hoặc thêm kịch bản ép lỗi để fallback thật sự phân biệt 3 proxy không?
- Timeout 2 tầng (`routing-policy.md` mục 5, điểm 6) — chỉ cần ghi vào phần giới hạn, không nhất thiết
  sửa.
- **Câu hỏi cho GVHD** (`roadmap.md` mục 6): _Khoa cần tự cập nhật đã hỏi/hẹn chưa._

## Còn thiếu / chưa xác nhận được

- Dry-run 27 lượt đã chạy 02/10 (phát hiện 2 đã sửa trước khi chạy). Phát hiện 1 (`decision_rule.py`
  tính lượt lỗi cost = 0) **chưa sửa** — chờ chốt với Hùng; dry-run không có lượt lỗi nên kết quả
  lần này không bị ảnh hưởng.
- Dry-run chỉ gồm closed-QA (`--limit 3` lấy 3 prompt đầu) — chưa thử runner với prompt code/mở.
- Chưa có bước nạp điểm chấm mù (18 câu code+mở) vào `response_quality_score` — chỉ cần khi có dữ liệu
  chấm thật ở Phase E; runner đã lưu sẵn `message_id` để làm.
- K4 (Complexity Router) không làm — D2 đã quyết định không dùng.
