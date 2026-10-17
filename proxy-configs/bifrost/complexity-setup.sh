#!/usr/bin/env bash
# Design Y, nhánh Bifrost (K1, docs/experiment-design.md mục 4): bật Complexity Router và map tier
# → model thật. Chạy SAU setup.sh (D7). Chạy lại nhiều lần vẫn an toàn — rule trùng tên thì xoá
# rồi tạo lại.
#
#   BIFROST_URL=http://localhost:18080 bash proxy-configs/bifrost/complexity-setup.sh   # máy Khoa
#   bash proxy-configs/bifrost/complexity-setup.sh                                      # mặc định :8080
#
# Hai bẫy đã gặp (docs/tasks/2026-10-12/tasks.md, K1):
# - PUT complexity-analyzer-config THAY TOÀN BỘ config → phải gửi lại cả keywords (150 câu mẫu mặc
#   định) + tier_boundaries, thiếu là lỗi 400. Script đọc config đang có rồi chỉ thêm khối semantic,
#   nên giữ nguyên 150 câu mẫu mặc định (experiment-design.md mục 9.2: không tự viết câu mẫu).
# - priority phải khác nhau trong cùng scope, trùng là lỗi 500 → dùng 5 / 6 / 7.
set -euo pipefail

BIFROST_URL="${BIFROST_URL:-http://localhost:8080}"

api() { curl -sS -f -H "Content-Type: application/json" "$@"; }

if ! api "$BIFROST_URL/api/providers" >/dev/null; then
  echo "Không gọi được $BIFROST_URL — Bifrost đã chạy chưa? (docker compose up -d bifrost)" >&2
  exit 1
fi

# 1. Analyzer: giữ keywords + tier_boundaries hiện có, thêm khối semantic.
CFG_FILE="$(mktemp)"
api "$BIFROST_URL/api/routing/complexity-analyzer-config" | python -c '
import json, sys
cfg = json.load(sys.stdin)
for k in ("simple_keywords", "medium_keywords", "complex_keywords"):
    if not cfg.get("keywords", {}).get(k):
        sys.exit(f"config hiện tại thiếu keywords.{k} - không dám PUT (sẽ lỗi 400)")
cfg["semantic"] = {
    "provider": "openai",
    "embedding_model": "text-embedding-3-small",
    # 8s, KHONG dung mac dinh 1.5s. Ly do do duoc (2026-10-17): luot embedding dau tien
    # sau khi idle mat ~1650ms -> VUOT han 1.5s -> analyzer bo cuoc -> complexity_tier
    # TRONG -> khong CEL rule nao khop -> request roi ve model ma app xin (gpt-4o-mini),
    # va duoc ghi nhan nhu mot quyet dinh routing binh thuong, KHONG co loi nao bao ra.
    # Bang chung trong /api/logs: tier=trong, mechanism=skipped, overhead=1647ms. Mot luot
    # khac mat 1465ms - sat han. Neu khong nang, Phase 3 se co nhung luot Bifrost am tham
    # bi tinh nhu "chon gpt-4o-mini", keo consistency_rate xuong va lam Bifrost trong re
    # hon thuc te. Nang han KHONG doi chinh sach dinh tuyen, chi cho analyzer du thoi gian.
    "timeout": "8s",
    "min_similarity": 0,
    "message_history_count": 1,
}
json.dump(cfg, sys.stdout)
' > "$CFG_FILE"
api -X PUT "$BIFROST_URL/api/routing/complexity-analyzer-config" --data-binary "@$CFG_FILE" >/dev/null
rm -f "$CFG_FILE"
echo "+ analyzer: bật semantic (text-embedding-3-small), giữ 150 câu mẫu mặc định"

# Chờ analyzer embed xong 150 câu mẫu (state: ready, loaded: 150).
for _ in $(seq 1 60); do
  status="$(api "$BIFROST_URL/api/routing/complexity-analyzer-status")"
  if echo "$status" | grep -q '"state":"ready"'; then break; fi
  if echo "$status" | grep -q '"state":"failed"'; then echo "! analyzer failed: $status" >&2; exit 1; fi
  sleep 2
done
echo "$status" | grep -oE '"state":"[a-z]+"|"loaded":[0-9]+|"total":[0-9]+' | paste -sd' '

# 2. Ba rule tier → model. Map giống hệt nhánh Portkey (routing-policy.md mục 7).
existing="$(api "$BIFROST_URL/api/routing/rules")"
create_rule() { # $1 tier, $2 provider, $3 model, $4 priority
  local name="design-y-$1"
  local id
  id="$(echo "$existing" | python -c "
import json, sys
rules = json.load(sys.stdin).get('rules') or []
print(next((r['id'] for r in rules if r.get('name') == '$name'), ''))
")"
  if [ -n "$id" ]; then
    api -X DELETE "$BIFROST_URL/api/routing/rules/$id" >/dev/null
  fi
  api -X POST "$BIFROST_URL/api/routing/rules" -d "{
    \"name\": \"$name\",
    \"description\": \"Design Y: complexity_tier $1 -> $2/$3\",
    \"enabled\": true,
    \"cel_expression\": \"complexity_tier == \\\"$1\\\"\",
    \"targets\": [{\"provider\": \"$2\", \"model\": \"$3\", \"weight\": 1}],
    \"scope\": \"global\",
    \"priority\": $4
  }" >/dev/null
  echo "+ rule $name (priority $4): $1 -> $2/$3"
}
create_rule SIMPLE  openai    gpt-4o-mini                 5
create_rule MEDIUM  anthropic claude-haiku-4-5-20251001   6
# COMPLEX dung gpt-4o, KHONG dung claude-sonnet-5: Sonnet bat thinking mac dinh va no
# phan suy nghi cho vua het max_tokens roi tra ve RONG (do 16/10: 512->512 thinking,
# 2048->2048 thinking, ca 2 lan text rong nhung van bi tinh tien). Sonnet cung tu choi
# tham so temperature ("deprecated for this model") nen khong ap duoc greedy decoding.
# gpt-4o cung thuoc tang dat trong pool (CLAUDE.md muc 2) va khong co ca 2 van de do.
create_rule COMPLEX openai    gpt-4o                      7
