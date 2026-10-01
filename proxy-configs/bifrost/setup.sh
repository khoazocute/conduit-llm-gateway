#!/usr/bin/env bash
# Dựng cấu hình Bifrost cho thí nghiệm (K1, D2/D7). Bifrost lưu cấu hình trong SQLite của volume
# bifrost/data, không đọc file config.json lúc khởi động, nên máy nào mới dựng cũng phải chạy script
# này 1 lần (chạy lại nhiều lần vẫn an toàn — không tạo trùng).
#
#   BIFROST_URL=http://localhost:18080 bash proxy-configs/bifrost/setup.sh   # máy Khoa (remap port)
#   bash proxy-configs/bifrost/setup.sh                                      # mặc định :8080
#
# Chuỗi fallback (rẻ → đắt) KHÔNG nằm ở đây: Bifrost nhận "fallbacks" theo từng request, nên backend
# tự gửi kèm — xem app.chat.proxy-fallback-chains trong backend-gateway/src/main/resources/application.yml.
set -euo pipefail

BIFROST_URL="${BIFROST_URL:-http://localhost:8080}"
TIMEOUT_SECONDS=45   # D7
MAX_RETRIES=2        # D7

api() { curl -sS -H "Content-Type: application/json" "$@"; }

if ! api "$BIFROST_URL/api/providers" >/dev/null; then
  echo "Không gọi được $BIFROST_URL — Bifrost đã chạy chưa? (docker compose up -d bifrost)" >&2
  exit 1
fi

# OpenAI/Anthropic: Bifrost tự tạo provider + key từ OPENAI_API_KEY/ANTHROPIC_API_KEY trong .env.
# Gemini thì không, phải khai báo tay.
if ! api "$BIFROST_URL/api/providers" | grep -q '"name":"gemini"'; then
  api -X POST "$BIFROST_URL/api/providers" -d '{"provider":"gemini"}' >/dev/null
  echo "+ tạo provider gemini"
fi
if ! api "$BIFROST_URL/api/keys" | grep -q '"name":"gemini-key-1"'; then
  # models phải là ["*"]; [] nghĩa là không cho model nào ("no keys found").
  api -X POST "$BIFROST_URL/api/providers/gemini/keys" \
    -d '{"name":"gemini-key-1","value":"env.GEMINI_API_KEY","models":["*"],"weight":1.0}' >/dev/null
  echo "+ thêm key gemini-key-1 (tham chiếu env.GEMINI_API_KEY)"
fi

for provider in openai anthropic gemini; do
  if ! api "$BIFROST_URL/api/providers" | grep -q "\"name\":\"$provider\""; then
    echo "! thiếu provider $provider — kiểm tra key tương ứng trong .env rồi tạo lại container bifrost" >&2
    exit 1
  fi
  api -X PUT "$BIFROST_URL/api/providers/$provider" -d "{
    \"network_config\": {
      \"default_request_timeout_in_seconds\": $TIMEOUT_SECONDS,
      \"max_retries\": $MAX_RETRIES,
      \"retry_backoff_initial\": 500,
      \"retry_backoff_max\": 5000
    },
    \"concurrency_and_buffer_size\": {\"concurrency\": 1000, \"buffer_size\": 5000}
  }" >/dev/null
done

echo "Trạng thái:"
api "$BIFROST_URL/api/providers" \
  | grep -oE '"name":"[a-z]+"|"default_request_timeout_in_seconds":[0-9]+|"max_retries":[0-9]+' \
  | paste - - - | sed 's/"//g'
