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

sys.path.insert(0, str(EXPERIMENTS_DIR / "analysis"))
from grading import is_correct  # noqa: E402

BASE = "http://localhost:8081/api"
PASSWORD = "experiment-runner-password-123"
CREDIT_GRANTED = 200000  # Gemini reasoning token ăn credit nhanh (đã thấy ~580/lượt) - để dư.
REQUEST_TIMEOUT = 60  # giây, chờ SSE - khớp router_settings.timeout (D7) + biên độ mạng.


def load_prompts() -> list[dict[str, Any]]:
    """Đọc prompts.json, gộp cả 3 nhóm thành 1 list phẳng, kèm 'category'."""
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    prompts: list[dict[str, Any]] = []
    for category, items in data.items():
        for item in items:
            prompts.append({**item, "category": category})
    return prompts


def _db(sql: str) -> str:
    """Đọc-only qua psql trong container — chỉ để ghi log nghiên cứu
    (cost_upstream không lộ ra API nào), không phải cách gọi model."""
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
        "content": last.get("content"),
        "model_used": last.get("model_used"),
        "credit_charged": last.get("credit_charged"),
        "latency_ms": last.get("latency_ms"),
        "cost_upstream": cost_upstream,
    }


def grade_closed_qa(prompt: dict[str, Any], response_text: str | None, stream_status: str) -> bool | None:
    if prompt["category"] != "closed_qa":
        return None
    if stream_status != "done" or not response_text:
        return False  # loi = tinh la sai (D7: loi tinh vao mau so, khong loai bo)
    return is_correct(response_text, prompt["expected_answer"], prompt["match_type"])


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

    is_correct_answer = grade_closed_qa(prompt, result.get("content"), result.get("stream_status", ""))

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proxy_name": proxy_name,
        "prompt_id": prompt["id"],
        "category": prompt["category"],
        "run_index": run_index,
        "model_selected": result.get("model_used"),
        "cost": result.get("cost_upstream", 0.0),
        "credit_charged": result.get("credit_charged"),
        "latency_ms": (time.monotonic() - started) * 1000,
        "response": result.get("content"),
        "closed_qa_correct": is_correct_answer,
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
    parser.add_argument("--limit", type=int, default=30, help="Chỉ chạy N prompt đầu (mặc định 30).")
    parser.add_argument("--runs", type=int, default=3, help="Số lần lặp/prompt (mặc định 3).")
    parser.add_argument("--proxy-name", default="litellm",
                         help="Nhãn ghi vào record - phải khớp CHAT_ACTIVE_PROXY thật của backend.")
    args = parser.parse_args()

    prompts = load_prompts()[: args.limit]
    identity = ensure_experiment_identity()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / f"run_{args.proxy_name}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"

    total = len(prompts) * args.runs
    done = 0
    for prompt in prompts:
        for run_index in range(1, args.runs + 1):
            done += 1
            print(f"[{done}/{total}] {prompt['id']} (proxy={args.proxy_name}, run={run_index})...")
            record = run_one(identity, prompt, args.proxy_name, run_index)
            append_result(record, out_file)
            print(f"  -> status={record['status']} model={record['model_selected']} "
                  f"cost={record['cost']} correct={record['closed_qa_correct']}")

    print(f"\nĐã ghi {total} record vào {out_file}")


if __name__ == "__main__":
    main()
