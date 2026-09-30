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
# đâu (tự dò đường dẫn). Windows: dùng taskkill để dừng backend giữa các proxy - nếu
# có tiến trình java.exe khác (không phải backend) đang chạy, nó cũng bị dừng theo.

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
# shellcheck disable=SC1091
source "$ROOT_DIR/.env"
set +a

wait_backend_ready() {
  for _ in $(seq 1 30); do
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/api/agents 2>/dev/null || echo "")
    if [ "$code" = "200" ]; then return 0; fi
    sleep 3
  done
  return 1
}

stop_backend() {
  taskkill //F //IM java.exe //T >/dev/null 2>&1 || true
  sleep 1
}

FAILED_PROXIES=()

for proxy in $PROXIES; do
  echo ""
  echo "=== Proxy: $proxy ==="
  stop_backend

  export CHAT_ACTIVE_PROXY="$proxy"
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
done

stop_backend

echo ""
echo "=== Xong ==="
echo "Kết quả thô: $ROOT_DIR/experiments/results/run_*.json"
if [ ${#FAILED_PROXIES[@]} -gt 0 ]; then
  echo "Proxy có vấn đề (xem log riêng): ${FAILED_PROXIES[*]}"
  exit 1
fi
