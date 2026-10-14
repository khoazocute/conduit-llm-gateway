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
| **Dry-run 27 lượt** (02/10) | ✅ 3 prompt (`cq_01`–`cq_03`, closed-QA) × 3 proxy × 3 lần. **27/27 thành công, 27/27 đúng**, mọi lượt đủ 3 bảng + `response_quality_score`. Cả 27 lượt đều `gpt-4o-mini` (không lượt nào phải fallback). **Chi phí thực: $0.0012297** (LiteLLM $0.0003651, Bifrost $0.0004491, Portkey $0.0004155; = 3716 credit), khớp giữa file kết quả và `usage_logs`. `decision_rule.py` chọn **LiteLLM** — nhưng xem phát hiện 6, chênh lệch là nhiễu. Lần chạy đầu dừng ngay do lỗi script (chưa gọi lượt nào, DB không đổi) → sửa rồi chạy lại | Kết quả thô: `experiments/results/run_{litellm,bifrost,portkey}_20261002T16*.json`; gộp + kết quả luật: `experiments/results/dry-run-20261002/` | Đọc phát hiện 6–8 |
| Kiểm tra lại dry-run (02/10) | ✅ (1) **LiteLLM thật sự đi qua `conduit-pool`**: `/model/info` cho thấy deployment `gpt-4o-mini` gọi thẳng có id dạng hash, còn deployment trong pool có id `gpt-4o-mini` — cả 9 dòng LiteLLM ghi `gpt-4o-mini` nên là từ pool (không tốn lượt gọi để kiểm tra). (2) **Đối chiếu tay** (roadmap Phase D): 19 token vào + 62 ra × giá gpt-4o-mini = $0.00004005 = DB; credit ceil(81 × 1.5) = 122 = DB; lượt thứ 2 (19 + 38) cũng khớp ($0.00002565, 86 credit) | — | — |

## Phát hiện quan trọng

1. **`decision_rule.py` thưởng cho proxy hay lỗi.** Lượt lỗi có `cost = 0` được tính vào chi phí trung
   bình. Dữ liệu giả: proxy B đắt hơn A 2%/lượt và lỗi 4/36 lượt → chi phí TB của B thấp hơn → **luật
   chọn B**. Có thể làm sai kết luận chính của khóa luận nếu không sửa trước Phase E.
2. **`dry_run.sh` không dùng routing thật của LiteLLM** (không đặt `CHAT_DEFAULT_MODEL=conduit-pool`)
   → dry-run sẽ đo LiteLLM như 1 proxy chuyển tiếp thường. **Đã sửa 02/10**, trước khi chạy dry-run.
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
8. **Chỉ Bifrost có bằng chứng chuyển model khi lỗi.** LiteLLM: `routing-policy.md` ghi chưa cấu hình
   `fallbacks`, và **chưa ai thử ép lỗi** — không biết khi `gpt-4o-mini` lỗi thì `conduit-pool` có tự
   sang `gemini-flash` không (đừng giả định là có). Portkey: chắc chắn không (rule 1-1). Vậy ở phần "độ
   bền" mới so được 1/3 proxy.

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

## Cần chỉnh sửa trước Phase E

Xếp theo mức ảnh hưởng tới kết luận khóa luận.

| # | Việc | Vì sao | Ai | Tốn tiền? |
|---|---|---|---|---|
| 1 | `decision_rule.py`: chi phí TB tính trên **lượt thành công** (tổng chi phí / số lượt thành công) + thêm test | Phát hiện 1 — đang thưởng cho proxy hay lỗi | Hùng (file của Hùng), sau khi chốt | Không |
| 2 | Chốt với GVHD cách xử lý phát hiện 6 (3 proxy cùng model → bước 2 chọn theo nhiễu) | Không xử lý thì Phase E chọn proxy gần như ngẫu nhiên | Cả hai + GVHD | Không |
| 3 | Ép lỗi LiteLLM 1 lượt (giống `fallback-test.sh` của Bifrost) + ghi rõ trong `routing-policy.md` mục 3 **lý do** bật/không bật fallback từng proxy (roadmap Phase C yêu cầu; hiện LiteLLM chưa có lý do, Portkey "static nên ít cần" còn yếu) | Phát hiện 8 — mới so được độ bền 1/3 proxy | Khoa (thử), cả hai chốt | 1–2 lượt tầng rẻ |
| 4 | `decision_rule.py` dùng `latency_ms` do backend đo thay vì runner | Review điểm 2 — runner cộng thêm 300–500 ms | Hùng | Không |
| 5 | `dry_run.sh` tự gộp 3 file kết quả + chạy `decision_rule.py` ở cuối | Roadmap Phase D: "một lệnh chạy hết dry-run" ra bảng tổng hợp — hiện phải gộp tay | Ai rảnh | Không |
| 6 | Portkey: thêm fallback hay ghi thành giới hạn | `routing-policy.md` mục 5 điểm 5 | Cả hai chốt | Không |
| 7 | 2 nhánh nhỏ của `decision_rule.py`: hoà cả 4 bước thì lặng lẽ chọn proxy đầu; lượt lỗi `model_selected = None` bị tính như 1 model ở consistency | Review điểm 3 | Hùng | Không |

## Lưu ý môi trường (máy Khoa)

- Port bị remap (`docker-compose.override.yml`, gitignored): Postgres `5433`, Bifrost `18080`. Chạy
  `dry_run.sh` phải export trước `SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5433/conduit
  BIFROST_BASE_URL=http://localhost:18080/v1` (đã ghi trong đầu script).
- Docker Desktop khởi động lại thì các container `conduit-*` **không tự chạy lại** → `docker compose up -d
  postgres redis litellm bifrost portkey`, rồi `BIFROST_URL=http://localhost:18080 bash
  proxy-configs/bifrost/setup.sh` để chắc chắn D7 còn nguyên (02/10: còn nguyên, key giả từ lần ép lỗi
  đã gỡ).
- Chạy test Python bằng `python -m unittest discover -s tests` trong `experiments/` (máy không có pytest).

## Còn thiếu / chưa xác nhận được

- Dry-run chỉ gồm closed-QA (`--limit 3` lấy 3 prompt đầu) — chưa thử runner với prompt code/mở.
- Roadmap Phase C "Đạt khi" cần `routing-policy.md` được **cả hai + GVHD** đồng ý — mới có Khoa.
- Chưa push (`dangkhoa` đang đi trước `origin/dangkhoa`) → Hùng chưa review được K1/K3/dry-run.
- Chưa có bước nạp điểm chấm mù (18 câu code+mở) vào `response_quality_score` — chỉ cần khi có dữ liệu
  chấm thật ở Phase E; runner đã lưu sẵn `message_id` để làm.
- K4 (Complexity Router) không làm — D2 đã quyết định không dùng.

## Review — Hùng (2026-10-03)

Đã merge `main` (K1/K2/K3 + dry-run) vào `lhung` trước khi đọc — không conflict. Xử lý bảng
"Cần chỉnh sửa trước Phase E":

- **#1 (chi phí tính cả lượt lỗi) — đã sửa.** `compute_avg_cost` giờ chỉ tính trên `status=success`.
  Viết test tái tạo đúng kịch bản Khoa mô tả (proxy đắt hơn 2%/lượt nhưng lỗi 4/36) — xác nhận lỗi cũ
  có thật (sanity check trong test) và đã hết sau khi sửa, luật chọn đúng proxy rẻ hơn thật. Thêm
  `compute_error_rate()`, luôn hiện trong `pareto_data` để không giấu rủi ro độ tin cậy dù không gộp
  vào chi phí. Chạy lại trên `dry-run-20261002/merged.json` thật — kết quả không đổi (27/27 không lỗi,
  đúng như kỳ vọng, không phải regression).
- **#4 (latency_ms runner cộng overhead) — đã sửa.** `run_experiment.py` giờ ghi `latency_ms` từ
  `messages.latency_ms` (backend tự đo), giữ `latency_ms_runner` (giá trị cũ) làm cột đối chiếu/debug,
  không dùng cho `decision_rule.py`.
- **#5 (dry_run.sh tự gộp + chạy luật) — đã làm.** Cuối mỗi lần chạy, tự gộp các file `run_<proxy>_*`
  mới nhất (kể cả proxy báo lỗi giữa chừng — vẫn giữ record đã ghi được) vào
  `experiments/results/dry-run-<timestamp>/merged.json`, chạy `decision_rule.py` luôn, in + lưu
  `decision_rule_output.json`. Test lại đoạn gộp bằng 3 file dry-run thật của Khoa — ra đúng kết quả
  cũ.
- **#7 (hòa 4 bước chọn lặng lẽ + lỗi tính như 1 model ở consistency) — đã sửa phần "chọn lặng lẽ".**
  `apply_decision_rule` giờ trả thêm `tie_unresolved`/`tied_candidates` nếu hòa tuyệt đối tới hết bước
  4 — không còn `max()` âm thầm chọn phần tử đầu. Phần "lỗi tính như 1 model" ở consistency: **giữ
  nguyên có chủ đích**, không coi là bug — đã đổi sentinel từ `""` sang `_ERROR_SENTINEL` tường minh +
  viết rõ lý do trong docstring (lỗi = 1 dạng mất nhất quán thật sự, không phải trường hợp trung lập).
  Nếu Khoa thấy cách hiểu này sai thì nói lại, dễ đổi.
- Test: `experiments/tests/test_decision_rule.py` 26/26 pass (10 test mới/sửa).

**Còn mở, cần cả hai/GVHD, chưa tự quyết:**
- #2 (phát hiện 6 — 3 proxy cùng model ở lượt bình thường, chênh chi phí là nhiễu): đồng ý đây là vấn
  đề thật, chưa có hướng xử lý — cần bàn trực tiếp, có thể đưa vào câu hỏi GVHD (roadmap mục 6).
- #3 (ép lỗi LiteLLM): để Khoa làm như đã ghi, Hùng không tự làm thay.
- #6 (Portkey fallback hay ghi hạn chế): chưa chốt, đọc `routing-policy.md` mục 5 rồi bàn tiếp.
