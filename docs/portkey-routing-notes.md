# Portkey AI Gateway routing — làm được / không làm được (nháp H5-style, chưa chạy thử)

Nguồn: https://portkey.ai/docs/product/ai-gateway/conditional-routing — đọc 2026-09-23.
Chưa chạy thử — VERIFY khi cấu hình thật. Cấu hình hiện tại (`proxy-configs/portkey/config.json`) đang
`strategy.mode: "single"` — tức **chưa bật routing thật**, chỉ trỏ 1 target cố định.

## 1. Cấu trúc config — khác hẳn LiteLLM/Bifrost
Không có "model pool" theo model_name như LiteLLM, cũng không phải weighted-provider như Bifrost. Portkey
dùng 1 object `config` gồm `strategy` (cách chọn) + `targets` (danh sách đích, mỗi đích = 1 provider/model):
```json
{
  "strategy": { "mode": "conditional", "conditions": [...], "default": "target_name" },
  "targets": [
    { "name": "target_name", "provider": "@provider-key", "override_params": { "model": "gpt-4o" } }
  ]
}
```
`strategy.mode` có ít nhất 3 giá trị: `single` (1 target cố định — đang dùng), `fallback` (thử lần lượt),
`loadbalance` (chia theo trọng số), và `conditional` (chọn theo điều kiện — mục này tài liệu mô tả kỹ nhất).

## 2. Conditional routing — đúng nghĩa "rule-based" mà CLAUDE.md mô tả
Điều kiện dùng cú pháp kiểu MongoDB query, so khớp trên:
- `metadata.<key>` — key-value tùy ý gửi kèm request (Conduit có thể gắn vd. `metadata.prompt_type=code`).
- `params.<key>` — tham số request LLM (model, temperature...).
- `url.pathname` — đường dẫn request.

Toán tử so sánh: `$eq/$ne/$in/$nin/$regex/$gt/$gte/$lt/$lte`; toán tử logic `$and/$or` (lồng được).
```json
{ "query": { "metadata.user_plan": { "$eq": "paid" } }, "then": "target_name" }
```
Giới hạn: chỉ kiểu dữ liệu nguyên thủy (string/number/boolean), key tối đa 2 đoạn (`metadata.key`, không
lồng sâu hơn `metadata.a.b`); thiếu key → điều kiện coi là `false` (không báo lỗi).

## 3. Portkey KHÔNG làm được
- **Không có cost-based hay latency-based routing tự động.** Tài liệu nói rõ: mọi quyết định dựa trên rule
  người tự khai báo (`conditions`) — không tự đo giá/độ trễ rồi chọn như LiteLLM `cost-based-routing`.
- `targets` không mô tả weight trong conditional mode (chọn theo điều kiện khớp là quyết định, không có
  xác suất) — weight chỉ có ý nghĩa ở `loadbalance` mode (chưa đọc chi tiết trang đó, cần đọc thêm nếu dùng).
- Không chọn theo độ khó/loại nội dung prompt tự động — phải tự gắn `metadata` (vd. đánh dấu prompt nào là
  "code"/"open_ended" từ phía runner) rồi viết rule khớp theo đó. Tức **routing "thông minh" ở Portkey thực
  chất là rule tĩnh do người viết**, không phải proxy tự quyết định.

## 4. Cách dùng
Cấu hình tạo trên UI Portkey → có Config ID → gắn vào request qua tham số `config` (docs không nêu rõ chi
tiết header `x-portkey-config` trong trang này — cần đọc thêm trang API reference nếu dùng header thay vì
Config ID, VERIFY trước khi cấu hình thật).

## 5. Hệ quả cho thiết kế thí nghiệm (đề xuất, cần Khoa phản biện)
1. Vì Portkey không có cost/latency tự động, cấu hình công bằng nhất so với LiteLLM `cost-based-routing` là
   viết **rule tĩnh mô phỏng cost-based**: vd. `conditions` khớp theo `metadata.prompt_group` (closed_qa/
   code/open_ended) → route tới model rẻ theo mặc định, `default` trỏ model rẻ nhất — tương tự cách con
   người sẽ tự làm nếu không có auto-routing.
2. Vì rule là tĩnh (không ngẫu nhiên, không phụ thuộc tải mạng), **consistency rate của Portkey cũng sẽ cao
   như Bifrost** — cùng lưu ý diễn giải như ghi ở `bifrost-routing-notes.md` mục 5.2.
3. Runner cần gửi kèm `metadata` mô tả loại prompt (vd. `prompt_group`) để rule có cái để khớp — ảnh hưởng
   thiết kế runner (H3/việc viết `run_experiment.py`), không chỉ là việc cấu hình proxy.

## Câu hỏi mở
- Rule conditional nên khớp theo cái gì: loại prompt (closed_qa/code/open_ended, do runner tự gắn metadata),
  hay theo độ dài prompt (đo được từ `params`, không cần metadata) để giống "quyết định dựa trên đặc điểm
  request" hơn là cấu hình cứng theo tay?
- Cần đọc thêm trang `loadbalance` mode và cú pháp header `x-portkey-config` trước khi build config thật.
