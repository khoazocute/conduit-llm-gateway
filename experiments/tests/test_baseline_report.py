"""Kiểm baseline_report.py (D18) bằng dữ liệu giả — mỗi phép tính có kịch bản biết trước kết quả.
Không gọi API, không tốn tiền.
Chạy: python -m unittest discover -s experiments/tests -v (từ thư mục gốc repo)
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from baseline_report import (  # noqa: E402
    baseline_name,
    by_category,
    dedupe_runs,
    load_baseline_dir,
    mini_check,
    pareto_front,
    point_metrics,
    upper_bound,
)


def rec(pid, passed, cost, proxy="litellm", run=1, status="success", model="gpt-4o-mini", cat="mmlu"):
    return {"prompt_id": pid, "run_index": run, "proxy_name": proxy, "category": cat,
            "status": status, "passed": passed if status == "success" else None,
            "cost": cost if status == "success" else 0.0,
            "model_selected": model if status == "success" else None}


class DedupeTest(unittest.TestCase):
    def test_success_replaces_earlier_error(self):
        rows = [rec("a", None, 0, status="error"), rec("a", True, 0.002), rec("b", False, 0.001)]
        kept, replaced = dedupe_runs(rows)
        self.assertEqual(replaced, 1)
        self.assertEqual(len(kept), 2)
        self.assertTrue(all(r["status"] == "success" for r in kept))

    def test_error_only_is_kept_as_error(self):
        kept, replaced = dedupe_runs([rec("a", None, 0, status="error")])
        self.assertEqual(replaced, 0)
        self.assertEqual(kept[0]["status"], "error")


class PointMetricsTest(unittest.TestCase):
    def test_error_counts_as_wrong_but_not_in_avg_cost(self):
        name = baseline_name("gpt-4o")
        rows = [rec("a", True, 0.004, proxy=name), rec("b", False, 0.002, proxy=name),
                rec("c", None, 0, proxy=name, status="error"), rec("d", True, 0.003, proxy=name)]
        p = point_metrics(rows, name)
        self.assertEqual(p["kind"], "baseline")
        self.assertAlmostEqual(p["accuracy"], 2 / 4)          # lỗi nằm trong mẫu số
        self.assertAlmostEqual(p["avg_cost"], 0.009 / 3)      # lỗi không kéo chi phí xuống
        self.assertAlmostEqual(p["cost_per_passing"], 0.009 / 2)
        self.assertEqual(p["n_error"], 1)


class ParetoTest(unittest.TestCase):
    def pt(self, name, acc, cost):
        return {"name": name, "accuracy": acc, "avg_cost": cost}

    def test_dominated_point_is_removed(self):
        pts = [self.pt("cheap", 0.85, 0.0001), self.pt("good", 0.95, 0.001),
               self.pt("bad", 0.80, 0.002)]   # đắt hơn VÀ kém hơn cả hai điểm kia
        self.assertEqual(pareto_front(pts), {"cheap", "good"})

    def test_tie_on_one_axis_does_not_dominate(self):
        # D18 ghi "vừa rẻ hơn vừa chính xác hơn" -> bằng độ chính xác thì không loại nhau
        pts = [self.pt("x", 0.85, 0.0001), self.pt("y", 0.85, 0.0002)]
        self.assertEqual(pareto_front(pts), {"x", "y"})


class UpperBoundTest(unittest.TestCase):
    def test_cheapest_correct_model_and_fallback_cost(self):
        by_model = {
            "gpt-4o-mini": [rec("a", True, 0.0001), rec("b", False, 0.0002), rec("c", False, 0.0003)],
            "claude-haiku": [rec("a", True, 0.001, model="claude-haiku"),
                             rec("b", True, 0.002, model="claude-haiku"),
                             rec("c", False, 0.001, model="claude-haiku")],
            "gpt-4o": [rec("a", True, 0.003, model="gpt-4o"), rec("b", True, 0.0015, model="gpt-4o"),
                       rec("c", None, 0, status="error", model="gpt-4o")],
        }
        ub = upper_bound(by_model)
        picks = {x["prompt_id"]: x["model"] for x in ub["per_item"]}
        self.assertEqual(picks, {"a": "gpt-4o-mini", "b": "gpt-4o", "c": None})  # b: 4o rẻ hơn haiku Ở ITEM NÀY
        self.assertEqual(ub["n_covered"], 2)
        self.assertAlmostEqual(ub["accuracy"], 2 / 3)
        # c không ai đúng -> tính chi phí gpt-4o-mini trên c
        self.assertAlmostEqual(ub["cost_total"], 0.0001 + 0.0015 + 0.0003)
        self.assertAlmostEqual(ub["avg_cost"], 0.0019 / 3)

    def test_fallback_error_costs_zero(self):
        by_model = {"gpt-4o-mini": [rec("a", None, 0, status="error")],
                    "claude-haiku": [rec("a", False, 0.001, model="claude-haiku")],
                    "gpt-4o": [rec("a", False, 0.002, model="gpt-4o")]}
        self.assertEqual(upper_bound(by_model)["cost_total"], 0.0)


class MiniCheckTest(unittest.TestCase):
    def test_majority_two_of_three(self):
        merged = []
        # a: LiteLLM đạt 2/3 -> đa số đạt; b: 1/3 -> đa số trượt; c: 3/3 có 1 lượt lỗi -> 2/3 đạt
        for i, ok in enumerate([True, True, False], 1):
            merged.append(rec("a", ok, 0.0001, run=i))
        for i, ok in enumerate([True, False, False], 1):
            merged.append(rec("b", ok, 0.0001, run=i))
        merged += [rec("c", True, 0.0001, run=1), rec("c", True, 0.0001, run=2),
                   rec("c", None, 0, run=3, status="error")]
        merged.append(rec("a", False, 0.001, proxy="bifrost"))  # proxy khác không được tính
        mini = [rec("a", True, 0.0001), rec("b", True, 0.0001), rec("c", True, 0.0001)]
        out = mini_check(mini, merged)
        self.assertEqual(out["n_items"], 3)
        self.assertEqual(out["n_mismatch"], 1)
        self.assertEqual(out["mismatches"][0]["prompt_id"], "b")
        self.assertFalse(out["exceeds_tolerance"])

    def test_exceeds_tolerance_above_four(self):
        merged = [rec(f"i{k}", False, 0.0001, run=r) for k in range(5) for r in (1, 2, 3)]
        mini = [rec(f"i{k}", True, 0.0001) for k in range(5)]
        out = mini_check(mini, merged)
        self.assertEqual(out["n_mismatch"], 5)
        self.assertTrue(out["exceeds_tolerance"])


class LoadAndCategoryTest(unittest.TestCase):
    def test_load_relabels_and_rejects_wrong_model(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            for m in ("gpt-4o-mini", "claude-haiku", "gpt-4o"):
                (base / m).mkdir()
                rows = [rec("a", None, 0, status="error", model=m), rec("a", True, 0.001, model=m)]
                (base / m / "run_litellm_x.json").write_text(json.dumps(rows), encoding="utf-8")
            by_model, replaced = load_baseline_dir(base)
            self.assertEqual(replaced, {"gpt-4o-mini": 1, "claude-haiku": 1, "gpt-4o": 1})
            self.assertEqual(by_model["gpt-4o"][0]["proxy_name"], "baseline-gpt-4o")
            # một lượt do model khác trả lời (vd. fallback) -> phải nổ, không phân tích tiếp
            bad = [rec("a", True, 0.001, model="claude-haiku")]
            (base / "gpt-4o" / "run_litellm_x.json").write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(SystemExit):
                load_baseline_dir(base)

    def test_by_category(self):
        rows = [rec("a", True, 0.1, cat="mmlu"), rec("b", False, 0.1, cat="mmlu"),
                rec("c", True, 0.1, cat="gsm8k")]
        out = {(x["name"], x["category"]): x["accuracy"] for x in by_category(rows, ["litellm"])}
        self.assertEqual(out, {("litellm", "gsm8k"): 1.0, ("litellm", "mmlu"): 0.5})


if __name__ == "__main__":
    unittest.main()
