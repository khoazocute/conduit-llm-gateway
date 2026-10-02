#!/usr/bin/env bash
# Ép OpenAI lỗi 401 trong Bifrost để kiểm tra chuỗi fallback (review K1), rồi khôi phục.
#
#   BIFROST_URL=http://localhost:18080 bash proxy-configs/bifrost/fallback-test.sh break
#   (chat qua app với CHAT_ACTIVE_PROXY=bifrost → routing_decisions.selected_model phải KHÁC gpt-4o-mini)
#   BIFROST_URL=http://localhost:18080 bash proxy-configs/bifrost/fallback-test.sh restore
#
# break: tắt key OpenAI thật, thêm 1 key giả → mọi lượt gọi OpenAI trả 401. Key thật chỉ bị tắt,
# không bị xoá; giá trị vẫn là tham chiếu env.OPENAI_API_KEY nên script không bao giờ đụng tới key.
set -euo pipefail

BIFROST_URL="${BIFROST_URL:-http://localhost:8080}"
REAL_NAME="OPENAI_API_KEY_auto_detected"
FAKE_NAME="fallback-test-invalid"

api() { curl -sS -H "Content-Type: application/json" "$@"; }
key_id() {
  api "$BIFROST_URL/api/keys" | grep -oE "\"name\":\"$1\",[^}]*\"key_id\":\"[^\"]+\"" \
    | grep -oE '"key_id":"[^"]+"' | cut -d'"' -f4 | head -1
}
set_real_enabled() {
  api -X PUT "$BIFROST_URL/api/providers/openai/keys/$(key_id "$REAL_NAME")" \
    -d "{\"name\":\"$REAL_NAME\",\"value\":\"env.OPENAI_API_KEY\",\"models\":[\"*\"],\"weight\":1,\"enabled\":$1}" >/dev/null
}

case "${1:-}" in
  break)
    [ -n "$(key_id "$REAL_NAME")" ] || { echo "Không thấy key $REAL_NAME — chạy setup.sh trước" >&2; exit 1; }
    set_real_enabled false
    if [ -z "$(key_id "$FAKE_NAME")" ]; then
      api -X POST "$BIFROST_URL/api/providers/openai/keys" \
        -d "{\"name\":\"$FAKE_NAME\",\"value\":\"sk-fallback-test-invalid\",\"models\":[\"*\"],\"weight\":1}" >/dev/null
    fi
    echo "OpenAI đã bị ép lỗi 401. Nhớ chạy '$0 restore' sau khi test."
    ;;
  restore)
    fake="$(key_id "$FAKE_NAME")"
    [ -n "$fake" ] && api -X DELETE "$BIFROST_URL/api/providers/openai/keys/$fake" >/dev/null
    set_real_enabled true
    echo "Đã khôi phục key OpenAI thật."
    ;;
  *)
    echo "Dùng: $0 break|restore" >&2
    exit 1
    ;;
esac
