#!/bin/bash
# Phep thu tiem loi provider — D15 (docs/roadmap.md muc 4, dang ky TRUOC khi chay).
#
# Do: khi provider OpenAI khong dung duoc nua, proxy nao PHUC HOI duoc (chuyen sang
# Anthropic/Gemini) va tra gia bao nhieu ve thoi gian.
#
# ⚠️ Ket qua phep thu nay KHONG duoc dung de chon lai proxy. Luat 4 buoc da khoa, da ap
# tren 720 luot, ket luan la litellm. Day la bang chung bo sung cho phan GIOI HAN.
#
# Loi tiem (giong nhau cho ca 3 proxy): OPENAI_API_KEY khong hop le.
#   - litellm, bifrost : ghi de env cua container qua docker-compose.faultinject.yml
#   - portkey          : ghi de env cua TIEN TRINH BACKEND (Portkey nhan key tu backend
#                        qua header x-portkey-config, khong doc env container no)
# Key Anthropic/Gemini GIU HOP LE.
#
# Item: 5 item GSM8K da khoa trong D15 — chon theo luat "id nho nhat trong so 36 item ma
# CA 3 proxy deu chon model OpenAI va nhat quan 3/3 lan o thi nghiem 720 luot", de ca 3
# proxy phoi nhiem loi BANG NHAU.
#
# Chay: bash experiments/scripts/fault_injection.sh
#       NO_CALLS=1 bash experiments/scripts/fault_injection.sh   # chi bootstrap, khong goi API
#
# Script TU DONG hoan tac: luon dung 3 container ve cau hinh that o cuoi, ke ca khi loi.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend-gateway"
OUT_DIR="$ROOT_DIR/experiments/results/fault-injection-$(date +%Y%m%d-%H%M%S)"
LOG_DIR="$OUT_DIR/logs"
mkdir -p "$LOG_DIR"

# Khoa trong D15 — KHONG doi khi chay.
IDS="gsm8k_01,gsm8k_03,gsm8k_06,gsm8k_08,gsm8k_12"
RUNS=3
PROXIES="litellm bifrost portkey"
BAD_KEY="sk-d15-fault-injection-invalid-key"
NO_CALLS="${NO_CALLS:-}"

echo "=== D15 — tiem loi provider ==="
echo "Item (khoa trong D15): $IDS"
echo "So luot du kien: 5 item x $RUNS lan x 3 proxy = 45"
echo "Ket qua: $OUT_DIR"
echo ""

set -a
# shellcheck disable=SC1090
source <(tr -d '\r' < "$ROOT_DIR/.env")
set +a

# May remap port (docker-compose.override.yml, VD may Khoa: Bifrost 18080 vi 8080 la Tomcat) phai
# giu file override khi tao lai container, neu khong Bifrost bi dung o cong goc va khong len duoc.
# `-f` tuong minh lam docker compose BO QUA override tu dong, nen phai ghep tay.
BASE_COMPOSE=(-f docker-compose.yml)
[ -f "$ROOT_DIR/docker-compose.override.yml" ] && BASE_COMPOSE+=(-f docker-compose.override.yml)

# Giu lai key THAT de con tra ve dung gia tri cho nhanh nao can
REAL_OPENAI_KEY="$OPENAI_API_KEY"

restore() {
  echo ""
  echo "=== Hoan tac: dung 3 container ve cau hinh that ==="
  stop_backend
  (cd "$ROOT_DIR" && docker compose "${BASE_COMPOSE[@]}" up -d --force-recreate litellm bifrost >/dev/null 2>&1) \
    && echo "  litellm + bifrost da quay ve doc .env" \
    || echo "  !! HOAN TAC LOI - chay tay: docker compose ${BASE_COMPOSE[*]} up -d --force-recreate litellm bifrost" >&2
}
trap restore EXIT

wait_backend_ready() {
  for _ in $(seq 1 30); do
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/api/agents 2>/dev/null || echo "")
    [ "$code" = "200" ] && return 0
    sleep 3
  done
  return 1
}

stop_backend() {
  local pid
  pid=$(netstat -ano | grep ':8081 ' | grep LISTENING | awk '{print $5}' | head -1 || true)
  if [ -n "$pid" ]; then
    taskkill //F //PID "$pid" //T >/dev/null 2>&1 || true
    sleep 2
  fi
}

echo "=== Bat loi: OPENAI_API_KEY khong hop le trong container litellm + bifrost ==="
(cd "$ROOT_DIR" && docker compose "${BASE_COMPOSE[@]}" -f docker-compose.faultinject.yml \
   up -d --force-recreate litellm bifrost) || { echo "Khong bat duoc loi" >&2; exit 1; }

# Cho bifrost healthy lai (no co healthcheck); litellm chi can cong 4000 tra loi.
for _ in $(seq 1 40); do
  bf=$(docker inspect --format '{{.State.Health.Status}}' conduit-bifrost 2>/dev/null || echo none)
  [ "$bf" = "healthy" ] && break
  sleep 3
done
echo "  bifrost: $(docker inspect --format '{{.State.Health.Status}}' conduit-bifrost 2>/dev/null)"
echo ""

FAILED=()
for proxy in $PROXIES; do
  echo "=== Proxy: $proxy ==="
  stop_backend
  export CHAT_ACTIVE_PROXY="$proxy"
  if [ "$proxy" = "litellm" ]; then
    export CHAT_DEFAULT_MODEL=conduit-pool
  else
    unset CHAT_DEFAULT_MODEL
  fi

  # Nhanh portkey: backend PHAI mang key sai, vi Portkey nhan key tu backend.
  # Hai nhanh kia: backend khong gui key OpenAI nen de key that cung khong anh huong,
  # nhung dat sai luon cho nhat quan - mot loi duy nhat, moi duong deu thay.
  export OPENAI_API_KEY="$BAD_KEY"

  (
    cd "$BACKEND_DIR"
    nohup ./mvnw spring-boot:run >"$LOG_DIR/backend_${proxy}.log" 2>&1 &
  )
  if ! wait_backend_ready; then
    echo "  Bo qua $proxy - backend khong len duoc. Xem $LOG_DIR/backend_${proxy}.log" >&2
    FAILED+=("$proxy")
    continue
  fi
  echo "  Backend san sang (active-proxy=$proxy, OPENAI_API_KEY da bi lam sai)"

  if [ "$NO_CALLS" = "1" ]; then
    echo "  NO_CALLS=1 -> khong goi luot nao."
    continue
  fi

  PYTHONIOENCODING=utf-8 python "$ROOT_DIR/experiments/scripts/run_experiment.py" \
      --proxy-name "$proxy" --runs "$RUNS" --ids "$IDS" --out-dir "$OUT_DIR" \
      2>&1 | tee "$LOG_DIR/runner_${proxy}.log" | grep -E "^\[|status=|Da ghi|Đã ghi" || true
done

export OPENAI_API_KEY="$REAL_OPENAI_KEY"

echo ""
if [ ${#FAILED[@]} -gt 0 ]; then
  echo "Proxy co van de: ${FAILED[*]}"
fi
echo "Ket qua tho: $OUT_DIR"
echo "Phan tich: PYTHONIOENCODING=utf-8 python experiments/analysis/fault_report.py \"$OUT_DIR\""
