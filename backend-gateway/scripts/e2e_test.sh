#!/bin/bash
# E2E test script for Auth + Agent vertical (backend-gateway)
# Runs the full checklist from CLAUDE.md section 8.7 against a live backend.
# Requires: backend running at localhost:8081/api, docker-compose stack up (Postgres reachable via `docker exec conduit-postgres psql`).

BASE="http://localhost:8081/api"
PASS=0
FAIL=0
RESULTS=()

# Unique emails per run so re-running the script doesn't collide with previous data.
RUN_ID=$(date +%s)
USER_EMAIL="e2e.user.${RUN_ID}@conduit.dev"
ADMIN_EMAIL="e2e.admin.${RUN_ID}@conduit.dev"
OTHER_EMAIL="e2e.other.${RUN_ID}@conduit.dev"
PASSWORD="password123"

COOKIE_JAR=$(mktemp)

json_get() {
  # $1 = json string, $2 = key (top-level, simple string/number field)
  echo "$1" | grep -o "\"$2\":\"[^\"]*\"" | head -1 | cut -d'"' -f4
}

json_get_nested_id() {
  # extracts the FIRST "id":"..." occurrence (used for user.id in AuthResponse)
  echo "$1" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4
}

check() {
  local name="$1" expected="$2" actual="$3" body="$4"
  if [ "$expected" == "$actual" ]; then
    PASS=$((PASS+1))
    RESULTS+=("PASS | $name | expected=$expected actual=$actual")
  else
    FAIL=$((FAIL+1))
    RESULTS+=("FAIL | $name | expected=$expected actual=$actual | body=$body")
  fi
}

http() {
  # $1=method $2=url $3=data(optional) $4=extra_curl_args(optional, e.g. -H "Authorization: Bearer x")
  local method="$1" url="$2" data="$3"
  shift 3
  if [ -n "$data" ]; then
    curl -s -w "\n%{http_code}" -X "$method" "$url" -H "Content-Type: application/json" -d "$data" "$@"
  else
    curl -s -w "\n%{http_code}" -X "$method" "$url" "$@"
  fi
}

split_body_code() {
  # sets globals BODY and CODE from a curl -w "\n%{http_code}" response
  BODY=$(echo "$1" | sed '$d')
  CODE=$(echo "$1" | tail -n1)
}

echo "==================================================================="
echo " E2E test run: $RUN_ID"
echo "==================================================================="

# --- 1. Register user ---
RESP=$(curl -s -w "\n%{http_code}" -c "$COOKIE_JAR" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"E2E User\"}")
split_body_code "$RESP"
check "register user -> 201" "201" "$CODE" "$BODY"
USER_ID=$(json_get_nested_id "$BODY")
USER_ACCESS=$(json_get "$BODY" "access_token")
[ -n "$(echo "$BODY" | grep -o '"created_at":"[^"]*"')" ] && check "register: created_at populated (not null)" "true" "true" "" || check "register: created_at populated (not null)" "true" "false" "$BODY"
echo "$BODY" | grep -q '"refresh_token"' && check "register: no refresh_token leaked in JSON body" "absent" "present" "$BODY" || check "register: no refresh_token leaked in JSON body" "absent" "absent" ""

# --- 2. Duplicate register -> 409 ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"Dup\"}")
split_body_code "$RESP"
check "duplicate email register -> 409" "409" "$CODE" "$BODY"

# --- 3. Validation error -> 400 ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"bad-email","password":"123","full_name":""}')
split_body_code "$RESP"
check "invalid register payload -> 400" "400" "$CODE" "$BODY"
echo "$BODY" | grep -q '"full_name"' && check "validation details use snake_case field names" "true" "true" "" || check "validation details use snake_case field names" "true" "false" "$BODY"

# --- 4. Login ---
RESP=$(curl -s -w "\n%{http_code}" -c "$COOKIE_JAR" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$PASSWORD\"}")
split_body_code "$RESP"
check "login -> 200" "200" "$CODE" "$BODY"
USER_ACCESS=$(json_get "$BODY" "access_token")

# --- 5. Login with wrong password -> 401 ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"wrongpassword\"}")
split_body_code "$RESP"
check "login wrong password -> 401" "401" "$CODE" "$BODY"

# --- 6. GET /users/me ---
RESP=$(curl -s -w "\n%{http_code}" "$BASE/users/me" -H "Authorization: Bearer $USER_ACCESS")
split_body_code "$RESP"
check "GET /users/me with token -> 200" "200" "$CODE" "$BODY"

# --- 7. GET /users/me without token -> 401 ---
RESP=$(curl -s -w "\n%{http_code}" "$BASE/users/me")
split_body_code "$RESP"
check "GET /users/me without token -> 401" "401" "$CODE" "$BODY"

# --- 8. POST /agents as role=user -> 403 ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents" \
  -H "Authorization: Bearer $USER_ACCESS" -H "Content-Type: application/json" \
  -d '{"title":"Blocked Agent","price_vnd":1000,"default_credit_granted":10}')
split_body_code "$RESP"
check "POST /agents as role=user -> 403" "403" "$CODE" "$BODY"

# --- 9. Promote to creator via SQL, re-login ---
docker exec conduit-postgres psql -U conduit -d conduit -c "UPDATE users SET role='creator' WHERE id='$USER_ID';" > /dev/null
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$PASSWORD\"}")
split_body_code "$RESP"
CREATOR_ACCESS=$(json_get "$BODY" "access_token")
echo "$BODY" | grep -q '"role":"creator"' && check "re-login reflects promoted role=creator" "true" "true" "" || check "re-login reflects promoted role=creator" "true" "false" "$BODY"

# --- 10. Create agent as creator -> 201, draft ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents" \
  -H "Authorization: Bearer $CREATOR_ACCESS" -H "Content-Type: application/json" \
  -d '{"title":"E2E Agent","introduction":"An automated test agent","price_vnd":1000,"default_credit_granted":10}')
split_body_code "$RESP"
check "POST /agents as creator -> 201" "201" "$CODE" "$BODY"
AGENT_ID=$(json_get_nested_id "$BODY")
echo "$BODY" | grep -q '"status":"draft"' && check "new agent status = draft" "true" "true" "" || check "new agent status = draft" "true" "false" "$BODY"
echo "$BODY" | grep -q '"created_at":null' && check "agent created_at populated (not null)" "true" "false" "$BODY" || check "agent created_at populated (not null)" "true" "true" ""

# --- 11. GET /agents/mine?status=draft ---
RESP=$(curl -s -w "\n%{http_code}" "$BASE/agents/mine?status=draft" -H "Authorization: Bearer $CREATOR_ACCESS")
split_body_code "$RESP"
check "GET /agents/mine?status=draft -> 200" "200" "$CODE" "$BODY"
echo "$BODY" | grep -q "$AGENT_ID" && check "agents/mine includes newly created agent" "true" "true" "" || check "agents/mine includes newly created agent" "true" "false" "$BODY"

# --- 12. Submit agent -> pending ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents/$AGENT_ID/submit" -H "Authorization: Bearer $CREATOR_ACCESS")
split_body_code "$RESP"
check "POST /agents/{id}/submit -> 200" "200" "$CODE" "$BODY"
echo "$BODY" | grep -q '"status":"pending"' && check "agent status after submit = pending" "true" "true" "" || check "agent status after submit = pending" "true" "false" "$BODY"

# --- 13. Submit again (wrong status) -> 409 ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents/$AGENT_ID/submit" -H "Authorization: Bearer $CREATOR_ACCESS")
split_body_code "$RESP"
check "double-submit (pending->pending) -> 409" "409" "$CODE" "$BODY"

# --- 14. Register admin, promote, login ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"E2E Admin\"}")
split_body_code "$RESP"
ADMIN_ID=$(json_get_nested_id "$BODY")
docker exec conduit-postgres psql -U conduit -d conduit -c "UPDATE users SET role='admin' WHERE id='$ADMIN_ID';" > /dev/null
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$PASSWORD\"}")
split_body_code "$RESP"
ADMIN_ACCESS=$(json_get "$BODY" "access_token")

# --- 15. Non-admin cannot list pending -> 403 ---
RESP=$(curl -s -w "\n%{http_code}" "$BASE/admin/agents/pending" -H "Authorization: Bearer $CREATOR_ACCESS")
split_body_code "$RESP"
check "non-admin GET /admin/agents/pending -> 403" "403" "$CODE" "$BODY"

# --- 16. Admin lists pending, sees our agent ---
RESP=$(curl -s -w "\n%{http_code}" "$BASE/admin/agents/pending" -H "Authorization: Bearer $ADMIN_ACCESS")
split_body_code "$RESP"
check "admin GET /admin/agents/pending -> 200" "200" "$CODE" "$BODY"
echo "$BODY" | grep -q "$AGENT_ID" && check "pending list includes our agent" "true" "true" "" || check "pending list includes our agent" "true" "false" "$BODY"

# --- 17. Admin approves ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/admin/agents/$AGENT_ID/approve" -H "Authorization: Bearer $ADMIN_ACCESS")
split_body_code "$RESP"
check "admin approve -> 200" "200" "$CODE" "$BODY"
echo "$BODY" | grep -q '"status":"published"' && check "agent status after approve = published" "true" "true" "" || check "agent status after approve = published" "true" "false" "$BODY"

# --- 18. Public listing shows published agent (no auth) ---
RESP=$(curl -s -w "\n%{http_code}" "$BASE/agents")
split_body_code "$RESP"
check "GET /agents (public, no auth) -> 200" "200" "$CODE" "$BODY"
echo "$BODY" | grep -q "$AGENT_ID" && check "public listing includes published agent" "true" "true" "" || check "public listing includes published agent" "true" "false" "$BODY"

# --- 19. PATCH published agent by owner -> 409 ---
RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/agents/$AGENT_ID" \
  -H "Authorization: Bearer $CREATOR_ACCESS" -H "Content-Type: application/json" \
  -d '{"title":"Changed"}')
split_body_code "$RESP"
check "PATCH published agent (owner) -> 409" "409" "$CODE" "$BODY"

# --- 20. PATCH by non-owner -> 403 (ABAC) ---
RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/agents/$AGENT_ID" \
  -H "Authorization: Bearer $ADMIN_ACCESS" -H "Content-Type: application/json" \
  -d '{"title":"Hacked"}')
split_body_code "$RESP"
check "PATCH agent by non-owner (ABAC) -> 403" "403" "$CODE" "$BODY"

# --- 21. Unpublish by owner -> 200 ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents/$AGENT_ID/unpublish" -H "Authorization: Bearer $CREATOR_ACCESS")
split_body_code "$RESP"
check "POST /agents/{id}/unpublish (owner) -> 200" "200" "$CODE" "$BODY"
echo "$BODY" | grep -q '"status":"unpublished"' && check "agent status after unpublish = unpublished" "true" "true" "" || check "agent status after unpublish = unpublished" "true" "false" "$BODY"

# --- 22. Admin: list users, update status ---
RESP=$(curl -s -w "\n%{http_code}" "$BASE/admin/users?page=0&size=50" -H "Authorization: Bearer $ADMIN_ACCESS")
split_body_code "$RESP"
check "admin GET /admin/users -> 200" "200" "$CODE" "$BODY"
echo "$BODY" | grep -q "$USER_EMAIL" && check "admin user list includes our test user" "true" "true" "" || check "admin user list includes our test user" "true" "false" "$BODY"

# --- 23. Register a third "other" user for ban test ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$OTHER_EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"E2E Other\"}")
split_body_code "$RESP"
OTHER_ID=$(json_get_nested_id "$BODY")

# --- 24. Admin bans the other user ---
RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/admin/users/$OTHER_ID/status" \
  -H "Authorization: Bearer $ADMIN_ACCESS" -H "Content-Type: application/json" \
  -d '{"status":"banned"}')
split_body_code "$RESP"
check "admin PATCH /admin/users/{id}/status (ban) -> 200" "200" "$CODE" "$BODY"
echo "$BODY" | grep -q '"status":"banned"' && check "user status updated to banned" "true" "true" "" || check "user status updated to banned" "true" "false" "$BODY"

# --- 25. Banned user cannot login -> 401 ---
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$OTHER_EMAIL\",\"password\":\"$PASSWORD\"}")
split_body_code "$RESP"
check "banned user login -> 401" "401" "$CODE" "$BODY"

# --- 26. Logout revokes refresh token ---
RESP=$(curl -s -w "\n%{http_code}" -b "$COOKIE_JAR" -c "$COOKIE_JAR" -X POST "$BASE/auth/logout" \
  -H "Authorization: Bearer $USER_ACCESS")
split_body_code "$RESP"
check "POST /auth/logout -> 204" "204" "$CODE" "$BODY"

RESP=$(curl -s -w "\n%{http_code}" -b "$COOKIE_JAR" -X POST "$BASE/auth/refresh")
split_body_code "$RESP"
check "POST /auth/refresh after logout (revoked) -> 401" "401" "$CODE" "$BODY"

# --- 27a. Unmapped route within a public (permitAll) prefix -> 404 (not 500) ---
RESP=$(curl -s -w "\n%{http_code}" "$BASE/auth/no-such-endpoint")
split_body_code "$RESP"
check "unmapped route under permitAll prefix -> 404" "404" "$CODE" "$BODY"

# --- 27b. Unmapped route outside any permitAll rule -> 401 (security rejects before routing, by design) ---
RESP=$(curl -s -w "\n%{http_code}" "$BASE/no-such-route")
split_body_code "$RESP"
check "unmapped route requiring auth -> 401 (not 500)" "401" "$CODE" "$BODY"

rm -f "$COOKIE_JAR"

echo ""
echo "==================================================================="
echo " RESULTS"
echo "==================================================================="
for r in "${RESULTS[@]}"; do
  echo "$r"
done
echo ""
echo "-------------------------------------------------------------------"
echo "TOTAL: $((PASS+FAIL))  PASS: $PASS  FAIL: $FAIL"
echo "-------------------------------------------------------------------"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
