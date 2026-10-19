# Tuần 2026-10-12 → 2026-10-18 — việc được giao

**Bản này thay bản nháp Khoa dựng 13/10.** Giữ nguyên cách chia việc của Khoa; thay đổi là vì **hai
việc thử khả thi đã chạy thật ngày 09/10 và 14/10 và đã có kết luận** (mục 3). Đừng làm lại hai việc đó.

**Bài toán: đọc `docs/experiment-design.md` trước.** File đó là nguồn đúng — câu hỏi nghiên cứu,
biến, 3 nhánh, bộ đánh giá, luật quyết định, giả thuyết, giới hạn. Không cần đọc lại chat.

**Mục tiêu tuần: có kết quả thực nghiệm trước hết ngày 17/10.** Chia 4 phase, mỗi phase 1 ngày.

Quy ước giữ nguyên: mỗi người ghi `log-hung.md` / `log-khoa.md` trong folder này, commit kèm sản
phẩm, không paste log vào chat. Review ghi vào cuối file log của người được review, dưới mục
`## Review — <người review> (<ngày>)`.

**Chi phí API:** dùng model tầng rẻ khi kiểm chức năng; **nêu rõ số lượt trước khi chạy** quá 10 lượt
hoặc dùng model tầng đắt (`CLAUDE.md` mục 2).

---

## 1. Đã chốt (Hùng chốt 14/10)

- **Thiết kế: Design Y** — mỗi proxy dùng cơ chế mạnh nhất mà bản OSS của nó cho phép.
  Chi tiết: `docs/experiment-design.md`.
- **Bộ đánh giá: 4 bộ, 0-shot** — MMLU, GSM8K, HumanEval (pass@1), IFEval. **10 item/bộ = 40 item
  → 360 lượt.** Bỏ MT-Bench (metric chuẩn của nó là GPT-4 làm trọng tài).
- **Luật quyết định: KHÔNG sửa**, giữ cả ngưỡng 80%. Chỉ số diễn giải chính: **chi phí/câu đạt** (ý Khoa).
- **Bỏ LiteLLM Auto Router** — lý do chính: cần ≥ v1.94 tức phải bỏ pin bảo mật `v1.83.14-stable`.
- **Không báo thầy đợt này**, cứ làm.

---

## 2. Bốn phase

### Phase 0 — 14/10 · Hùng · không tốn tiền ✅ xong

Viết `docs/experiment-design.md` + file này · ghi quyết định D2 sửa / D10 / D11 vào `roadmap.md`
mục 4 + `CLAUDE.md` mục 2 · sửa con số "30 prompt / 270 lượt" → "40 item / 360 lượt" · xoá file
chết · commit 2 lô dữ liệu smoke + issue draft · mở PR.

### Phase 1 — 15/10 · bộ đề + cấu hình 3 proxy · ~6 lượt, **có tầng đắt → báo trước**

**Hùng**

| # | Việc | Đạt khi |
|---|---|---|
| H1 | Tải 4 dataset **từ nguồn chính thức**; lấy **10 item/bộ**, **seed ghi lại**; sinh `prompts.json` (0-shot) | File hợp lệ, 40 item, id duy nhất |
| H2 | Sửa `experiments/prompts/validate_prompts.py` — đang cứng 12/6/12 | `python experiments/prompts/validate_prompts.py` pass |
| H3 | **Suy ngưỡng `prompt_len`** cho Portkey từ phân bố độ dài thật của 40 item; **khoá kèm lý do** | Ngưỡng + lý do ghi trong `docs/routing-policy.md`, **trước khi chạy** |
| H4 | `docs/benchmark-survey.md`: mỗi bộ — paper gốc, link dataset, **phiên bản/commit**, split, metric **trích từ paper**, protocol gốc, giấy phép | Mọi metric có citation; Khoa đã đọc |
| H5 | **Pin Bifrost** `maximhq/bifrost:latest` → `v2.1.1` (`docker-compose.yml:56`) | `docker inspect conduit-bifrost --format '{{.Config.Image}}'` = `maximhq/bifrost:v2.1.1` |
| H6 | Dọn container thử `litellm-autorouter-test` (port 4001) | `docker ps` không còn |

**Khoa**

| # | Việc | Đạt khi |
|---|---|---|
| K1 | **Bifrost:** bật analyzer + 3 CEL rule map tier → **model thật** (SIMPLE→`gpt-4o-mini`, MEDIUM→`claude-haiku`, COMPLEX→`claude-sonnet`) | Gửi 1 câu dễ + 1 câu khó → 2 model khác nhau |
| K2 | **Portkey:** config conditional theo `metadata.prompt_len` (`$lt`/`$gt`) | Prompt ngắn/dài ra model khác nhau |
| K3 | **Backend** (`HttpProxyChatClient.complete()`): thêm `metadata.prompt_len`; thêm `max_tokens: 512` (thực thi D7 — hiện **chưa gửi bao giờ**) | `e2e_workflow_test.sh` pass |
| K4 | ⚠️ **Sửa `resolveReturnedModel`** (`HttpProxyChatClient.java:151-157`) | `routing_decisions.selected_model` + `cost_upstream` **đúng** khi Portkey định tuyến động |

**Trạng thái Bifrost khi Khoa bắt đầu K1** (Hùng đã dọn 14/10): image pin `v2.1.1`, container đã
tạo lại, **0 routing rule**, analyzer **disabled**, provider openai/anthropic/gemini đều `active`
với `timeout=45s` + `max_retries=2` (D7). 3 rule `smoke-*` của đợt thử khả thi đã xoá — nếu không
xoá thì K1 sẽ đụng lỗi trùng `priority`.

**Lưu ý kỹ thuật cho K1** (đã gặp thật, tiết kiệm thời gian cho Khoa):
- `PUT /api/routing/complexity-analyzer-config` **thay toàn bộ config** → phải gửi lại **cả**
  `keywords` (150 câu mẫu) + `tier_boundaries`, không chỉ khối `semantic`. Thiếu `keywords` → lỗi 400
  *"keyword lists must be non-empty"*.
- Khối cần thêm: `semantic: {provider: openai, embedding_model: text-embedding-3-small, timeout:
  "1.5s", min_similarity: 0, message_history_count: 1}`. Key OpenAI có `models:["*"]` nên **không
  phải khai provider embedding riêng**.
- `POST /api/routing/rules`: ⚠️ `priority` phải **duy nhất trong mỗi scope** — 3 rule cùng
  `priority: 5` → **lỗi 500** *"routing rule with priority 5 already exists for scope 'global'"*.
  Dùng 5 / 6 / 7.
- Sau khi PUT, chờ `GET /api/routing/complexity-analyzer-status` báo `state: ready`, `loaded: 150`.

**Lưu ý kỹ thuật cho K4** — đây là chỗ dễ bỏ sót nhất: comment trong code ghi lý do *"Portkey's
conditional routing is a static 1:1 alias→target mapping — it never dynamically picks a different
model"*. Lý do đó **đúng với thiết kế cũ** và **sai ngay khi** Portkey định tuyến theo `prompt_len`.
Không sửa thì toàn bộ nhánh Portkey **ghi sai model và sai giá, sai trong im lặng**. Portkey trả
`model` là id có ngày (`gpt-4o-mini-2024-07-18`) → phải qua `properties.aliasOf()`, có thể cần thêm
ánh xạ cho dạng id đó.

**Đạt khi (cả hai):** gửi **cùng một prompt dài** qua 3 proxy → **3 model khác nhau**;
`e2e_workflow_test.sh` pass với cả `CHAT_ACTIVE_PROXY=portkey` và `=bifrost`.

### Phase 2 — 16/10 · bộ chấm + dry-run · 36 lượt, ~$0.05–0.15 → báo trước

**Hùng**

| # | Việc | Đạt khi |
|---|---|---|
| H7 | Bộ chấm 4 metric, **dùng harness chính thức, không tự viết lại**: MMLU (trích chữ cái), GSM8K (trích số cuối / `#### N`), **HumanEval pass@1 (sandbox chạy code, temperature 0)**, IFEval (verifier ràng buộc). Mở rộng `experiments/analysis/grading.py` (33 dòng, hiện chỉ exact/contains/regex) | Mỗi metric có test **≥2 ca đúng + 2 ca sai** |
| H8 | Sửa `experiments/scripts/run_experiment.py`: `load_prompts()` đọc 4 nhóm mới; **chuyển chấm sang offline** — runner chỉ thu output | Runner chạy 1 item không crash; chấm chạy riêng được |

> **Vì sao tách chấm ra offline:** đây là chỗ cứu tiến độ. Thu output và chấm điểm độc lập nhau, nên
> nếu sandbox pass@1 chưa xong kịp 16/10 thì ngày 17 vẫn chạy đủ 360 lượt, chấm 3 bộ còn lại,
> HumanEval bù sau — không phải hoãn Phase 3.

**Khoa**

| # | Việc | Đạt khi |
|---|---|---|
| K5 | **Dry-run 4 item (1/bộ) × 3 proxy × 3 lần = 36 lượt** trên thiết kế mới | 36 dòng `routing_decisions` |
| K6 | Kiểm `routing_decisions`: `selected_model` đúng, **tier suy được từ model**, `cost_upstream` khớp `model_pricing` | **Không lượt nào ghi sai model/giá** |
| K7 | Chạy `experiments/analysis/decision_rule.py` trên dữ liệu dry-run | Ra bảng, không lỗi |

**Tier không cần ghi cột riêng:** map tier → model là **1:1** nên tier **suy được từ
`selected_model`** — khỏi phải gọi `/api/logs` của Bifrost sau mỗi lượt.

### Phase 3 — 17/10 · chạy chính thức + chấm + kết luận · 360 lượt, ~$0.5–1.5 → báo trước

**Sáng — chạy 360 lượt**, chia đôi:
- **Hùng:** 20 item (MMLU + GSM8K) × 3 proxy × 3 lần = 180 lượt
- **Khoa:** 20 item (HumanEval + IFEval) × 3 proxy × 3 lần = 180 lượt

Mỗi người chạy phần mình qua **cả 3 proxy** (`CHAT_ACTIVE_PROXY` đổi theo đợt).

**Chiều — chấm + kết luận** → `docs/experiment-results.md`:
- Bảng số liệu 3 proxy: accuracy/pass@1, chi phí TB/lượt, **chi phí/câu đạt**, p95 latency, error_rate
- **Bảng tỷ lệ model mỗi proxy đã chọn** — bắt buộc, không có thì accuracy vô nghĩa
- Áp luật 4 bước, kết luận "proxy được chọn và vì sao" theo **đúng thứ tự** luật
- **Đối chiếu 3 giả thuyết** ở `experiment-design.md` mục 7 — khớp hay không khớp **đều phải nói**

**Đạt khi:** 360 dòng `routing_decisions`; lượt lỗi **liệt kê chứ không loại**; có proxy được chọn
kèm lý do; kết quả thô lưu bất biến trong `experiments/results/`.

### Phương án lùi — quyết trước, không quyết lúc đang cháy

| Trượt ở đâu | Làm gì |
|---|---|
| HumanEval pass@1 sandbox chưa xong 16/10 | **Vẫn chạy đủ 360 lượt** (thu output). Chấm 3 bộ kia; HumanEval ghi "đã thu, chưa chấm"; `decision_rule.py` chạy trên 3 bộ và **nói rõ**. **Không hoãn Phase 3** |
| Nhánh Portkey chưa chạy hết 15/10 | Chạy 2 proxy trước ngày 17, Portkey bù sau — **ghi rõ là thiếu 1 proxy** |
| Provider lỗi hàng loạt | Ghi `usage_logs.status=error`, **không chạy bù** (D7); `error_rate` báo riêng |
| Lượt chạy chạm `REQUEST_TIMEOUT` 45s | `max_tokens=512` giữ generation không chạy dài; nếu vẫn chạm, ghi vào giới hạn |

---

## 3. Hai việc đã xong — ĐỪNG LÀM LẠI

Dữ liệu thô: `experiments/results/bifrost-complexity-smoke-20261009/` và
`experiments/results/litellm-autorouter-smoke-20261014/`. Tổng **27 lượt API thật**, ~$0.038.
Phân tích đầy đủ: `docs/experiment-design.md` mục 8.

### 3.1. K3 cũ — Bifrost Complexity Router: **CHẠY ĐƯỢC**, nhưng phân loại lệch

Không bị gate Enterprise; v2.1.1; phân loại **tất định** (3/3 và 2/2); **đối chứng dương đạt** (câu
migrate live DB → COMPLEX cả 2 lần) nên cơ chế thật sự phân biệt được.

Nhưng: **trắc nghiệm tầm thường → COMPLEX** (đẩy sang model đắt nhất, tốn tiền không được gì);
**mọi prompt tiếng Việt → SIMPLE** (`mechanism=semantic` chứ không phải `skipped` → nó *có* phân
loại, chỉ luôn rơi đáy; **sai trong im lặng**); overhead **~257 ms/request**, tắt analyzer còn
**0.8–1.4 ms** → toàn bộ là lượt embedding.

→ Vì vụ tiếng Việt, **bộ đánh giá buộc phải là tiếng Anh**. Bộ 30 câu tiếng Việt đổi vai thành phép
thử riêng cho chỗ nhạy ngôn ngữ.

### 3.2. H3 cũ phần LiteLLM — Auto Router: **BỎ**

Cần ≥ v1.94 → phải bỏ pin `v1.83.14-stable` vốn pin vì **lý do bảo mật**. Nhân đó phát hiện lỗi
upstream: auto_router **bỏ qua giới hạn sinh token** ở cả 3 đường cấu hình, trên cả `v1.105.0` và
`v1.106.0-rc.1`, và báo `finish_reason=stop` nên **không phát hiện được**. Issue đã soạn ở
`docs/upstream-issues/litellm-autorouter-drops-max-tokens.md` (Hùng tự đăng).

→ **Không phải nâng LiteLLM, không phải dựng container riêng**, mất luôn rủi ro "nâng bản làm hỏng
cấu hình đang chạy" trong bản nháp.

---

## 4. Review chéo

| Sản phẩm | Viết | Phản biện | Phản biện làm gì |
|---|---|---|---|
| `benchmark-survey.md` + bộ chấm (H4, H7) | Hùng | Khoa | Đối chiếu metric với **paper gốc**; tải 1 bộ và chấm thử 2 ca |
| Bifrost tier→model (K1) | Khoa | Hùng | Chạy lại 2–3 câu trên máy mình, đối chiếu tier trong log Bifrost |
| Portkey `prompt_len` + `resolveReturnedModel` (K2, K4) | Khoa | Hùng | Gửi 1 prompt ngắn + 1 dài, kiểm **model ghi vào DB có đúng** không |
| Ngưỡng `prompt_len` (H3) | Hùng | Khoa | Kiểm ngưỡng có suy từ phân bố thật hay đặt theo cảm tính |
| `experiment-results.md` | Cả hai | — | Đọc chéo trước khi đưa vào báo cáo |

---

## 5. Bẫy môi trường mới gặp (bổ sung cho `CLAUDE.md`)

- **git-bash biến đổi đường dẫn Unix trong lệnh docker:** `-v .../x.yaml:/app/config.yaml` và
  `--config /app/config.yaml` bị đổi thành `C:/Program Files/Git/app/...` → container chết với
  *"Config file not found"*. Phải đặt `MSYS_NO_PATHCONV=1` trước `docker run`.
- `grep -P` không dùng được (lỗi locale) → dùng `sed -n 's/.../p'` để đọc biến từ `.env`.
- Python trong git-bash không hiểu đường dẫn `/tmp/...` → dùng đường dẫn Windows.
- **Script Python in tiếng Việt ra console bị `UnicodeEncodeError` (cp1252)** — không phải lỗi logic.
  Chạy `PYTHONIOENCODING=utf-8 python ...` (vd. `validate_prompts.py`).
- **GHCR *có* publish tag trần** cho LiteLLM bản mới (`v1.105.0`, `v1.104.3` tồn tại;
  `v1.105.0-stable` thì **không**). Ghi chú "GHCR không publish tag trần" trong `CLAUDE.md` chỉ đúng
  cho nhánh v1.83.x.

---

## 6. Checklist cuối tuần

- [x] Phase 0: `experiment-design.md`, task file, quyết định D2/D10/D11, xoá file chết, PR
- [x] H1–H4: bộ 40 item + validator + ngưỡng `prompt_len` + `benchmark-survey.md` — xong 14/10
- [x] H5, H6: pin Bifrost `v2.1.1`, dọn container thử — xong 14/10
- [x] H7, H8: 4 bộ chấm có test, runner đọc 4 nhóm + chấm offline — xong 14/10
- [x] K1–K4: Bifrost tier→model, Portkey `prompt_len`, backend metadata + `max_tokens`, **sửa `resolveReturnedModel`** — xong 15–16/10, xem `log-khoa.md`
- [x] K5–K7: dry-run 36 lượt, kiểm `routing_decisions`, chạy `decision_rule.py` — xong 16/10, 36/36 thành công, 0 dòng sai giá
- [ ] Phase 3: 360 lượt, chấm, `experiment-results.md` có kết luận + đối chiếu giả thuyết
- [ ] Review chéo xong, cả hai đã viết `log-*.md`
- [ ] `roadmap.md` mục 5 cập nhật: Phase B/C → 🟨, Phase E ghi mốc 17/10

## 7. Nhật ký cuối tuần (điền Chủ nhật 18/10)

| Việc | Trạng thái (✅/🟨/⛔) | Ghi chú |
|---|---|---|
| Phase 0 | ✅ | 14/10, Hùng |
| H1–H6 (Phase 1) | ✅ | 14/10, làm sớm 1 ngày. Xem `log-hung.md` |
| K1–K4 (Phase 1) | ✅ | 15–16/10, Khoa. e2e 43/43 cả 3 proxy. Portkey so `prompt_len` theo số (đã thử 93/300/1102). Xem `log-khoa.md` |
| H7–H8 (Phase 2) | ✅ | 14/10, làm sớm 2 ngày. Xem `log-hung.md` |
| K5–K7 (Phase 2) | ✅ | 16/10, Khoa. 36/36, $0.0505. Sửa bộ chấm HumanEval (thiếu import của đề). ⛔ Trước Phase 3 phải chốt `max_tokens` vì Sonnet dùng hết 512 token để suy nghĩ → trả lời rỗng |
| Phase 3 | 🟨 | Khoa xong phần HumanEval + IFEval 19/10: 180/180, 0 lỗi, $0.1187, dữ liệu sạch (`verify_results.py`). Chờ phần MMLU + GSM8K của Hùng rồi gộp 360 lượt |
