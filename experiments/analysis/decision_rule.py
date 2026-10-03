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
    CÁC LƯỢT THÀNH CÔNG (status == "success") của proxy_name.

    Lượt lỗi KHÔNG tính vào đây (dù vẫn tính vào mẫu số của compute_closed_qa_accuracy
    và compute_consistency_rate — D7, lỗi vẫn là 1 lần lặp). Lý do: lượt lỗi ghi
    cost=0.0 (không có usage thật để tính giá — CLAUDE.md mục 5, "billing chỉ tính
    khi có usage thật"), nhưng $0 không có nghĩa là "rẻ" — nếu tính cả lượt lỗi vào
    trung bình, 1 proxy hay lỗi sẽ trông rẻ hơn giả tạo (phát hiện của Khoa,
    docs/tasks/2026-09-28/log-khoa.md, chốt 2026-10-03). Tỷ lệ lỗi được báo cáo
    riêng qua compute_error_rate() — không gộp vào chi phí để không che giấu rủi ro
    độ tin cậy, cũng không thưởng cho nó."""
    costs = [
        r["cost"] for r in records
        if r["proxy_name"] == proxy_name and r.get("status") == "success" and r.get("cost") is not None
    ]
    if not costs:
        return 0.0
    return sum(costs) / len(costs)


def compute_error_rate(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Tỷ lệ lượt lỗi (status != "success") trên tổng số lượt của proxy_name, mọi
    category. KHÔNG phải 1 bước của quy tắc quyết định (quy tắc đã khóa, CLAUDE.md
    mục 2, không tự thêm bước) — chỉ để báo cáo minh bạch cạnh avg_cost, vì giờ
    avg_cost chỉ tính trên lượt thành công nên không còn phản ánh độ tin cậy."""
    proxy_records = [r for r in records if r["proxy_name"] == proxy_name]
    if not proxy_records:
        return 0.0
    errors = sum(1 for r in proxy_records if r.get("status") != "success")
    return errors / len(proxy_records)


def compute_p95_latency(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Percentile 95 của record['latency_ms'] cho proxy_name."""
    latencies = [
        r["latency_ms"] for r in records
        if r["proxy_name"] == proxy_name and r.get("latency_ms") is not None
    ]
    return _percentile(latencies, 95)


_ERROR_SENTINEL = "__ERROR__"  # khong dung "" de tranh lan voi model_selected bi thieu du lieu that su


def compute_consistency_rate(records: list[dict[str, Any]], proxy_name: str) -> float:
    """Tỷ lệ prompt mà model_selected giống nhau qua cả 3 lần lặp, trên tổng số
    prompt, cho proxy_name.

    Lượt lỗi (status != "success", model_selected thường là None) được tính là
    1 "lựa chọn" riêng biệt (_ERROR_SENTINEL) — cố ý, không bỏ qua: quyết định hòa
    thuận (Khoa, 2026-10-03). Một prompt có 2 lần ra cùng model + 1 lần lỗi vẫn là
    KHÔNG nhất quán, vì proxy không trả về cùng 1 kết quả cả 3 lần — lỗi tự nó là
    1 dạng mất nhất quán của quyết định routing, không phải trường hợp trung lập."""
    by_prompt: dict[str, set[str]] = {}
    for r in records:
        if r["proxy_name"] != proxy_name:
            continue
        selection = r.get("model_selected") if r.get("status") == "success" else _ERROR_SENTINEL
        by_prompt.setdefault(r["prompt_id"], set()).add(selection or _ERROR_SENTINEL)
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
    tie_unresolved = False
    tied_candidates: list[str] = []
    if selected is None:
        consistency = {name: compute_consistency_rate(records, name) for name in tied_on_latency}
        max_consistency = max(consistency.values())
        still_tied = [name for name, c in consistency.items() if c == max_consistency]
        if len(still_tied) > 1:
            # Hòa cả 4 bước - KHÔNG âm thầm chọn proxy đầu tiên trong danh sách (Khoa,
            # 2026-10-03). Vẫn trả về 1 "selected_proxy" (thứ tự alphabet, để luôn có
            # kết quả dùng được), nhưng đánh dấu rõ để không báo cáo như thể luật đã
            # phân biệt được - cần bàn thêm với GVHD/Khoa nếu thực sự xảy ra ở Phase E.
            tie_unresolved = True
            tied_candidates = sorted(still_tied)
            selected = tied_candidates[0]
        else:
            selected = still_tied[0]

    return {
        "selected_proxy": selected,
        "tie_unresolved": tie_unresolved,
        "tied_candidates": tied_candidates,
        "candidates_after_qa_filter": candidates,
        "pareto_data": {
            name: {
                "closed_qa_accuracy": compute_closed_qa_accuracy(records, name),
                "avg_cost": costs.get(name),
                "error_rate": compute_error_rate(records, name),
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
