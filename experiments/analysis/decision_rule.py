"""
Áp dụng quy tắc quyết định chọn proxy đã khóa trước khi chạy (CLAUDE.md mục 2),
theo đúng thứ tự ưu tiên:

  1. Loại bỏ proxy có tỷ lệ đúng closed-QA < 80%.
  2. Trong số còn lại, chọn proxy có chi phí trung bình/prompt thấp nhất.
  3. Nếu chênh lệch chi phí < 5%, ưu tiên proxy có p95 latency thấp hơn.
  4. Nếu vẫn hòa, ưu tiên proxy có consistency rate cao hơn qua 3 lần lặp.

Định dạng record kỳ vọng (1 dòng = 1 lượt gọi, xem experiments/scripts/run_experiment.py):
  proxy_name, prompt_id, category, run_index, model_selected, cost, latency_ms, response, status
"""

import json
import math
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROMPTS_FILE = SCRIPT_DIR.parent / "prompts" / "prompts.json"

sys.path.insert(0, str(SCRIPT_DIR))
from grading import is_correct  # noqa: E402

CLOSED_QA_PASS_THRESHOLD = 0.80
COST_TIE_THRESHOLD = 0.05  # 5%


def load_records(results_file: Path) -> list[dict[str, Any]]:
    return json.loads(results_file.read_text(encoding="utf-8"))


def _load_closed_qa_answers() -> dict[str, dict[str, str]]:
    """id -> {expected_answer, match_type}, chỉ nhóm closed_qa (mục duy nhất chấm tự động)."""
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["closed_qa"]}


def _percentile(values: list[float], p: float) -> float:
    """Percentile nội suy tuyến tính (giống numpy mặc định). values rỗng -> 0.0."""
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100)
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def compute_closed_qa_accuracy(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Tỷ lệ đúng closed-QA (so response với expected_answer theo match_type,
    dùng đúng luật ở experiments/analysis/grading.py). Không tính prompt code/mở
    vào đây — chỉ closed_qa có đáp án đúng/sai khách quan (CLAUDE.md mục 2)."""
    answers = _load_closed_qa_answers()
    qa_records = [
        r for r in records
        if r["proxy_name"] == proxy_name and r["category"] == "closed_qa"
    ]
    if not qa_records:
        return 0.0
    correct = 0
    for r in qa_records:
        item = answers.get(r["prompt_id"])
        if item is None:
            continue
        if r.get("status") == "success" and is_correct(
            r.get("response") or "", item["expected_answer"], item["match_type"]
        ):
            correct += 1
    return correct / len(qa_records)


def compute_avg_cost(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Chi phí trung bình/prompt của proxy_name — trung bình record['cost'] trên
    toàn bộ lượt gọi (mọi category, 30 prompt x 3 lần) của proxy_name."""
    costs = [r["cost"] for r in records if r["proxy_name"] == proxy_name and r.get("cost") is not None]
    if not costs:
        return 0.0
    return sum(costs) / len(costs)


def compute_p95_latency(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Percentile 95 của record['latency_ms'] cho proxy_name."""
    latencies = [
        r["latency_ms"] for r in records
        if r["proxy_name"] == proxy_name and r.get("latency_ms") is not None
    ]
    return _percentile(latencies, 95)


def compute_consistency_rate(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Tỷ lệ prompt mà model_selected giống nhau qua cả 3 lần lặp, trên tổng số
    prompt, cho proxy_name. Prompt nào chỉ có 1 dòng (lỗi thiếu lượt) vẫn được
    tính "nhất quán" (không có gì để so lệch), ghi rõ khi diễn giải kết quả."""
    by_prompt: dict[str, set[str]] = {}
    for r in records:
        if r["proxy_name"] != proxy_name:
            continue
        by_prompt.setdefault(r["prompt_id"], set()).add(r.get("model_selected") or "")
    if not by_prompt:
        return 0.0
    consistent = sum(1 for models in by_prompt.values() if len(models) == 1)
    return consistent / len(by_prompt)


def apply_decision_rule(records: list[dict[str, Any]], proxy_names: list[str]) -> dict[str, Any]:
    """Áp dụng đúng 4 bước quy tắc quyết định, trả về proxy được chọn + số liệu
    Pareto (cost vs quality vs latency) của từng proxy còn lại sau bước 1."""

    # Bước 1: loại proxy có tỷ lệ đúng closed-QA < 80%
    candidates = [
        name
        for name in proxy_names
        if compute_closed_qa_accuracy(records, name) >= CLOSED_QA_PASS_THRESHOLD
    ]

    if not candidates:
        raise ValueError("Không có proxy nào đạt ngưỡng closed-QA >= 80%")

    # Bước 2: chi phí trung bình/prompt thấp nhất
    costs = {name: compute_avg_cost(records, name) for name in candidates}
    min_cost = min(costs.values())
    near_min_cost = [
        name for name, cost in costs.items()
        if cost <= min_cost * (1 + COST_TIE_THRESHOLD)
    ]

    selected = near_min_cost[0] if len(near_min_cost) == 1 else None

    # Bước 3: nếu chênh lệch chi phí < 5%, xét p95 latency
    if selected is None:
        latencies = {name: compute_p95_latency(records, name) for name in near_min_cost}
        min_latency = min(latencies.values())
        tied_on_latency = [name for name, lat in latencies.items() if lat == min_latency]
        selected = tied_on_latency[0] if len(tied_on_latency) == 1 else None
    else:
        tied_on_latency = [selected]

    # Bước 4: nếu vẫn hòa, xét consistency rate
    if selected is None:
        consistency = {name: compute_consistency_rate(records, name) for name in tied_on_latency}
        selected = max(consistency, key=consistency.get)

    return {
        "selected_proxy": selected,
        "candidates_after_qa_filter": candidates,
        "pareto_data": {
            name: {
                "closed_qa_accuracy": compute_closed_qa_accuracy(records, name),
                "avg_cost": costs.get(name),
                "p95_latency_ms": compute_p95_latency(records, name),
                "consistency_rate": compute_consistency_rate(records, name),
            }
            for name in candidates
        },
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decision_rule.py <results_file.json>")
        sys.exit(1)

    results_file = Path(sys.argv[1])
    all_records = load_records(results_file)
    proxies = sorted({r["proxy_name"] for r in all_records})

    result = apply_decision_rule(all_records, proxies)
    print(json.dumps(result, indent=2, ensure_ascii=False))
