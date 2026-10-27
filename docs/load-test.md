# Load test (TASK-56)

Công cụ: `grafana/k6` chạy bằng Docker (máy không cài k6). **Không gọi LLM có phí.**
Máy đo: laptop Windows của Khoa; backend chạy `./mvnw spring-boot:run`, proxy + Postgres + Redis
trong Docker Desktop; k6 chạy trong container, gọi backend qua `host.docker.internal:8081`.

- **Phần chat:** Khoa, mục 1.
- **Phần đăng nhập, danh sách agent, ví:** Hùng, mục 2.

---

## 1. Phần chat (Khoa, 27/10)

### Cách giữ chi phí bằng 0

Alias giả **`conduit-mock`** trong `proxy-configs/litellm/config.yaml` dùng `mock_response`: LiteLLM
trả một câu cố định ngay lập tức, **không gọi nhà cung cấp nào**. Mọi bước còn lại đi đúng đường thật:

```
JWT → tạo hội thoại → POST tin nhắn (SSE) → backend gọi LiteLLM → trừ credit
    → ghi messages / usage_logs / routing_decisions
```

Kiểm bằng 1 request trước khi chạy tải:
- gọi thẳng LiteLLM: trả lời sau 10 ms, header `x-litellm-model-id: conduit-mock`;
- qua app: `selected_model = conduit-mock`, `cost_upstream = 0`, trừ 45 credit.

Cần 2 dòng `model_pricing` giá 0 cho alias này ở **DB local**, nếu không ChatService không tra được
giá: `loadtest/mock-pricing.sql`. Không đưa vào migration, vì production không có alias này.

### Cách chạy

```bash
docker exec -i conduit-postgres psql -U conduit -d conduit < loadtest/mock-pricing.sql

# Backend trỏ vào alias giả
CHAT_ACTIVE_PROXY=litellm CHAT_DEFAULT_MODEL=conduit-mock ./mvnw spring-boot:run   # + biến DB như thường

# AGENT_ID: agent miễn phí đã duyệt, default_credit_granted lớn
# (dùng agent của experiments/scripts/.experiment_identity.json)
MSYS_NO_PATHCONV=1 docker run --rm -i -e BASE_URL=http://host.docker.internal:8081/api \
  -e AGENT_ID=<agent_id> -e SCENARIO=many_users \
  -v "<repo>/loadtest:/scripts" grafana/k6 run /scripts/chat.js
```

`setup()` của script tự đăng ký tài khoản và mua agent miễn phí, nên mỗi tài khoản có ví riêng.
`MSYS_NO_PATHCONV=1` là bắt buộc trong git-bash (xem `docs/tasks/2026-10-12/tasks.md` mục 5).

Tải: tăng dần lên `MAX_VUS/2` trong 30 s → giữ 1 phút → tăng lên `MAX_VUS` (25) trong 30 s → giữ
1 phút → giảm về 0. Tổng 3 phút 20 giây. Mỗi vòng lặp là một lượt chat trọn vẹn (tạo hội thoại +
gửi tin nhắn), **không có thời gian nghỉ** giữa các vòng.

### Kết quả

| Kịch bản | Người dùng ảo | Lượt chat thành công | Lượt lỗi | Thông lượng | p50 | p95 | Tối đa |
|---|---|---|---|---|---|---|---|
| **Nhiều người dùng** (mỗi người dùng ảo một tài khoản, ví riêng) | 25 | **23.640** | **0** | 117 lượt/s | 107 ms | **211 ms** | 718 ms |
| Một người dùng gửi song song, **sau khi sửa** | 25 | 11.245 | 1.389 (11%) — đều là xung đột ví | 56 lượt/s | 66 ms | 1.090 ms | 1.640 ms |
| Một người dùng gửi song song, **trước khi sửa** | 25 | 10.853 | 10.897 (50%) | 54 lượt/s | 104 ms | 219 ms | 327 ms |

"Thời gian một lượt chat" = thời gian request `POST /conversations/{id}/messages`, từ lúc gửi tới
khi nhận `event:done`, **không gồm thời gian sinh câu trả lời của LLM** (alias giả trả lời ngay). Đây
là chi phí của backend + proxy + DB, không phải độ trễ người dùng thấy khi chat thật.

Lỗi HTTP: 7/47.337 request ở kịch bản nhiều người dùng là `dial: i/o timeout` khi k6 mở kết nối qua
mạng của Docker Desktop. Backend không ghi nhận lỗi nào cho các request này. Đây là nhiễu môi trường
đo, không phải lỗi ứng dụng.

Dữ liệu thô: `loadtest/results/2026-10-27-*.txt` (bản in đầy đủ của k6).

### Lỗi tìm ra nhờ load test — đã sửa

**Cùng một người dùng chat song song → khoảng 50% lượt lỗi, và lượt LLM đã gọi bị mất dấu.**

- Thông điệp: `Unexpected error: Row was updated or deleted by another transaction … CreditWallet`.
- **Nguyên nhân:** retry khi xung đột khóa nằm trong `CreditService`. Nhưng khi chat, việc trừ credit
  chạy **bên trong** transaction của `ChatService.recordSuccessfulTurn`, nên cả 3 lần thử đều nằm trong
  **cùng một transaction** đã bị đánh dấu rollback và vẫn đọc số dư cũ → chắc chắn thua lại.
- **Hậu quả trong chạy thật:** lượt LLM **đã được gọi** (đã tốn tiền nhà cung cấp) nhưng không ghi
  `usage_logs`/`routing_decisions` và không trừ credit — rò rỉ chi phí không để lại dấu vết.
- Test TASK-54 không bắt được vì nó gọi thẳng `CreditService`, không đi qua `ChatService`.
- **Sửa:** `ChatService.recordSuccessfulTurnWithRetry` thử lại **cả** `recordSuccessfulTurn` trong một
  transaction **mới** (qua proxy `self`), tối đa 8 lần, có chờ ngẫu nhiên tăng dần (10 → 400 ms).
  Trừ credit, ghi tin nhắn và ghi log vẫn nguyên tử.
- Không có chờ giữa các lần thử thì vẫn thua: 20 luồng song song → 11/20 thua cả 5 lần. Có chờ:
  20/20 và 40/40 thành công.

### Giới hạn còn lại

1. **Một tài khoản gửi 25 luồng liên tục vẫn còn 11% lượt thua xung đột ví.** Đây là tình huống cực
   đoan: khoảng 60 tin nhắn/giây từ một người dùng. Người dùng thật không gửi được như vậy. Nếu cần
   chắc chắn hơn: khóa bi quan khi trừ credit (`SELECT … FOR UPDATE`), hoặc đưa lượt thua vào hàng
   đợi. Lượt thua vẫn **mất dấu chi phí LLM** như trên — chỉ được ghi log `WARN "Billing gave up"`.
2. Đo trên một laptop, k6 và backend dùng chung CPU. Số tuyệt đối không đại diện cho máy chủ thật;
   dùng để so sánh trước/sau và tìm lỗi khi tải đồng thời.
3. Không đo độ trễ sinh câu trả lời của LLM thật (cố ý, để không tốn phí).

---

## 2. Phần đăng nhập, danh sách agent, ví (Hùng)

_(Hùng điền.)_
