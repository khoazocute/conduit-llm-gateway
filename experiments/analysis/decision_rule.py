"""
Áp dụng quy tắc quyết định chọn proxy đã khóa trước khi chạy (CLAUDE.md mục 2),
theo đúng thứ tự ưu tiên:

  1. Loại bỏ proxy có tỷ lệ đúng closed-QA < 80%.
  2. Trong số còn lại, chọn proxy có chi phí trung bình/prompt thấp nhất.
  3. Nếu chênh lệch chi phí < 5%, ưu tiên proxy có p95 latency thấp hơn.
  4. Nếu vẫn hòa, ưu tiên proxy có consistency rate cao hơn qua 3 lần lặp.

Khung script — TODO tính toán thật khi có dữ liệu từ experiments/results/.
"""

import json
import sys
from pathlib import Path
from typing import Any

CLOSED_QA_PASS_THRESHOLD = 0.80
COST_TIE_THRESHOLD = 0.05  # 5%


def load_records(results_file: Path) -> list[dict[str, Any]]:
    return json.loads(results_file.read_text(encoding="utf-8"))


def compute_closed_qa_accuracy(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Tỷ lệ đúng closed-QA (gồm cả 'code' nếu được coi là có đáp án đúng/sai
    khách quan — điều chỉnh theo cách CLAUDE.md phân loại khi có dữ liệu thật).

    TODO: so khớp record['response'] với expected_answer (từ prompts.json) theo
    match_type (exact/contains/regex), tính tỷ lệ đúng trên tổng số lượt closed_qa
    của proxy_name.
    """
    raise NotImplementedError


def compute_avg_cost(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Chi phí trung bình / prompt của proxy_name.

    TODO: trung bình record['cost'] trên toàn bộ lượt gọi (30 prompt x 3 lần) của
    proxy_name.
    """
    raise NotImplementedError


def compute_p95_latency(records: list[dict[str, Any]], proxy_name: str) -> float:
    """TODO: percentile 95 của record['latency_ms'] cho proxy_name."""
    raise NotImplementedError


def compute_consistency_rate(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Tỷ lệ prompt mà model_selected giống nhau qua cả 3 lần lặp, trên tổng số
    prompt, cho proxy_name.

    TODO: group theo prompt_id, kiểm tra record['model_selected'] có giống nhau
    ở cả 3 run_index hay không.
    """
    raise NotImplementedError


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
