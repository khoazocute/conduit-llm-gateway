"""Kiểm tiền-bay TRƯỚC khi chạy Phase 3 — tầng MIỄN PHÍ (không gọi LLM nào).

Chạy:  PYTHONIOENCODING=utf-8 python experiments/scripts/preflight.py
Thoát mã 1 nếu có mục ⛔ (chặn chạy Phase 3).

Mục đích: Phase 3 tốn tiền thật và không muốn chạy lại lần 2. Mọi thứ kiểm được mà
không gọi LLM thì kiểm hết ở đây. Các rủi ro đã gặp thật và nay được chặn:
  - sửa file cấu hình nhưng chưa nạp vào container/volume -> routing vẫn theo bản cũ
  - model được chọn không có dòng trong model_pricing -> cost ghi 0 TRONG IM LẶNG,
    làm bẩn bước 2 của luật quyết định
  - thiếu nltk punkt -> verifier IFEval trượt hàng loạt
  - claude-sonnet-5 còn sót trong một đường định tuyến -> HTTP 400 vì temperature
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments"
sys.path.insert(0, str(EXP / "analysis"))

PG = ["docker", "exec", "-i", "conduit-postgres", "psql", "-U", "conduit", "-d", "conduit", "-tAc"]
TIER_MODELS = {"SIMPLE": "gpt-4o-mini", "MEDIUM": "claude-haiku", "COMPLEX": "gpt-4o"}
BANNED = "claude-sonnet"  # D12: bo khoi moi duong dinh tuyen

results: list[tuple[str, str, str]] = []  # (trang thai, ten, chi tiet)


def ok(name, detail=""): results.append(("✅", name, detail))
def warn(name, detail=""): results.append(("⚠️ ", name, detail))
def bad(name, detail=""): results.append(("⛔", name, detail))


def sh(cmd, timeout=30):
    # encoding/errors tuong minh: console Windows mac dinh cp1252, script con in tieng Viet
    # -> khong dat thi UnicodeDecodeError lam ca muc kiem bao sai.
    import os
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace", env=env)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception as e:
        return 1, "", str(e)


def strip_comments(text: str, marker: str = "#") -> str:
    """Bo dong comment — de khong khop vao chinh loi giai thich trong config."""
    return "\n".join(l for l in text.splitlines() if not l.strip().startswith(marker))


def http(url, timeout=8):
    code, out, _ = sh(["curl", "-sS", "-m", str(timeout), url], timeout + 5)
    return out if code == 0 else None


# ---------------------------------------------------------------- 1. container
def check_containers():
    need = ["conduit-postgres", "conduit-redis", "conduit-litellm", "conduit-bifrost", "conduit-portkey"]
    _, out, _ = sh(["docker", "ps", "--format", "{{.Names}}"])
    running = set(out.splitlines())
    missing = [c for c in need if c not in running]
    if missing:
        bad("Container", f"chưa chạy: {missing}")
    else:
        ok("Container", f"{len(need)}/{len(need)} chạy")


# ---------------------------------------------------------------- 2. LiteLLM
def check_litellm():
    cfg = ROOT / "proxy-configs" / "litellm" / "config.yaml"
    text = cfg.read_text(encoding="utf-8")
    # dem deployment trong conduit-pool (dong "- model_name: conduit-pool")
    n_pool = text.count("- model_name: conduit-pool")
    pool_block = text.split("conduit-pool", 1)[1] if "conduit-pool" in text else ""
    if n_pool == 0:
        bad("LiteLLM conduit-pool", "không tìm thấy trong config")
        return
    # sonnet khong duoc nam trong conduit-pool (cho phep alias doc lap o tren).
    # Bo comment truoc khi kiem, neu khong se khop vao chinh loi giai thich "da bo sonnet".
    after_first_pool = strip_comments(text[text.index("- model_name: conduit-pool"):])
    if "claude-sonnet-5" in after_first_pool:
        bad("LiteLLM conduit-pool", "VẪN CÒN claude-sonnet-5 -> mìn 400 khi fallback (D12)")
    else:
        ok("LiteLLM conduit-pool", f"{n_pool} deployment, không còn {BANNED}")

    body = http("http://localhost:4000/health/liveliness")
    if body is None:
        bad("LiteLLM sống", "không gọi được :4000")
    else:
        ok("LiteLLM sống", ":4000")


# ---------------------------------------------------------------- 3. Bifrost
def check_bifrost():
    st = http("http://localhost:8080/api/routing/complexity-analyzer-status")
    if not st:
        bad("Bifrost analyzer", "không gọi được :8080")
        return
    s = json.loads(st)
    if s.get("state") != "ready":
        bad("Bifrost analyzer", f"state={s.get('state')} (cần 'ready') "
                                f"-> chạy proxy-configs/bifrost/complexity-setup.sh")
    elif s.get("loaded", 0) < 150:
        warn("Bifrost analyzer", f"loaded={s.get('loaded')} (thường 150)")
    else:
        ok("Bifrost analyzer", f"ready, {s['loaded']} câu mẫu")

    # Han timeout cua analyzer: mac dinh 1.5s QUA CHAT - luot embedding dau tien sau idle
    # mat ~1650ms -> qua han -> tier TRONG -> khong rule nao khop -> roi ve model app xin,
    # ghi nhan nhu quyet dinh routing binh thuong ma KHONG bao loi (do that 2026-10-17).
    cfgs = http("http://localhost:8080/api/routing/complexity-analyzer-config")
    if cfgs:
        sem = json.loads(cfgs).get("semantic") or {}
        t = str(sem.get("timeout", ""))
        try:
            secs = float(t.rstrip("s")) if t.endswith("s") else 0.0
        except ValueError:
            secs = 0.0
        if secs < 5:
            bad("Bifrost timeout", f"semantic.timeout={t or 'khong dat'} — quá chặt, lượt đầu "
                                   f"~1650ms sẽ quá hạn và rơi về model app xin TRONG IM LẶNG. "
                                   f"Chạy lại complexity-setup.sh (đặt 8s)")
        else:
            ok("Bifrost timeout", f"semantic.timeout={t}")
    else:
        warn("Bifrost timeout", "không đọc được complexity-analyzer-config")

    rl = http("http://localhost:8080/api/routing/rules")
    if not rl:
        bad("Bifrost CEL rule", "không đọc được")
        return
    rules = json.loads(rl).get("rules", [])
    found = {}
    for r in rules:
        for tier in TIER_MODELS:
            if tier in str(r.get("cel_expression", "")):
                models = [t.get("model") for t in (r.get("targets") or [])]
                found[tier] = models
    missing = [t for t in TIER_MODELS if t not in found]
    if missing:
        bad("Bifrost CEL rule", f"thiếu rule cho tier {missing} (có {len(rules)} rule)")
        return
    wrong = []
    for tier, want in TIER_MODELS.items():
        got = " ".join(found[tier])
        if want not in got:
            wrong.append(f"{tier}->{got} (cần chứa {want})")
        if BANNED in got:
            wrong.append(f"{tier} VẪN CÒN {BANNED}")
    if wrong:
        bad("Bifrost tier->model", "; ".join(wrong) + " -> chạy lại complexity-setup.sh")
    else:
        ok("Bifrost tier->model", ", ".join(f"{t}->{TIER_MODELS[t]}" for t in TIER_MODELS))


# ---------------------------------------------------------------- 4. Portkey
def check_portkey():
    cfg = json.loads((ROOT / "proxy-configs" / "portkey" / "config.json").read_text(encoding="utf-8"))
    conds = cfg["strategy"]["conditions"]
    thresholds = json.loads((EXP / "prompts" / "manifest.json").read_text(encoding="utf-8")) \
        .get("portkey_prompt_len_thresholds", {})
    lo, hi = thresholds.get("cheap_below"), thresholds.get("expensive_at_or_above")

    got_lo = got_hi = None
    for c in conds:
        q = c["query"].get("metadata.prompt_len", {})
        if "$lt" in q:
            got_lo = (q["$lt"], c["then"])
        if "$gte" in q:
            got_hi = (q["$gte"], c["then"])
    problems = []
    if not got_lo or got_lo[0] != lo:
        problems.append(f"ngưỡng rẻ {got_lo} != manifest {lo}")
    if not got_hi or got_hi[0] != hi:
        problems.append(f"ngưỡng đắt {got_hi} != manifest {hi}")
    if got_hi and BANNED in str(got_hi[1]):
        problems.append(f"tier đắt VẪN TRỎ {BANNED} (D12)")
    if cfg["strategy"]["default"] != TIER_MODELS["MEDIUM"]:
        problems.append(f"default={cfg['strategy']['default']} (cần {TIER_MODELS['MEDIUM']})")
    if problems:
        bad("Portkey rule", "; ".join(problems))
    else:
        ok("Portkey rule", f"<{lo}->{got_lo[1]}, default->{cfg['strategy']['default']}, >={hi}->{got_hi[1]}")

    # ten target phai la alias co trong model_pricing (backend doc targets[N].name)
    names = [t.get("name") for t in cfg["targets"]]
    ok("Portkey targets", f"{len(names)} target: {names}")

    body = http("http://localhost:8787/v1/health")
    if body is None:
        warn("Portkey sống", "không gọi được :8787/v1/health (có thể endpoint khác)")
    else:
        ok("Portkey sống", ":8787")


# ---------------------------------------------------------------- 5. model_pricing
def check_pricing():
    code, out, err = sh([*PG, "SELECT model, unit_type FROM model_pricing ORDER BY model, unit_type;"])
    if code != 0:
        bad("model_pricing", f"không query được DB: {err[:80]}")
        return
    rows = [tuple(l.split("|")) for l in out.splitlines() if "|" in l]
    have = {m for m, _ in rows}
    need = set(TIER_MODELS.values())
    missing = need - have
    if missing:
        bad("model_pricing", f"THIẾU dòng giá cho {sorted(missing)} -> cost sẽ ghi 0 TRONG IM LẶNG")
        return
    # moi model can ca token_input va token_output
    incomplete = [m for m in need
                  if {u for mm, u in rows if mm == m} < {"token_input", "token_output"}]
    if incomplete:
        bad("model_pricing", f"{incomplete} thiếu token_input hoặc token_output")
    else:
        ok("model_pricing", f"đủ giá cho {sorted(need)} ({len(rows)} dòng tổng)")


# ---------------------------------------------------------------- 6. backend config
def check_backend_config():
    y = (ROOT / "backend-gateway" / "src" / "main" / "resources" / "application.yml").read_text(encoding="utf-8")
    problems = []
    if "max-tokens:" not in y:
        problems.append("thiếu app.chat.max-tokens")
    if "temperature:" not in y:
        problems.append("thiếu app.chat.temperature (D12)")
    for line in y.splitlines():
        if line.strip().startswith("bifrost: [") and BANNED in line:
            problems.append(f"chuỗi fallbacks Bifrost VẪN CÓ {BANNED} -> mìn 400 (D12)")
    if problems:
        bad("application.yml", "; ".join(problems))
    else:
        ok("application.yml", "max-tokens + temperature có, fallbacks sạch")

    body = http("http://localhost:8081/api/actuator/health") or http("http://localhost:8081/api/agents")
    if body is None:
        warn("Backend sống", "không gọi được :8081 — phải khởi động lại backend sau khi đổi config")
    else:
        ok("Backend sống", ":8081")


# ---------------------------------------------------------------- 7. bo de + bo cham
def check_credit():
    """Vi credit cua user thi nghiem co du cho 360 luot khong.

    Het credit giua dot -> cac luot con lai bi tu choi va ghi status=error, ma do la loi
    VI NOI BO can tien, khong phai loi nha cung cap -> ban error_rate cua proxy dang chay.
    Do that 17/10: 360 luot can ~249.000 credit (692/luot), vi chi con 155.681.
    """
    code, out, _ = sh([*PG,
        "SELECT u.email, w.balance FROM credit_wallets w JOIN users u ON u.id=w.user_id "
        "WHERE u.email LIKE 'exp.buyer.%' ORDER BY w.balance DESC LIMIT 1;"])
    if code != 0 or not out:
        warn("Vi credit", "khong tim thay user thi nghiem (exp.buyer.*) - runner se tu tao")
        return
    email, bal = out.split("|")[0], int(out.split("|")[1])
    need_360 = 360 * 1600
    if bal < need_360:
        warn("Vi credit", f"{email} con {bal:,}, uoc can ~{need_360:,} cho 360 luot. "
                          f"Xoa experiments/scripts/.experiment_identity.json de tao danh "
                          f"tinh moi (duoc cap 1.000.000), hoac chia nho dot chay")
    else:
        ok("Vi credit", f"{bal:,} - du cho 360 luot (~{need_360:,})")


def check_prompts_and_graders():
    code, out, err = sh([sys.executable, str(EXP / "prompts" / "validate_prompts.py")])
    if code != 0:
        bad("prompts.json", (out + err)[:120])
    else:
        ok("prompts.json", out.splitlines()[-1][:90] if out else "hợp lệ")

    try:
        import nltk
        nltk.data.find("tokenizers/punkt_tab")
        ok("nltk punkt_tab", "có — verifier IFEval chạy được")
    except LookupError:
        bad("nltk punkt_tab", "THIẾU -> 2 verifier IFEval trượt hàng loạt. "
                              "Chạy: python -c \"import nltk; nltk.download('punkt_tab')\"")
    except ImportError:
        bad("nltk", "chưa cài — pip install -r experiments/requirements.txt")

    code, out, err = sh([sys.executable, "-m", "unittest", "discover", "-s", str(EXP / "tests")], 180)
    tail = (err or out).strip().splitlines()[-1] if (err or out) else ""
    if code != 0:
        bad("Test bộ chấm", tail[:100])
    else:
        ok("Test bộ chấm", tail[:60])


def main():
    check_containers()
    check_litellm()
    check_bifrost()
    check_portkey()
    check_pricing()
    check_backend_config()
    check_credit()
    check_prompts_and_graders()

    print("=" * 78)
    print("PRE-FLIGHT Phase 3 — tầng miễn phí (không gọi LLM)")
    print("=" * 78)
    for state, name, detail in results:
        print(f"{state} {name:24s} {detail}")
    print("=" * 78)
    n_bad = sum(1 for s, _, _ in results if s == "⛔")
    n_warn = sum(1 for s, _, _ in results if s.strip() == "⚠️")
    if n_bad:
        print(f"⛔ {n_bad} mục CHẶN — sửa xong rồi mới chạy Phase 3.")
        sys.exit(1)
    print(f"✅ Không có mục chặn ({n_warn} cảnh báo). Sang được tầng kiểm có gọi LLM.")


if __name__ == "__main__":
    main()
