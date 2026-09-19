#!/bin/bash
# E2E cross-vertical workflow test: Auth+Agent (Hùng) -> Credit+Chat+Payment (Khoa).
# creator tạo agent -> admin duyệt -> user mua (Mock Payment) -> webhook -> credit vào ví
# -> chat qua proxy. Kèm security acceptance test (CLAUDE.md mục 7): webhook sai chữ ký bị từ chối,
# duplicate callback không cộng credit 2 lần.
#
# Yêu cầu: backend chạy ở localhost:8081/api, docker-compose up (container conduit-postgres), openssl.
# Lưu ý: nếu .env chỉ có API key placeholder thì bước chat sẽ lỗi ở upstream — script kiểm tra
# đúng nhánh đó (lỗi phải báo về client và KHÔNG bị trừ credit, CLAUDE.md mục 5).

BASE="http://localhost:8081/api"
MOCK_SECRET="${MOCK_WEBHOOK_SECRET:-dev-only-mock-webhook-secret}"
PASS=0
FAIL=0
RESULTS=()

RUN_ID=$(date +%s)
PASSWORD="password123"
CREATOR_EMAIL="wf.creator.${RUN_ID}@conduit.dev"
ADMIN_EMAIL="wf.admin.${RUN_ID}@conduit.dev"
BUYER_EMAIL="wf.buyer.${RUN_ID}@conduit.dev"
OTHER_EMAIL="wf.other.${RUN_ID}@conduit.dev"

PRICE_VND=50000
# credit ~ 1 per token x1.5 markup (CLAUDE.md muc 4) and Gemini Flash spends reasoning tokens even on short answers,
# so the grant must be realistic — 100 credit is (correctly) rejected as "Insufficient credit balance" by a real chat.
CREDIT_GRANTED=50000

check() {
  local name="$1" expected="$2" actual="$3" body="$4"
  if [ "$expected" == "$actual" ]; then
    PASS=$((PASS+1)); RESULTS+=("PASS | $name | expected=$expected actual=$actual")
  else
    FAIL=$((FAIL+1)); RESULTS+=("FAIL | $name | expected=$expected actual=$actual | body=$body")
  fi
}

json_str() { echo "$1" | grep -o "\"$2\":\"[^\"]*\"" | head -1 | cut -d'"' -f4; }
json_num() { echo "$1" | grep -o "\"$2\":-\?[0-9]*" | head -1 | cut -d':' -f2; }
first_id() { echo "$1" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4; }

# request helper: sets BODY and CODE
req() {
  local method="$1" url="$2" token="$3" data="$4"
  local args=(-s -w "\n%{http_code}" -X "$method" "$url")
  [ -n "$token" ] && args+=(-H "Authorization: Bearer $token")
  [ -n "$data" ] && args+=(-H "Content-Type: application/json" -d "$data")
  local resp; resp=$(curl "${args[@]}")
  BODY=$(echo "$resp" | sed '$d'); CODE=$(echo "$resp" | tail -n1)
}

register_and_login() {  # $1=email $2=role(optional) -> sets USER_ID, TOKEN
  req POST "$BASE/auth/register" "" "{\"email\":\"$1\",\"password\":\"$PASSWORD\",\"full_name\":\"WF $1\"}"
  USER_ID=$(first_id "$BODY")
  if [ -n "$2" ]; then
    docker exec conduit-postgres psql -U conduit -d conduit -c "UPDATE users SET role='$2' WHERE id='$USER_ID';" > /dev/null
  fi
  req POST "$BASE/auth/login" "" "{\"email\":\"$1\",\"password\":\"$PASSWORD\"}"
  TOKEN=$(json_str "$BODY" access_token)
}

sign() { printf '%s' "$1" | openssl dgst -sha256 -hmac "$MOCK_SECRET" | awk '{print $NF}'; }

echo "=== Cross-vertical workflow test (run $RUN_ID) ==="

# --- Setup actors ---
register_and_login "$CREATOR_EMAIL" creator; CREATOR_TOKEN=$TOKEN
register_and_login "$ADMIN_EMAIL" admin;     ADMIN_TOKEN=$TOKEN
register_and_login "$BUYER_EMAIL";           BUYER_TOKEN=$TOKEN
register_and_login "$OTHER_EMAIL";           OTHER_TOKEN=$TOKEN

# --- Hùng's vertical: creator -> agent -> admin approves ---
req POST "$BASE/agents" "$CREATOR_TOKEN" "{\"title\":\"WF Agent $RUN_ID\",\"introduction\":\"workflow test agent\",\"price_vnd\":$PRICE_VND,\"default_credit_granted\":$CREDIT_GRANTED}"
check "creator creates agent -> 201" 201 "$CODE" "$BODY"
AGENT_ID=$(first_id "$BODY")

req POST "$BASE/agents/$AGENT_ID/submit" "$CREATOR_TOKEN" ""
check "creator submits agent -> 200" 200 "$CODE" "$BODY"
req POST "$BASE/admin/agents/$AGENT_ID/approve" "$ADMIN_TOKEN" ""
check "admin approves agent -> 200" 200 "$CODE" "$BODY"

# --- Khoa's vertical: wallet starts at 0 ---
req GET "$BASE/wallet" "$BUYER_TOKEN" ""
check "new buyer wallet -> 200" 200 "$CODE" "$BODY"
check "new buyer wallet balance = 0" 0 "$(json_num "$BODY" balance)" "$BODY"

# --- Purchase (Mock Payment) ---
req POST "$BASE/agents/$AGENT_ID/purchases" "$BUYER_TOKEN" '{"payment_method":"mock"}'
check "buyer creates purchase -> 201" 201 "$CODE" "$BODY"
TX_REF=$(json_str "$BODY" transaction_ref)
check "purchase starts as pending" pending "$(json_str "$BODY" payment_status)" "$BODY"

req GET "$BASE/wallet" "$BUYER_TOKEN" ""
check "balance still 0 before webhook" 0 "$(json_num "$BODY" balance)" "$BODY"

# --- Security: wrong webhook signature must be rejected ---
WH_BODY="{\"transaction_ref\":\"$TX_REF\",\"result\":\"success\"}"
BAD=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/payments/webhook/mock" \
  -H "Content-Type: application/json" -H "X-Webhook-Signature: deadbeef" -d "$WH_BODY")
check "webhook with WRONG signature -> 400" 400 "$BAD" ""
NOSIG=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/payments/webhook/mock" \
  -H "Content-Type: application/json" -d "$WH_BODY")
check "webhook with NO signature -> 400" 400 "$NOSIG" ""

req GET "$BASE/wallet" "$BUYER_TOKEN" ""
check "balance still 0 after rejected webhooks" 0 "$(json_num "$BODY" balance)" "$BODY"

# --- Valid webhook ---
SIG=$(sign "$WH_BODY")
OK=$(curl -s -w "\n%{http_code}" -X POST "$BASE/payments/webhook/mock" \
  -H "Content-Type: application/json" -H "X-Webhook-Signature: $SIG" -d "$WH_BODY")
check "webhook with valid signature -> 200" 200 "$(echo "$OK" | tail -n1)" "$(echo "$OK" | sed '$d')"

req GET "$BASE/purchases/$TX_REF" "$BUYER_TOKEN" ""
check "purchase is now paid" paid "$(json_str "$BODY" payment_status)" "$BODY"
req GET "$BASE/wallet" "$BUYER_TOKEN" ""
check "balance = default_credit_granted after paid" "$CREDIT_GRANTED" "$(json_num "$BODY" balance)" "$BODY"

# --- Security: duplicate callback must not grant credit twice ---
DUP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/payments/webhook/mock" \
  -H "Content-Type: application/json" -H "X-Webhook-Signature: $SIG" -d "$WH_BODY")
check "duplicate webhook callback -> 200 (idempotent)" 200 "$DUP" ""
req GET "$BASE/wallet" "$BUYER_TOKEN" ""
check "balance unchanged after duplicate webhook" "$CREDIT_GRANTED" "$(json_num "$BODY" balance)" "$BODY"

req GET "$BASE/wallet/transactions" "$BUYER_TOKEN" ""
check "wallet transactions -> 200" 200 "$CODE" "$BODY"
echo "$BODY" | grep -q '"type":"purchase_grant"' && check "ledger has a purchase_grant entry" yes yes "" || check "ledger has a purchase_grant entry" yes no "$BODY"
GRANTS=$(echo "$BODY" | grep -o '"type":"purchase_grant"' | wc -l | tr -d ' ')
check "exactly ONE purchase_grant entry (no double credit)" 1 "$GRANTS" "$BODY"

# --- Re-buying an already purchased agent ---
req POST "$BASE/agents/$AGENT_ID/purchases" "$BUYER_TOKEN" '{"payment_method":"mock"}'
check "buying an already-purchased agent -> 409" 409 "$CODE" "$BODY"

# --- Purchase access control: other user cannot read someone else's purchase ---
req GET "$BASE/purchases/$TX_REF" "$OTHER_TOKEN" ""
echo "other-user purchase lookup code: $CODE" > /dev/null
[ "$CODE" == "403" ] || [ "$CODE" == "404" ] && check "other user cannot read buyer's purchase (403/404)" ok ok "" || check "other user cannot read buyer's purchase (403/404)" "403|404" "$CODE" "$BODY"

# --- Chat ---
req POST "$BASE/conversations" "$OTHER_TOKEN" "{\"agent_id\":\"$AGENT_ID\"}"
[ "$CODE" == "403" ] || [ "$CODE" == "409" ] && check "non-purchaser cannot open a conversation (403/409)" ok ok "" || check "non-purchaser cannot open a conversation (403/409)" "403|409" "$CODE" "$BODY"

req POST "$BASE/conversations" "$BUYER_TOKEN" "{\"agent_id\":\"$AGENT_ID\"}"
check "buyer opens conversation -> 201" 201 "$CODE" "$BODY"
CONV_ID=$(first_id "$BODY")

BAL_BEFORE_CHAT=$(json_num "$(curl -s "$BASE/wallet" -H "Authorization: Bearer $BUYER_TOKEN")" balance)
# Validation failure on the SSE endpoint must be a real 400 (was masked as 401 via the /error dispatch).
EMPTY_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/conversations/$CONV_ID/messages" \
  -H "Authorization: Bearer $BUYER_TOKEN" -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" -d '{"content":""}')
check "empty chat message -> 400 (not masked as 401)" 400 "$EMPTY_CODE" ""

# Send the Vietnamese body from a UTF-8 file: passing non-ASCII via `curl -d` on Windows git-bash mangles the encoding.
SSE_REQ_FILE=$(mktemp); printf '{"content":"Xin chào, 1+1 bằng mấy?"}' > "$SSE_REQ_FILE"
SSE_BODY_FILE=$(mktemp)
SSE_META=$(curl -s -N --max-time 90 -o "$SSE_BODY_FILE" -w "%{http_code} %{content_type}" -X POST "$BASE/conversations/$CONV_ID/messages" \
  -H "Authorization: Bearer $BUYER_TOKEN" -H "Content-Type: application/json; charset=utf-8" \
  -H "Accept: text/event-stream" --data-binary @"$SSE_REQ_FILE")
rm -f "$SSE_REQ_FILE"
SSE_EXIT=$?
SSE=$(cat "$SSE_BODY_FILE"); rm -f "$SSE_BODY_FILE"
echo "--- SSE response (meta: $SSE_META, curl exit: $SSE_EXIT) ---"; echo "$SSE" | head -n 12; echo "--------------------"
BAL_AFTER_CHAT=$(json_num "$(curl -s "$BASE/wallet" -H "Authorization: Bearer $BUYER_TOKEN")" balance)

# A real SSE reply, terminated cleanly. (An earlier version of this check passed falsely on a 401 JSON body.)
check "chat responds HTTP 200 text/event-stream" "200 text/event-stream" "$(echo "$SSE_META" | sed 's/;.*//')" "$SSE"
check "SSE stream terminates cleanly (curl exit 0, not cut off)" 0 "$SSE_EXIT" "$SSE"
echo "$SSE" | grep -q "^event:" && check "stream contains SSE events" yes yes "" || check "stream contains SSE events" yes no "$SSE"

db() { docker exec conduit-postgres psql -U conduit -d conduit -t -A -c "$1" | tr -d '[:space:]'; }

if echo "$SSE" | grep -q "^event:done"; then
  # Successful chat: real provider usage -> credit deducted, fully logged, ledger consistent.
  CHARGED=$(db "select credit_charged from messages where conversation_id='$CONV_ID' and role='assistant' order by created_at desc limit 1;")
  check "successful chat streamed a 'done' event" yes yes ""
  [ "$BAL_AFTER_CHAT" -lt "$BAL_BEFORE_CHAT" ] && check "successful chat deducted credit" yes yes "" || check "successful chat deducted credit" yes no "before=$BAL_BEFORE_CHAT after=$BAL_AFTER_CHAT"
  check "balance drop == messages.credit_charged" "$((BAL_BEFORE_CHAT - BAL_AFTER_CHAT))" "$CHARGED" ""
  check "usage_logs row: status=success with real token counts" 1 "$(db "select count(*) from usage_logs ul join messages m on m.id=ul.message_id where m.conversation_id='$CONV_ID' and ul.status='success' and ul.token_input>0 and ul.token_output>0;")" ""
  check "routing_decisions row recorded (proxy_name=litellm)" 1 "$(db "select count(*) from routing_decisions rd join messages m on m.id=rd.message_id where m.conversation_id='$CONV_ID' and rd.proxy_name='litellm';")" ""
  check "credit_transactions usage_deduct amount == credit_charged" "$CHARGED" "$(db "select abs(amount) from credit_transactions where type='usage_deduct' and related_message_id=(select id from messages where conversation_id='$CONV_ID' and role='assistant' order by created_at desc limit 1);")" ""
elif echo "$SSE" | grep -q "Chat provider error"; then
  # No usable provider key: the failure must surface as an SSE error and must NOT be billed.
  check "provider failure surfaces as an SSE error event" yes yes ""
  check "failed chat does NOT charge credit (billing only on real usage)" "$BAL_BEFORE_CHAT" "$BAL_AFTER_CHAT" "$SSE"
else
  check "chat outcome is a success or a provider error" yes no "$(echo "$SSE" | head -c 200)"
fi

req GET "$BASE/conversations/$CONV_ID/messages" "$BUYER_TOKEN" ""
check "list messages -> 200" 200 "$CODE" "$BODY"

# --- Admin surfaces (Khoa) ---
req GET "$BASE/admin/api-keys" "$ADMIN_TOKEN" ""
check "admin GET /admin/api-keys -> 200" 200 "$CODE" "$BODY"
req GET "$BASE/admin/api-keys" "$BUYER_TOKEN" ""
check "non-admin GET /admin/api-keys -> 403" 403 "$CODE" "$BODY"
req GET "$BASE/admin/model-pricing" "$ADMIN_TOKEN" ""
check "admin GET /admin/model-pricing -> 200" 200 "$CODE" "$BODY"
req GET "$BASE/admin/model-pricing" "$BUYER_TOKEN" ""
check "non-admin GET /admin/model-pricing -> 403" 403 "$CODE" "$BODY"

echo ""
echo "==================================================================="
for r in "${RESULTS[@]}"; do echo "$r"; done
echo "-------------------------------------------------------------------"
echo "TOTAL: $((PASS+FAIL))  PASS: $PASS  FAIL: $FAIL"
echo "-------------------------------------------------------------------"
[ "$FAIL" -gt 0 ] && exit 1
exit 0
