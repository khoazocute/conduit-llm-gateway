"""RQ3: Gateway them bao nhieu do tre so voi goi truc tiep nha cung cap.

Do 3 tang, xen ke tung vong de cung dieu kien mang:
  direct_<p>   : goi thang API nha cung cap (OpenAI, Anthropic)
  litellm_<p>  : goi qua LiteLLM (localhost:4000), cung model
  mock_litellm : LiteLLM alias gia conduit-mock (khong goi nha cung cap)
  mock_conduit : qua app Conduit (backend, JWT, ABAC, DB, SSE) voi CHAT_DEFAULT_MODEL=conduit-mock

  overhead proxy  = litellm_<p> - direct_<p>
  overhead ung dung = mock_conduit - mock_litellm   (khong goi nha cung cap, khong ton phi)

Chi phi: 4 duong x N luot goi that voi prompt rat ngan (khoang 15 token vao, toi da 16 token ra).
Chay: python experiments/scripts/rq3_latency.py --n 20 --mock-n 30
Can: docker compose up (postgres, redis, litellm), backend chay voi CHAT_DEFAULT_MODEL=conduit-mock,
OPENAI_API_KEY / ANTHROPIC_API_KEY / LITELLM_MASTER_KEY trong .env.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import run_experiment as rx  # noqa: E402  (tai dung dang nhap + agent thi nghiem)

ROOT = Path(__file__).resolve().parents[2]
PROMPT = "Reply with the single word: ok"


def load_env() -> dict[str, str]:
    env = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def pct(xs: list[float], q: float) -> float:
    s = sorted(xs)
    k = (len(s) - 1) * q
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--mock-n", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=2)
    args = ap.parse_args()
    env = load_env()
    s = requests.Session()

    def direct_openai() -> None:
        r = s.post("https://api.openai.com/v1/chat/completions",
                   headers={"Authorization": f"Bearer {env['OPENAI_API_KEY']}"},
                   json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": PROMPT}],
                         "max_tokens": 16, "temperature": 0}, timeout=60)
        r.raise_for_status()

    def direct_anthropic() -> None:
        r = s.post("https://api.anthropic.com/v1/messages",
                   headers={"x-api-key": env["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                   json={"model": "claude-haiku-4-5-20251001", "max_tokens": 16, "temperature": 0,
                         "messages": [{"role": "user", "content": PROMPT}]}, timeout=60)
        r.raise_for_status()

    def litellm(model: str):
        def call() -> None:
            r = s.post("http://localhost:4000/v1/chat/completions",
                       headers={"Authorization": f"Bearer {env['LITELLM_MASTER_KEY']}"},
                       json={"model": model, "messages": [{"role": "user", "content": PROMPT}],
                             "max_tokens": 16, "temperature": 0}, timeout=60)
            r.raise_for_status()
        return call

    identity = rx.ensure_experiment_identity()
    _, token = rx.register_and_login(identity["buyer_email"])
    conv = rx._req("POST", "/conversations", token=token, json_body={"agent_id": identity["agent_id"]})
    conv.raise_for_status()
    conv_id = conv.json()["id"]

    def conduit_mock() -> None:
        r = s.post(f"{rx.BASE}/conversations/{conv_id}/messages", json={"content": PROMPT},
                   headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"},
                   stream=True, timeout=60)
        done = False
        for line in r.iter_lines(decode_unicode=True):
            if line and line.startswith("event:") and line.split(":", 1)[1].strip() in ("done", "error"):
                done = line.endswith("done")
                break
        r.close()
        if not done:
            raise RuntimeError("conduit chat khong ket thuc bang event done")

    paid = {"direct_openai": direct_openai, "litellm_openai": litellm("gpt-4o-mini"),
            "direct_anthropic": direct_anthropic, "litellm_anthropic": litellm("claude-haiku")}
    free = {"mock_litellm": litellm("conduit-mock"), "mock_conduit": conduit_mock}

    results: dict[str, list[float]] = {k: [] for k in [*paid, *free]}
    errors: dict[str, int] = {k: 0 for k in results}

    def run(group: dict, n: int) -> None:
        for i in range(n + args.warmup):
            for name, fn in group.items():
                t = time.perf_counter()
                try:
                    fn()
                except Exception as e:  # noqa: BLE001
                    if i >= args.warmup:
                        errors[name] += 1
                        print(f"loi {name}: {e}", file=sys.stderr)
                    continue
                ms = (time.perf_counter() - t) * 1000
                if i >= args.warmup:
                    results[name].append(ms)

    run(free, args.mock_n)
    run(paid, args.n)

    summary = {}
    for k, xs in results.items():
        if xs:
            summary[k] = {"n": len(xs), "errors": errors[k], "mean_ms": round(statistics.mean(xs), 1),
                          "median_ms": round(statistics.median(xs), 1), "p95_ms": round(pct(xs, 0.95), 1),
                          "stdev_ms": round(statistics.pstdev(xs), 1)}
    def diff(a: str, b: str) -> dict:
        return {"mean_ms": round(summary[a]["mean_ms"] - summary[b]["mean_ms"], 1),
                "median_ms": round(summary[a]["median_ms"] - summary[b]["median_ms"], 1)}
    overhead = {"proxy_openai": diff("litellm_openai", "direct_openai"),
                "proxy_anthropic": diff("litellm_anthropic", "direct_anthropic"),
                "app_layer": diff("mock_conduit", "mock_litellm")}
    out = {"run_at": datetime.now(timezone.utc).isoformat(), "prompt": PROMPT, "summary": summary,
           "overhead": overhead, "raw_ms": results}
    path = ROOT / "experiments" / "results" / f"rq3-latency-{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"summary": summary, "overhead": overhead}, indent=2))
    print("saved", path)


if __name__ == "__main__":
    main()
