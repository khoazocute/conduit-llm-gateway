"""
Chạy bộ 30 prompt x 3 proxy x 3 lần lặp (CLAUDE.md mục 2), ghi kết quả thô vào
experiments/results/ để analysis/decision_rule.py xử lý sau.

Khung script — chưa gọi API thật, chỉ định nghĩa cấu trúc hàm và TODO rõ ràng.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = SCRIPT_DIR.parent
PROMPTS_FILE = EXPERIMENTS_DIR / "prompts" / "prompts.json"
PROXIES_FILE = SCRIPT_DIR / "proxies.yaml"
RESULTS_DIR = EXPERIMENTS_DIR / "results"

RUNS_PER_PROMPT = 3


def load_prompts() -> list[dict[str, Any]]:
    """Đọc prompts.json, gộp cả 3 nhóm (closed_qa/code/open_ended) thành 1 list phẳng,
    kèm trường 'category' để phân loại khi chấm điểm."""
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    prompts: list[dict[str, Any]] = []
    for category, items in data.items():
        for item in items:
            prompts.append({**item, "category": category})
    return prompts


def load_proxies() -> dict[str, Any]:
    return yaml.safe_load(PROXIES_FILE.read_text(encoding="utf-8"))["proxies"]


def call_proxy(proxy_name: str, proxy_config: dict[str, Any], prompt: dict[str, Any], run_index: int) -> dict[str, Any]:
    """Gọi 1 prompt tới 1 proxy, 1 lần lặp cụ thể.

    TODO: implement gọi API thật theo từng proxy:
      - litellm: POST {base_url}/chat/completions (OpenAI-compatible), header
        Authorization: Bearer <LITELLM_MASTER_KEY>, body {"model": "auto"/model_name, "messages": [...]}
      - bifrost: POST {base_url}/v1/chat/completions (OpenAI-compatible)
      - portkey: POST {base_url}/v1/chat/completions, header x-portkey-config: <config.json content>

    Trả về dict record chuẩn hóa để ghi vào results/.
    """
    started_at = time.monotonic()

    # TODO: thay bằng lời gọi HTTP thật (requests.post(...))
    response_text = None
    model_selected = None
    cost = None
    status = "not_implemented"

    latency_ms = (time.monotonic() - started_at) * 1000

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proxy_name": proxy_name,
        "prompt_id": prompt["id"],
        "category": prompt["category"],
        "run_index": run_index,
        "model_selected": model_selected,
        "cost": cost,
        "latency_ms": latency_ms,
        "response": response_text,
        "status": status,
    }


def run_all() -> list[dict[str, Any]]:
    """Lặp 30 prompt x 3 proxy x 3 lần (270 lượt gọi), trả về danh sách record."""
    prompts = load_prompts()
    proxies = load_proxies()

    records: list[dict[str, Any]] = []
    for prompt in prompts:
        for proxy_name, proxy_config in proxies.items():
            for run_index in range(1, RUNS_PER_PROMPT + 1):
                record = call_proxy(proxy_name, proxy_config, prompt, run_index)
                records.append(record)

    return records


def save_results(records: list[dict[str, Any]]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / f"run_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    out_file.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_file


if __name__ == "__main__":
    results = run_all()
    output_path = save_results(results)
    print(f"Wrote {len(results)} records to {output_path}")
