# KHÔNG phải dữ liệu thí nghiệm — đừng dùng để phân tích

## `run_litellm_20261016T163635Z.json`

Đợt chạy **dở dang do Hùng/Claude dừng giữa chừng** ngày 2026-10-16, không phải một đợt
thí nghiệm có chủ đích.

**Nguyên nhân:** `--limit 0` vừa được đổi nghĩa từ *"không chạy lượt nào"* sang *"lấy hết
item"*, nhưng header `dry_run.sh` vẫn ghi `PROMPT_LIMIT=0` là cách test không tốn tiền.
Bản vá thêm cơ chế chặn bị lỗi cú pháp nên **chưa được áp dụng**, mà lệnh test lại chạy
ngay sau đó trong cùng một lượt gọi → script chạy thật. Phát hiện và dừng sau 79 bản ghi.

**Vì sao không dùng được:** 28/79 bản ghi có `status=error` là **do bị kill**, không phải
lỗi nhà cung cấp — dùng nó sẽ làm `error_rate` sai hoàn toàn.

**Chi phí thực:** $0.00325 (51 lượt thành công, toàn `gpt-4o-mini`).

**Nhưng nó có ích, và đã dùng để kiểm 3 thứ (miễn phí):**
1. `temperature: 0` **có hiệu lực thật** — 17/17 item chạy đủ 3 lần đều cho **cùng kết quả**,
   0 lượt dao động. Trước khi có nó, dry-run 16/10 của Khoa có `ifeval_01` đạt/trượt/đạt.
2. `max_tokens: 1024` đi qua app bình thường.
3. Chuỗi `run_experiment.py` → `grade_results.py` → `verify_results.py` chạy end-to-end
   trên dữ liệu thật; `verify_results.py` báo sạch (model đều có trong `model_pricing`,
   mọi lượt thành công đều có chi phí > 0).

**Cơ chế chặn đã thêm sau sự cố:** `PROMPT_LIMIT=0` giờ bị từ chối kèm thông báo; muốn
test không tốn tiền thì dùng `NO_CALLS=1`.
