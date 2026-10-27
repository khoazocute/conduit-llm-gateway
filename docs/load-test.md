# Load test (TASK-56)

Hai phần: **(A) các endpoint không gọi LLM** (Hùng, xong 27/10) và **(B) chat qua proxy** (Khoa,
dùng alias giả trong LiteLLM để không tốn phí). Mục tiêu: biết hệ thống chịu được tới đâu trước khi
deploy, và kiểm các ràng buộc bảo mật vẫn đúng khi có tải.

## A. Đăng nhập, xem chợ agent, xem chi tiết agent, xem ví

**Kịch bản** (`scripts/load-test/browse.js`): mỗi người dùng ảo có **tài khoản riêng** (tạo trong
`setup`), đăng nhập, rồi duyệt 5 lượt (danh sách agent → chi tiết một agent ngẫu nhiên → ví), nghỉ
1 giây giữa các lượt. Tải tăng dần 30 giây, giữ 1 phút, giảm 15 giây. **Không gọi LLM, không tốn phí.**

**Ngưỡng đạt (đặt trước khi chạy, trong `options.thresholds`):** tỷ lệ request lỗi < 1%; p95 < 500 ms
cho danh sách agent, chi tiết agent và ví; p95 < 1.500 ms cho đăng nhập (băm BCrypt nên chậm hơn có
chủ đích); > 99% check đạt. Một check riêng xác nhận **trang chi tiết agent không bao giờ trả
`instructions`** cho người không phải chủ agent (D8), kể cả khi có tải.

| | 20 người dùng ảo | 100 người dùng ảo |
|---|---|---|
| Tổng request | 5.157 | 20.053 |
| Thông lượng | 46,5 request/giây | 167,6 request/giây |
| Request lỗi | **0%** | **0%** |
| Check đạt (gồm "không lộ `instructions`") | 100% (6.741) | 100% (26.187) |
| p95 danh sách agent | 23 ms | **438 ms** (ngưỡng 500) |
| p95 chi tiết agent | 25 ms | 364 ms |
| p95 ví | 20 ms | 303 ms |
| p95 đăng nhập | 151 ms | 723 ms |
| Ngưỡng | **Đạt hết** | **Đạt hết**, danh sách agent sát ngưỡng |

**Đọc kết quả:**
- Không có request lỗi nào ở cả hai mức, và D8 vẫn đúng dưới tải.
- Từ 20 lên 100 người dùng, thông lượng tăng 3,6 lần nhưng p95 của ba endpoint đọc tăng **15–19
  lần** (đăng nhập tăng khoảng 5 lần, vì vốn đã chậm do BCrypt). Hệ thống bắt đầu
  chậm rõ ở khoảng 100 người dùng đồng thời **trên máy này**; danh sách agent là chỗ sát ngưỡng nhất.
- Đăng nhập chậm nhất vì BCrypt, đúng thiết kế. Người dùng thật không đăng nhập liên tục như kịch bản
  (mỗi lượt lặp đăng nhập lại 1 lần), nên con số này là mức bất lợi.

**Giới hạn của phép đo, nói rõ:**
- Chạy trên **laptop**, backend + Postgres + Redis + k6 cùng một máy, nên tranh tài nguyên với nhau.
  Không đại diện cho môi trường deploy; chỉ dùng để so sánh tương đối giữa các mức tải.
- Chỉ đo endpoint đọc và đăng nhập. Luồng ghi (mua agent, trừ credit) và chat thuộc phần B.
- `setup` tạo 120 tài khoản `load.*@conduit.dev` trong DB local mỗi lần chạy đủ hai mức. Không ảnh
  hưởng dữ liệu thí nghiệm (bảng `routing_decisions` không bị đụng tới).

**Chạy lại** (cần Docker và backend ở `localhost:8081`; nên chạy `e2e_test.sh` trước để có agent
published):

```bash
MSYS_NO_PATHCONV=1 docker run --rm -v "$PWD/scripts/load-test:/scripts" grafana/k6:0.54.0 run \
  -e BASE=http://host.docker.internal:8081/api -e VUS=20 \
  --summary-export=/scripts/results/browse-summary.json /scripts/browse.js
```

`MSYS_NO_PATHCONV=1` chỉ cần trên git-bash Windows. Số liệu thô: `scripts/load-test/results/`.

## B. Chat qua proxy (Khoa)

_(Khoa điền sau TASK-51.)_ Phải dùng alias giả trong LiteLLM (`mock_response`), kiểm bằng 1 request
trước, và thêm dòng `model_pricing` giá 0 cho alias đó ở môi trường local.
