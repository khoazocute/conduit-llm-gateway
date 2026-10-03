#!/bin/bash
# Tự động chạy dry-run/thực nghiệm qua cả 3 proxy: với mỗi proxy, restart backend
# trỏ đúng CHAT_ACTIVE_PROXY, chờ sẵn sàng, rồi gọi run_experiment.py (D3 - qua app
# thật, không gọi thẳng proxy). Gộp lại quy trình vốn phải làm tay 3 lần (Phase D,
# docs/roadmap.md).
#
# CHỈ chạy khi đã xin xác nhận số lượt/model với Hùng (CLAUDE.md mục 2) - script này
# TỰ NÓ không hỏi lại, kiểm tra kỹ PROMPT_LIMIT/RUNS/PROXIES trước khi Enter.
# Test cơ chế an toàn (không tốn tiền): PROMPT_LIMIT=0 (bootstrap chạy nhưng
# không lượt chat thật nào).
#
# Cách dùng:
#   PROMPT_LIMIT=3 RUNS=3 PROXIES="litellm bifrost portkey" bash experiments/scripts/dry_run.sh
# Mặc định: PROMPT_LIMIT=3 RUNS=3 PROXIES="litellm bifrost portkey" (= 27 lượt nếu cả 3 proxy chạy được)
#
# Yêu cầu: docker compose up -d postgres redis litellm bifrost portkey (đúng những
# proxy có trong $PROXIES); .env có đủ key thật; chạy từ thư mục gốc repo hoặc bất kỳ
# đâu (tự dò đường dẫn). Windows: dùng taskkill dừng tiến trình giữ cổng 8081 giữa các proxy.
# Máy remap port (docker-compose.override.yml) thì export trước khi chạy, VD máy Khoa:
#   SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5433/conduit BIFROST_BASE_URL=http://localhost:18080/v1

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend-gateway"
LOG_DIR="$ROOT_DIR/experiments/results/dry-run-logs"
mkdir -p "$LOG_DIR"

PROMPT_LIMIT="${PROMPT_LIMIT:-3}"
RUNS="${RUNS:-3}"
PROXIES="${PROXIES:-litellm bifrost portkey}"

echo "=== Dry-run: PROMPT_LIMIT=$PROMPT_LIMIT RUNS=$RUNS PROXIES=\"$PROXIES\" ==="
echo "Tổng lượt gọi thật dự kiến (nếu cả $(echo $PROXIES | wc -w) proxy chạy được): $((PROMPT_LIMIT * RUNS * $(echo $PROXIES | wc -w)))"

set -a
# .env soạn trên Windows có CRLF - không bỏ \r thì mọi giá trị dính \r ở cuối
# (LITELLM_MASTER_KEY sai → LiteLLM trả 401).
# shellcheck disable=SC1090
source <(tr -d '\r' < "$ROOT_DIR/.env")
set +a

wait_backend_ready() {
  for _ in $(seq 1 30); do
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/api/agents 2>/dev/null || echo "")
    if [ "$code" = "200" ]; then return 0; fi
    sleep 3
  done
  return 1
}

# Chỉ dừng tiến trình đang giữ cổng 8081 (backend), không đụng java.exe khác
# (VD language server Java của VS Code).
stop_backend() {
  local pid
  pid=$(netstat -ano | grep ':8081 ' | grep LISTENING | awk '{print $5}' | head -1 || true)
  if [ -n "$pid" ]; then
    taskkill //F //PID "$pid" //T >/dev/null 2>&1 || true
    sleep 2
  fi
}

FAILED_PROXIES=()
RESULT_FILES=()

for proxy in $PROXIES; do
  echo ""
  echo "=== Proxy: $proxy ==="
  stop_backend

  export CHAT_ACTIVE_PROXY="$proxy"
  # D2: LiteLLM tự chọn model rẻ nhất trong alias conduit-pool (cost-based-routing,
  # H1). Gọi thẳng gpt-4o-mini thì LiteLLM chỉ chuyển tiếp, không định tuyến gì.
  # Bifrost/Portkey không có alias này - dùng mặc định gpt-4o-mini (+ fallbacks).
  if [ "$proxy" = "litellm" ]; then
    export CHAT_DEFAULT_MODEL=conduit-pool
  else
    unset CHAT_DEFAULT_MODEL
  fi
  (
    cd "$BACKEND_DIR"
    nohup ./mvnw spring-boot:run >"$LOG_DIR/backend_${proxy}.log" 2>&1 &
  )

  if ! wait_backend_ready; then
    echo "  Bỏ qua $proxy — backend không lên được sau 90s. Xem $LOG_DIR/backend_${proxy}.log" >&2
    FAILED_PROXIES+=("$proxy")
    continue
  fi
  echo "  Backend sẵn sàng (active-proxy=$proxy). Chạy runner..."

  # PYTHONIOENCODING: console Windows mac dinh cp1252, khong in duoc tieng Viet co dau.
  if ! PYTHONIOENCODING=utf-8 python "$ROOT_DIR/experiments/scripts/run_experiment.py" \
      --proxy-name "$proxy" --limit "$PROMPT_LIMIT" --runs "$RUNS"; then
    echo "  Runner báo lỗi cho $proxy — xem log ở trên, kết quả đã chạy được vẫn giữ nguyên (ghi ngay từng lượt)." >&2
    FAILED_PROXIES+=("$proxy")
  fi
  # File runner vừa ghi (tên có timestamp lúc chạy, không đoán trước được) - lấy file
  # run_<proxy>_*.json mới nhất để gộp, kể cả khi runner báo lỗi giữa chừng (vẫn có
  # record đã ghi được, roadmap.md mục 7: không vứt dữ liệu thô).
  latest=$(ls -t "$ROOT_DIR/experiments/results/run_${proxy}_"*.json 2>/dev/null | head -1 || true)
  [ -n "$latest" ] && RESULT_FILES+=("$latest")
done

stop_backend

echo ""
echo "=== Xong ==="
echo "Kết quả thô: $ROOT_DIR/experiments/results/run_*.json"

# Gộp kết quả + áp decision_rule.py ngay (roadmap.md Phase D: "một lệnh chạy hết
# dry-run và cho ra file kết quả thô + bảng tổng hợp" - trước đây phải gộp tay).
if [ ${#RESULT_FILES[@]} -gt 0 ]; then
  MERGE_DIR="$ROOT_DIR/experiments/results/dry-run-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$MERGE_DIR"
  PYTHONIOENCODING=utf-8 python - "${RESULT_FILES[@]}" <<'PYEOF' > "$MERGE_DIR/merged.json"
import json, sys
records = []
for p in sys.argv[1:]:
    records.extend(json.load(open(p, encoding="utf-8")))
print(json.dumps(records, indent=2, ensure_ascii=False))
PYEOF
  echo "Gộp ${#RESULT_FILES[@]} file -> $MERGE_DIR/merged.json"
  if PYTHONIOENCODING=utf-8 python "$ROOT_DIR/experiments/analysis/decision_rule.py" "$MERGE_DIR/merged.json" \
      | tee "$MERGE_DIR/decision_rule_output.json"; then
    echo "Bảng quyết định: $MERGE_DIR/decision_rule_output.json"
  else
    echo "decision_rule.py báo lỗi (có thể do chưa đủ proxy đạt ngưỡng closed-QA) — xem ở trên." >&2
  fi
fi

if [ ${#FAILED_PROXIES[@]} -gt 0 ]; then
  echo "Proxy có vấn đề (xem log riêng): ${FAILED_PROXIES[*]}"
  exit 1
fi
