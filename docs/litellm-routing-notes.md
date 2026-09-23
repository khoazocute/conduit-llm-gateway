# LiteLLM routing — làm được / không làm được (nháp H4, cần Khoa phản biện)

Nguồn: https://docs.litellm.ai/docs/routing (đọc 2026-09-22). Chưa chạy thử — mục "VERIFY" cần kiểm ở H3.
Config nháp: `proxy-configs/litellm/config.routing-draft.yaml`.

## 1. Gom 5 model thành 1 alias
Nhiều `model_list` entry cùng `model_name` = 1 "model group"; Router chọn 1 deployment trong nhóm theo
`router_settings.routing_strategy`. Runner chỉ cần gọi `model="conduit-pool"` và đọc model thực sự được chọn từ
response (`model` / header) để ghi `routing_decisions.selected_model`.

## 2. Các strategy

| Strategy | Chọn theo | Ghi chú cho thí nghiệm |
|---|---|---|
| `simple-shuffle` (mặc định) | ngẫu nhiên, có thể có `weight`/`rpm`/`tpm` | Là load balancing, không phải "routing thông minh". Dùng làm baseline. |
| `cost-based-routing` | deployment có giá **thấp nhất** (giá từ cost map, có thể ghi đè `input_cost_per_token`/`output_cost_per_token`; model không có trong map bị coi $1) | Tất yếu chọn 2 model tầng rẻ mọi lúc → **tầng trung/đắt gần như không bao giờ được dùng** |
| `latency-based-routing` | deployment có latency trung bình thấp nhất (`ttl`, `lowest_latency_buffer`) | Kết quả phụ thuộc mạng/tải lúc chạy → consistency thấp hơn |
| `usage-based-routing-v2` | TPM đang dùng thấp nhất; cần Redis + `tpm`/`rpm` | Là cân tải, không liên quan chi phí/chất lượng; tốn Redis |
| `least-busy` | ít request đang chạy nhất | Với runner chạy tuần tự thì gần như ngẫu nhiên |

## 3. Độ bền (đặt giống nhau giữa 3 proxy)
`num_retries`, `retry_after`, `timeout`, `allowed_fails` + `cooldown_time` (cooldown deployment lỗi),
`order` (ưu tiên deployment), fallbacks cross-model. Cú pháp `fallbacks` trong docs không nhất quán → VERIFY.
Hiện config chưa có fallback (log: `Available Model Group Fallbacks=None`).

## 4. LiteLLM KHÔNG làm được (quan trọng cho kết luận)
- **Không chọn model theo độ khó/loại prompt.** Cost-based chỉ nhìn giá; không có bộ phân loại chất lượng.
  ("Auto Router" bản BETA có tồn tại nhưng docs không mô tả rõ — chưa đánh giá, nằm ngoài thiết kế thí nghiệm.)
  → Muốn "prompt dễ → model rẻ, prompt khó → model đắt" phải viết ngoài proxy: thuộc phạm vi V2 đã bỏ, không làm.
- Quyết định routing không tự trả về đầy đủ lý do; phải suy ra từ response.

## 5. Hệ quả cho thiết kế thí nghiệm (đề xuất, cần chốt với Khoa)
1. Với `cost-based` thuần, độ chính xác closed-QA ≈ độ chính xác của GPT-4o-mini/Gemini Flash → dễ qua ngưỡng 80% nhưng
   thí nghiệm không thấy đánh đổi cost–quality thật. Nên ghi rõ đây là đặc tính của strategy, không phải lỗi proxy.
2. So sánh công bằng: mỗi proxy chọn 1 strategy "gần nghĩa" nhất (cost/latency) và **cùng** retry/timeout/fallback.
3. Consistency rate (quy tắc 4) chỉ có ý nghĩa với strategy có tính ngẫu nhiên/động (latency, shuffle, usage);
   cost-based cho kết quả gần như hằng → tie-break đó sẽ không phân biệt được.
4. Cần biết Bifrost/Portkey cũng gom nhóm được kiểu này không (H5 cho Portkey; Bifrost chưa có việc) trước khi chốt
   "strategy tương đương".

## Câu hỏi mở
- Chạy `cost-based` hay `latency-based` làm strategy chính cho LiteLLM? (đề xuất: chạy cả hai, mỗi cái 1 dòng kết quả)
- Có bật fallback không? (chỉ khi cả 3 proxy cấu hình được failover tương đương)
