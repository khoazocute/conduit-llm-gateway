"""Kiểm chứng decision_rule.py bằng dữ liệu giả — mỗi nhánh của luật quyết định
(CLAUDE.md mục 2) có ít nhất 1 kịch bản biết trước kết quả. Không gọi API, không tốn tiền.
Chạy: python -m unittest discover -s experiments/tests -v (từ thư mục gốc repo)
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from decision_rule import (  # noqa: E402
    apply_decision_rule,
    compute_avg_cost,
    compute_closed_qa_accuracy,
    compute_consistency_rate,
    compute_p95_latency,
    _percentile,
)

# 12 câu closed-QA thật + 1 đáp án đúng/1 đáp án sai mỗi câu (khớp docs/eval-prompts.md).
CLOSED_QA_IDS = [f"cq_{i:02d}" for i in range(1, 13)]
GOOD_ANSWERS = {
    "cq_01": "Canberra", "cq_02": "Natri", "cq_03": "Nguyễn Du", "cq_04": "Sao Thủy",
    "cq_05": "408", "cq_06": "84", "cq_07": "x = 5", "cq_08": "36",
    "cq_09": "Có", "cq_10": "Chi", "cq_11": "(b)", "cq_12": "32",
}
BAD_ANSWER = "câu trả lời sai hoàn toàn, không liên quan"


def make_records(proxy_name, correct_ids, cost, latency, run_index=1, model_selected="m"):
    """1 dòng/câu trong CLOSED_QA_IDS, đúng nếu id nằm trong correct_ids."""
    records = []
    for pid in CLOSED_QA_IDS:
        response = GOOD_ANSWERS[pid] if pid in correct_ids else BAD_ANSWER
        records.append({
            "proxy_name": proxy_name, "prompt_id": pid, "category": "closed_qa",
            "run_index": run_index, "model_selected": model_selected,
            "cost": cost, "latency_ms": latency, "response": response, "status": "success",
        })
    return records


class ComputeFunctions(unittest.TestCase):
    def test_accuracy_counts_only_closed_qa_and_success(self):
        records = make_records("p", CLOSED_QA_IDS[:9], cost=0.01, latency=100)  # 9/12 đúng
        records.append({  # lượt lỗi không được tính là đúng dù response trùng đáp án
            "proxy_name": "p", "prompt_id": "cq_01", "category": "closed_qa",
            "run_index": 2, "model_selected": "m", "cost": 0.01, "latency_ms": 100,
            "response": "Canberra", "status": "error",
        })
        acc = compute_closed_qa_accuracy(records, "p")
        # 13 dòng tổng (12 + 1 lượt lỗi thêm cho cq_01), 9 đúng -> lượt lỗi vẫn tính vào
        # mẫu số (đúng nguyên tắc D7: lượt lỗi tính là 1 lần lặp, không loại bỏ).
        self.assertAlmostEqual(acc, 9 / 13)

    def test_avg_cost_ignores_other_proxy(self):
        records = make_records("p", CLOSED_QA_IDS, cost=0.02, latency=100)
        records += make_records("q", CLOSED_QA_IDS, cost=99.0, latency=100)
        self.assertAlmostEqual(compute_avg_cost(records, "p"), 0.02)

    def test_percentile_known_values(self):
        # numpy-style linear interpolation, kiểm tra bằng tay: [10,20,30,40] p95
        # -> k=(4-1)*0.95=2.85 -> 30 + (40-30)*0.85 = 38.5
        self.assertAlmostEqual(_percentile([10, 20, 30, 40], 95), 38.5)
        self.assertEqual(_percentile([], 95), 0.0)
        self.assertEqual(_percentile([7], 95), 7)

    def test_p95_latency(self):
        records = make_records("p", CLOSED_QA_IDS, cost=0.01, latency=100)
        for i, r in enumerate(records):
            r["latency_ms"] = 100 + i * 10  # 100..210
        p95 = compute_p95_latency(records, "p")
        self.assertAlmostEqual(p95, _percentile([100 + i * 10 for i in range(12)], 95))

    def test_consistency_rate(self):
        records = []
        # prompt A: 3 lần chọn cùng model -> nhất quán
        for run in (1, 2, 3):
            records.append({"proxy_name": "p", "prompt_id": "cq_01", "category": "closed_qa",
                             "run_index": run, "model_selected": "gpt-4o-mini", "cost": 0.01,
                             "latency_ms": 100, "response": "Canberra", "status": "success"})
        # prompt B: đổi model giữa các lần -> không nhất quán
        for run, model in ((1, "gpt-4o-mini"), (2, "gemini-flash"), (3, "gpt-4o-mini")):
            records.append({"proxy_name": "p", "prompt_id": "cq_02", "category": "closed_qa",
                             "run_index": run, "model_selected": model, "cost": 0.01,
                             "latency_ms": 100, "response": "Natri", "status": "success"})
        # 1/2 prompt nhất quán
        self.assertAlmostEqual(compute_consistency_rate(records, "p"), 0.5)


class DecisionRuleBranches(unittest.TestCase):
    """Mỗi test dựng 1 bộ dữ liệu độc lập, biết trước proxy nào phải được chọn."""

    def test_branch1_excludes_low_accuracy_proxy(self):
        # proxyA chỉ đúng 8/12 (66.7% < 80%) -> bị loại dù rẻ nhất.
        records = (
            make_records("proxyA", CLOSED_QA_IDS[:8], cost=0.001, latency=50)
            + make_records("proxyB", CLOSED_QA_IDS, cost=0.02, latency=100)
        )
        result = apply_decision_rule(records, ["proxyA", "proxyB"])
        self.assertNotIn("proxyA", result["candidates_after_qa_filter"])
        self.assertEqual(result["selected_proxy"], "proxyB")

    def test_branch2_picks_clear_cheapest(self):
        # Cả 2 đều đạt accuracy, proxyB rẻ hơn hẳn (>5%) -> thắng ngay ở bước 2.
        records = (
            make_records("proxyB", CLOSED_QA_IDS, cost=0.01, latency=500)
            + make_records("proxyC", CLOSED_QA_IDS, cost=0.02, latency=100)  # rẻ hơn thì lại nhanh hơn
        )
        result = apply_decision_rule(records, ["proxyB", "proxyC"])
        self.assertEqual(result["selected_proxy"], "proxyB")

    def test_branch3_cost_tie_breaks_on_latency(self):
        # Chênh lệch chi phí 2% (<5%) -> hòa ở bước 2, proxyE thắng vì latency thấp hơn.
        records = (
            make_records("proxyD", CLOSED_QA_IDS, cost=0.0100, latency=500)
            + make_records("proxyE", CLOSED_QA_IDS, cost=0.0102, latency=300)
        )
        result = apply_decision_rule(records, ["proxyD", "proxyE"])
        self.assertEqual(result["selected_proxy"], "proxyE")

    def test_branch4_latency_tie_breaks_on_consistency(self):
        # Cùng chi phí, cùng p95 latency -> hòa tới bước 4, proxyG thắng vì nhất quán hơn.
        records = []
        for proxy, consistent in (("proxyF", False), ("proxyG", True)):
            for pid in CLOSED_QA_IDS:
                for run in (1, 2, 3):
                    model = "m1" if (consistent or run == 1) else f"m{run}"
                    records.append({
                        "proxy_name": proxy, "prompt_id": pid, "category": "closed_qa",
                        "run_index": run, "model_selected": model,
                        "cost": 0.01, "latency_ms": 200,
                        "response": GOOD_ANSWERS[pid], "status": "success",
                    })
        result = apply_decision_rule(records, ["proxyF", "proxyG"])
        self.assertEqual(compute_avg_cost(records, "proxyF"), compute_avg_cost(records, "proxyG"))
        self.assertEqual(compute_p95_latency(records, "proxyF"), compute_p95_latency(records, "proxyG"))
        self.assertLess(compute_consistency_rate(records, "proxyF"), compute_consistency_rate(records, "proxyG"))
        self.assertEqual(result["selected_proxy"], "proxyG")

    def test_no_candidate_raises(self):
        records = make_records("proxyA", [], cost=0.01, latency=100)  # 0/12 đúng
        with self.assertRaises(ValueError):
            apply_decision_rule(records, ["proxyA"])


if __name__ == "__main__":
    unittest.main()
