"""
Chạy bộ prompt qua app Conduit thật (D3, docs/roadmap.md mục 4 — KHÔNG gọi thẳng
3 proxy), ghi kết quả thô vào experiments/results/ để analysis/decision_rule.py
xử lý sau.

Cách chạy (đọc trước khi chạy thật — tốn phí, CLAUDE.md mục 2):
  python experiments/scripts/run_experiment.py --limit 1 --proxy-name litellm

Tham số:
  --limit N       chỉ chạy N prompt đầu (mặc định 30 = tất cả). Tuần 28/09 chỉ
                   chạy --limit 1 để verify runner, chưa chạy dry-run 27 lượt.
  --runs N        số lần lặp/prompt (mặc định 3, theo CLAUDE.md mục 2).
  --proxy-name    nhãn ghi vào record["proxy_name"] — chỉ để ghi chép, KHÔNG tự
                   đổi backend đang chạy proxy nào (đó là việc của
                   CHAT_ACTIVE_PROXY khi khởi động backend, xem application.yml).

Yêu cầu: backend chạy ở localhost:8081/api, docker-compose up (postgres/redis +
đúng proxy đang test), export LITELLM_MASTER_KEY trước khi chạy backend
(CLAUDE.md mục 8, bẫy môi trường).
"""

import argparse
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = SCRIPT_DIR.parent
PROMPTS_FILE = EXPERIMENTS_DIR / "prompts" / "prompts.json"
RESULTS_DIR = EXPERIMENTS_DIR / "results"
IDENTITY_FILE = SCRIPT_DIR / ".experiment_identity.json"

BASE = "http://localhost:8081/api"
PASSWORD = "experiment-runner-password-123"
# 1.000.000: du cho mot nguoi chay het 360 luot (uoc ~576.000 o muc 1.600 credit/luot).
# Truoc day 200.000 - do that 17/10 cho thay 360 luot can ~249.000 nen vi se can giua
# dot, va cac luot sau bi ghi status=error lam ban error_rate. Credit la don vi NOI BO
# (khong phai tien that) nen de du thoai mai khong ton gi.
CREDIT_GRANTED = 1000000
REQUEST_TIMEOUT = 60  # giây, chờ SSE - khớp router_settings.timeout (D7) + biên độ mạng.


def load_prompts() -> list[dict[str, Any]]:
    """Đọc prompts.json, gộp cả 3 nhóm thành 1 list phẳng, kèm 'category'."""
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    prompts: list[dict[str, Any]] = []
    for category, items in data.items():
        for item in items:
            prompts.append({**item, "category": category})
    return prompts


def select_prompts(prompts: list[dict[str, Any]], sets: str, per_set: int) -> list[dict[str, Any]]:
    """Lọc theo bộ (--sets) và lấy N item đầu mỗi bộ (--per-set), giữ thứ tự trong prompts.json.
    Dry-run K5 dùng --per-set 1 (1 item/bộ); Phase 3 chia đôi theo bộ bằng --sets."""
    wanted = {s.strip() for s in sets.split(",") if s.strip()}
    unknown = wanted - {p["category"] for p in prompts}
    if unknown:
        raise SystemExit(f"--sets có bộ không tồn tại: {sorted(unknown)}")
    selected: list[dict[str, Any]] = []
    taken: dict[str, int] = {}
    for p in prompts:
        if wanted and p["category"] not in wanted:
            continue
        if per_set and taken.get(p["category"], 0) >= per_set:
            continue
        taken[p["category"]] = taken.get(p["category"], 0) + 1
        selected.append(p)
    return selected


def skip_ran_items(prompts: list[dict[str, Any]], patterns: list[str]) -> list[dict[str, Any]]:
    """Bỏ item đã có trong các file kết quả cũ (đợt mở rộng cỡ mẫu — D14).

    Lọc theo **item**, không theo lượt: item nào đã chạy (dù 1 lượt) thì bỏ hẳn, vì đợt
    mở rộng chỉ cần chạy item MỚI. Lấy chính dữ liệu đã chạy làm nguồn đúng, an toàn hơn
    lọc theo số thứ tự trong ID (ID chỉ là quy ước đặt tên, đổi quy ước là lọc sai).

    Không khớp file nào thì NỔ, không âm thầm chạy lại hết — gõ sai đường dẫn mà vẫn chạy
    thì trả tiền hai lần cho toàn bộ bộ đề.
    """
    if not patterns:
        raise SystemExit("--skip-ran: phải cho ít nhất 1 file kết quả")
    ran: set[str] = set()
    n_files = 0
    for pattern in patterns:
        pp = Path(pattern)
        matches = sorted(pp.parent.glob(pp.name)) if any(c in pattern for c in "*?[") else [pp]
        for path in matches:
            if not path.exists():
                continue
            for r in json.loads(path.read_text(encoding="utf-8")):
                if r.get("prompt_id"):
                    ran.add(r["prompt_id"])
            n_files += 1
    if not n_files:
        raise SystemExit(f"--skip-ran: khong file nao khop {patterns} - kiem lai duong dan")
    kept = [p for p in prompts if p["id"] not in ran]
    print(f"--skip-ran: {n_files} file, {len(ran)} item da chay -> con {len(kept)}/{len(prompts)} item moi")
    if not kept:
        raise SystemExit("--skip-ran: khong con item nao de chay")
    return kept


# Credit uoc can cho MOI luot, dung de kiem so du truoc khi chay. Do that tu dot 24 luot
# 16/10: trung binh 692 credit/luot, cao nhat 1.595. Lay 1.600 cho du bien an toan.
CREDIT_PER_RUN_ESTIMATE = 1600


def assert_enough_credit(buyer_token: str, n_runs: int) -> None:
    """Chan dot chay neu vi KHONG du credit cho het so luot da len ke hoach.

    Vi sao can: het credit giua dot thi moi luot con lai bi tu choi va ghi
    status=error - nhung do la loi VI MINH CAN TIEN NOI BO, khong phai loi nha cung cap,
    the la `error_rate` cua dung proxy dang chay luc do bi ban. Do that 17/10: 360 luot
    can ~249.000 credit ma vi chi con 155.681 -> se chet o khoang luot 225.
    """
    resp = _req("GET", "/wallet", token=buyer_token)
    if resp.status_code != 200:
        print(f"  (khong doc duoc so du vi: HTTP {resp.status_code} - bo qua buoc kiem)")
        return
    balance = resp.json().get("balance", 0)
    need = n_runs * CREDIT_PER_RUN_ESTIMATE
    print(f"  vi credit: {balance:,} | uoc can cho {n_runs} luot: ~{need:,} "
          f"({CREDIT_PER_RUN_ESTIMATE}/luot)")
    if balance < need:
        sys.exit(
            f"\n⛔ DUNG LAI: vi chi con {balance:,} credit, uoc can ~{need:,} cho {n_runs} luot.\n"
            f"   Het credit giua dot se lam cac luot con lai bi ghi status=error va ban\n"
            f"   error_rate cua proxy dang chay. Cach xu ly:\n"
            f"   1. Xoa {IDENTITY_FILE.name} roi chay lai -> tao danh tinh moi,\n"
            f"      duoc cap {CREDIT_GRANTED:,} credit; HOAC\n"
            f"   2. Chia nho dot chay (--sets) de moi dot nam trong so du hien co; HOAC\n"
            f"   3. Nap thêm credit cho vi qua webhook mock / admin.")


def plan_runs(prompts: list[dict[str, Any]], runs: int,
              resume_file: "Path | None") -> tuple[list[tuple[dict[str, Any], int]], int]:
    """Danh sach (prompt, run_index) can chay, va so luot duoc bo qua nho --resume.

    Bo qua nhung luot DA THANH CONG trong file cu -> khong tra tien hai lan cho cung mot
    luot khi dot chay bi dut giua chung (rui ro ghi o roadmap.md muc 7 "chay tiep tu luot
    loi", truoc day chua co cach lam). Luot LOI thi CHAY LAI: no khong ton tien va moi
    item can du 3 lan lap.
    """
    already: set[tuple[str, int]] = set()
    if resume_file is not None:
        for r in json.loads(resume_file.read_text(encoding="utf-8")):
            if r.get("status") == "success":
                already.add((r.get("prompt_id"), r.get("run_index")))
    planned = [(p, i) for p in prompts for i in range(1, runs + 1)
               if (p["id"], i) not in already]
    return planned, len(already)


def _db(sql: str) -> str:
    """psql trong container — chỉ để ghi log nghiên cứu (đọc cost_upstream, ghi
    response_quality_score: cả 2 không lộ qua API nào), không phải cách gọi model."""
    result = subprocess.run(
        ["docker", "exec", "conduit-postgres", "psql", "-U", "conduit", "-d", "conduit",
         "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def _req(method: str, path: str, token: str | None = None, json_body: dict | None = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{BASE}{path}", json=json_body, headers=headers, timeout=REQUEST_TIMEOUT)


def register_and_login(email: str, role: str | None = None) -> tuple[str, str]:
    """Trả về (user_id, access_token). Nếu email đã tồn tại, chỉ login.
    Cả /auth/register lẫn /auth/login trả về {"access_token", "user": {"id", ...}}."""
    resp = _req("POST", "/auth/register", json_body={
        "email": email, "password": PASSWORD, "full_name": f"Experiment {email}",
    })
    if resp.status_code == 201:
        user_id = resp.json()["user"]["id"]
        if role:
            _db(f"UPDATE users SET role='{role}' WHERE id='{user_id}';")
    elif resp.status_code != 409:  # 409 = email đã tồn tại, coi như bình thường
        raise RuntimeError(f"register {email} failed: {resp.status_code} {resp.text}")

    # Login lại (kể cả vừa register xong) để JWT phản ánh đúng role sau khi đổi qua psql.
    resp = _req("POST", "/auth/login", json_body={"email": email, "password": PASSWORD})
    if resp.status_code != 200:
        raise RuntimeError(f"login {email} failed: {resp.status_code} {resp.text}")
    body = resp.json()
    return body["user"]["id"], body["access_token"]


def ensure_experiment_identity() -> dict[str, Any]:
    """Tạo 1 lần (idempotent): creator + agent (miễn phí, credit lớn) + admin duyệt
    + buyer đã mua. Lưu vào IDENTITY_FILE (gitignored, per-máy) để lần sau tái dùng,
    không tạo rác mỗi lần chạy."""
    if IDENTITY_FILE.exists():
        identity = json.loads(IDENTITY_FILE.read_text(encoding="utf-8"))
        # Xác nhận agent vẫn còn tồn tại (phòng DB bị reset giữa các lần chạy).
        check = _req("GET", f"/agents/{identity['agent_id']}")
        if check.status_code == 200:
            return identity
        print("Agent trong .experiment_identity.json không còn tồn tại — tạo lại.")

    run_id = uuid.uuid4().hex[:8]
    creator_email = f"exp.creator.{run_id}@conduit.dev"
    admin_email = f"exp.admin.{run_id}@conduit.dev"
    buyer_email = f"exp.buyer.{run_id}@conduit.dev"

    _, creator_token = register_and_login(creator_email, role="creator")
    _, admin_token = register_and_login(admin_email, role="admin")
    buyer_id, buyer_token = register_and_login(buyer_email)

    resp = _req("POST", "/agents", token=creator_token, json_body={
        "title": f"Experiment Agent {run_id}",
        "introduction": "Agent dùng riêng cho thí nghiệm đánh giá proxy (D3, không phải agent thật).",
        "price_vnd": 0,  # mien phi -> mua xong cong credit ngay, khong can webhook
        "default_credit_granted": CREDIT_GRANTED,
    })
    if resp.status_code != 201:
        raise RuntimeError(f"create agent failed: {resp.status_code} {resp.text}")
    agent_id = resp.json()["id"]

    resp = _req("POST", f"/agents/{agent_id}/submit", token=creator_token, json_body={})
    if resp.status_code != 200:
        raise RuntimeError(f"submit agent failed: {resp.status_code} {resp.text}")

    resp = _req("POST", f"/admin/agents/{agent_id}/approve", token=admin_token, json_body={})
    if resp.status_code != 200:
        raise RuntimeError(f"approve agent failed: {resp.status_code} {resp.text}")

    resp = _req("POST", f"/agents/{agent_id}/purchases", token=buyer_token,
                json_body={"payment_method": "mock"})
    if resp.status_code != 201:
        raise RuntimeError(f"purchase agent failed: {resp.status_code} {resp.text}")

    identity = {
        "run_id": run_id, "agent_id": agent_id,
        "buyer_email": buyer_email, "buyer_id": buyer_id,
    }
    IDENTITY_FILE.write_text(json.dumps(identity, indent=2), encoding="utf-8")
    print(f"Đã tạo experiment identity mới: agent_id={agent_id}, buyer={buyer_email}")
    return identity


def send_chat_and_read_result(buyer_token: str, agent_id: str, prompt_text: str) -> dict[str, Any]:
    """POST /conversations -> POST .../messages (SSE, chờ done/error) -> GET
    messages để lấy model_used/credit_charged/latency_ms/content thật (đều lộ
    qua API, xem MessageResponse.java — không cần DB cho các trường này)."""
    resp = _req("POST", "/conversations", token=buyer_token, json_body={"agent_id": agent_id})
    if resp.status_code != 201:
        raise RuntimeError(f"create conversation failed: {resp.status_code} {resp.text}")
    conv_id = resp.json()["id"]

    sse_resp = requests.post(
        f"{BASE}/conversations/{conv_id}/messages",
        json={"content": prompt_text},
        headers={"Authorization": f"Bearer {buyer_token}", "Accept": "text/event-stream"},
        stream=True, timeout=REQUEST_TIMEOUT,
    )
    stream_status = "unknown"
    for raw_line in sse_resp.iter_lines(decode_unicode=True):
        if raw_line and raw_line.startswith("event:"):
            event = raw_line.split(":", 1)[1].strip()
            if event in ("done", "error"):
                stream_status = event
                break
    sse_resp.close()

    resp = _req("GET", f"/conversations/{conv_id}/messages", token=buyer_token)
    if resp.status_code != 200:
        raise RuntimeError(f"get messages failed: {resp.status_code} {resp.text}")
    messages = resp.json()["items"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]
    if not assistant_messages:
        raise RuntimeError(f"no assistant message found for conversation {conv_id}")
    last = assistant_messages[-1]

    cost_upstream = 0.0
    if last.get("id"):
        raw_cost = _db(f"SELECT cost_upstream FROM usage_logs WHERE message_id='{last['id']}';")
        cost_upstream = float(raw_cost) if raw_cost else 0.0

    return {
        "stream_status": stream_status,
        "message_id": last.get("id"),
        "content": last.get("content"),
        "model_used": last.get("model_used"),
        "credit_charged": last.get("credit_charged"),
        "latency_ms": last.get("latency_ms"),
        "cost_upstream": cost_upstream,
    }


# Cham diem KHONG dien ra o day nua (D10, 2026-10-14). Runner chi THU output; cham chay
# offline bang experiments/scripts/grade_results.py, vi 4 metric moi can harness khac nhau:
# pass@1 phai chay code trong sandbox, IFEval phai chay verifier chinh thuc. Nho tach ra ma
# mot bo cham chua xong cung khong chan viec chay thi nghiem.
#
# Hau qua can biet: moi record ghi ra co "passed": None. Chay decision_rule.py trước khi
# cham se thay accuracy = 0 va ungraded_runs = toan bo — KHONG phai loi.

def run_one(identity: dict[str, Any], prompt: dict[str, Any], proxy_name: str, run_index: int) -> dict[str, Any]:
    _, buyer_token = register_and_login(identity["buyer_email"])  # fresh login, token het han nhanh

    started = time.monotonic()
    status = "success"
    result: dict[str, Any] = {}
    try:
        result = send_chat_and_read_result(buyer_token, identity["agent_id"], prompt["prompt"])
        if result["stream_status"] != "done":
            status = "error"
    except Exception as e:  # noqa: BLE001 - ghi lại lượt lỗi, không để crash cả batch
        status = "error"
        result = {"content": None, "model_used": None, "latency_ms": None, "cost_upstream": 0.0}
        print(f"  lỗi ở {prompt['id']} run {run_index}: {e}")
    elapsed_ms = (time.monotonic() - started) * 1000  # fallback khi backend không đo được (VD lỗi trước khi có response)
    # Dùng latency_ms backend tự đo (messages.latency_ms, chỉ tính thời gian gọi proxy) thay vì
    # elapsed_ms của runner (cộng thêm round-trip HTTP + SSE parse + GET /messages, review Khoa
    # 2026-10-03: runner cao hơn backend ~300-500ms, làm lệch khi so p95 latency giữa 3 proxy).
    latency_ms = result.get("latency_ms")
    if latency_ms is None:
        latency_ms = elapsed_ms

    message_id = result.get("message_id")

    return {
        "message_id": message_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proxy_name": proxy_name,
        "prompt_id": prompt["id"],
        "category": prompt["category"],
        "run_index": run_index,
        "model_selected": result.get("model_used"),
        "cost": result.get("cost_upstream", 0.0),
        "credit_charged": result.get("credit_charged"),
        "latency_ms": latency_ms,
        "latency_ms_runner": elapsed_ms,  # giữ lại để đối chiếu/debug, không dùng cho decision_rule.py
        "response": result.get("content"),
        "passed": None,  # cham offline bang grade_results.py (D10)
        "metric": prompt.get("metric"),
        "status": status,
    }


def append_result(record: dict[str, Any], out_file: Path) -> None:
    """Ghi ngay sau mỗi lượt (không đợi hết batch) - CLAUDE.md mục 2 + roadmap.md
    mục 7 (rủi ro mất dữ liệu thô khi runner lỗi giữa chừng)."""
    records: list[dict[str, Any]] = []
    if out_file.exists():
        records = json.loads(out_file.read_text(encoding="utf-8"))
    records.append(record)
    out_file.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    # Mac dinh 0 = lay HET. Truoc day default=30 (tu thiet ke 30 prompt cu) nhung bo de gio
    # co 40 item -> chay ca 4 bo ma khong truyen --limit se AM THAM bo mat 10 item IFEval
    # cuoi (IFEval nam cuoi prompts.json). Mat tron mot bo benchmark ma khong bao gi.
    parser.add_argument("--limit", type=int, default=0,
                         help="Chỉ chạy N item đầu (sau khi lọc --sets). 0 = lấy hết.")
    parser.add_argument("--runs", type=int, default=3, help="Số lần lặp/prompt (mặc định 3).")
    parser.add_argument("--proxy-name", default="litellm",
                         help="Nhãn ghi vào record - phải khớp CHAT_ACTIVE_PROXY thật của backend.")
    parser.add_argument("--sets", default="",
                         help="Chỉ chạy các bộ này, cách nhau dấu phẩy (VD humaneval,ifeval). Mặc định: cả 4.")
    parser.add_argument("--resume", metavar="FILE",
                         help="Chạy tiếp vào file kết quả cũ, bỏ qua các lượt ĐÃ thành công "
                              "(không trả tiền hai lần khi đợt chạy bị dứt giữa chừng).")
    parser.add_argument("--per-set", type=int, default=0,
                         help="Lấy N item đầu của MỖI bộ (VD dry-run 1/bộ). 0 = lấy hết.")
    parser.add_argument("--skip-ran", nargs="*", metavar="FILE", default=None,
                         help="Bỏ các item ĐÃ chạy trong các file kết quả này (dùng cho đợt "
                              "mở rộng cỡ mẫu D14: chỉ chạy item mới, không trả tiền lại "
                              "cho item cũ). Khác --resume: --resume lọc theo từng LƯỢT và "
                              "ghi tiếp vào file cũ, --skip-ran lọc theo ITEM và ghi file mới.")
    args = parser.parse_args()

    prompts = select_prompts(load_prompts(), args.sets, args.per_set)
    if args.skip_ran is not None:
        prompts = skip_ran_items(prompts, args.skip_ran)
    if args.limit:
        prompts = prompts[: args.limit]
    identity = ensure_experiment_identity()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / f"run_{args.proxy_name}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"

    # --resume: bo qua nhung (prompt_id, run_index) DA CO trong file ket qua truoc, de
    # khong tra tien hai lan cho cung mot luot khi dot chay bi dut giua chung (rui ro da
    # ghi o roadmap.md muc 7 "chay tiep tu luot loi" nhung truoc day chua co cach lam).
    resume_file = None
    if args.resume:
        resume_file = Path(args.resume)
        if not resume_file.exists():
            sys.exit(f"--resume: khong thay file {resume_file}")
        out_file = resume_file  # ghi tiep vao chinh file cu

    planned, n_skipped = plan_runs(prompts, args.runs, resume_file)
    if resume_file is not None:
        print(f"--resume: bo qua {n_skipped} luot da thanh cong truoc do")
    total = len(planned)

    # Chan TRUOC khi tieu dong nao: vi khong du credit thi dot chay chet giua duong va
    # cac luot con lai bi ghi status=error (ban error_rate). Thà dừng ngay còn hơn.
    if total:
        _, check_token = register_and_login(identity["buyer_email"])
        assert_enough_credit(check_token, total)

    checked_proxy = False
    done = 0
    for prompt, run_index in planned:
        done += 1
        print(f"[{done}/{total}] {prompt['id']} (proxy={args.proxy_name}, run={run_index})...")
        record = run_one(identity, prompt, args.proxy_name, run_index)
        append_result(record, out_file)
        print(f"  -> status={record['status']} model={record['model_selected']} "
              f"cost={record['cost']} passed={record['passed']}")

        # Chan nhan sai NGAY o luot dau: --proxy-name chi la cai NHAN runner tu ghi, con
        # backend ghi proxy that cua no vao routing_decisions.proxy_name. Lech nhau thi ca
        # dot du lieu bi dan nhan sai va phep so sanh thanh vo nghia - ma khong co loi nao
        # bao ra. Phase 3 hai nguoi chay tay nen day la cho de go lech nhat.
        if not checked_proxy and record.get("message_id") and record["status"] == "success":
            checked_proxy = True
            actual = _db("SELECT proxy_name FROM routing_decisions "
                         f"WHERE message_id = '{record['message_id']}';").strip()
            if actual and actual != args.proxy_name:
                sys.exit(
                    f"\n⛔ DUNG LAI: --proxy-name='{args.proxy_name}' nhung backend dang chay "
                    f"proxy '{actual}' (doc tu routing_decisions).\n"
                    f"   Da chay 1 luot roi - xoa {out_file.name} hoac dung --resume sau khi sua.\n"
                    f"   Khoi dong lai backend voi CHAT_ACTIVE_PROXY={args.proxy_name}, "
                    f"hoac doi --proxy-name thanh '{actual}'.")
            print(f"  (da doi chieu: backend that su dang chay proxy '{actual}')")

    print(f"\nĐã ghi {total} record vào {out_file}")


if __name__ == "__main__":
    main()
