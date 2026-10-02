"""Kiểm chứng build_grading_sheets.py bằng dữ liệu giả — không cần chờ có kết quả
thí nghiệm thật. Chạy: python -m unittest discover -s experiments/tests -v
"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_grading_sheets import CSV_FIELDS, DOUBLE_GRADE_FRACTION, build_sheets  # noqa: E402


def make_record(proxy, prompt_id, category, run_index=1, status="success", response="output text"):
    return {
        "proxy_name": proxy, "prompt_id": prompt_id, "category": category,
        "run_index": run_index, "model_selected": "gpt-4o-mini", "cost": 0.001,
        "latency_ms": 100.0, "response": response, "status": status,
    }


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fake_records(n_code=6, n_open=12, n_proxies=3, n_runs=3, error_every=10):
    """Mô phỏng ~ cấu trúc thật: n_code + n_open prompt, mỗi prompt x n_proxies x
    n_runs lượt, thỉnh thoảng chèn 1 lượt lỗi (error_every) để test auto-0-điểm."""
    records = []
    i = 0
    for cat, n in (("code", n_code), ("open_ended", n_open)):
        for p in range(n):
            for proxy in [f"proxy{k}" for k in range(n_proxies)]:
                for run in range(1, n_runs + 1):
                    i += 1
                    status = "error" if i % error_every == 0 else "success"
                    records.append(make_record(proxy, f"{cat}_{p:02d}", cat, run, status,
                                                response=f"{cat} answer {p}-{proxy}-{run}"))
    # Xen thêm vài dòng closed_qa để test bị loại khỏi bảng chấm.
    records.append(make_record("proxy0", "cq_01", "closed_qa", 1, "success", "Canberra"))
    return records


class BuildGradingSheets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_closed_qa_excluded(self):
        records = fake_records()
        stats = build_sheets(records, out_dir=self.out_dir)
        hung = _read_csv(self.out_dir / "sheet-hung.csv")
        khoa = _read_csv(self.out_dir / "sheet-khoa.csv")
        all_prompt_ids = {r["prompt_id"] for r in hung + khoa}
        self.assertNotIn("cq_01", all_prompt_ids)
        self.assertTrue(all(pid.startswith(("code_", "open_ended_")) for pid in all_prompt_ids))

    def test_errored_records_not_in_sheets_but_in_answer_key(self):
        records = fake_records(error_every=5)
        n_errored_expected = sum(1 for r in fake_records(error_every=5) if r["status"] == "error")
        self.assertGreater(n_errored_expected, 0, "sanity: fixture phải có ít nhất 1 lượt lỗi")

        stats = build_sheets(records, out_dir=self.out_dir)
        self.assertEqual(stats["errored"], n_errored_expected)

        hung = _read_csv(self.out_dir / "sheet-hung.csv")
        khoa = _read_csv(self.out_dir / "sheet-khoa.csv")
        for row in hung + khoa:
            self.assertNotEqual(row["answer_text"], "")  # loi khong lot vao day

        import json
        answer_key = json.loads((self.out_dir / "answer-key.json").read_text(encoding="utf-8"))
        error_entries = [v for k, v in answer_key.items() if k.startswith("error-")]
        self.assertEqual(len(error_entries), n_errored_expected)

    def test_no_proxy_or_model_column_in_sheets(self):
        build_sheets(fake_records(), out_dir=self.out_dir)
        with (self.out_dir / "sheet-hung.csv").open(encoding="utf-8") as f:
            header = next(csv.reader(f))
        self.assertEqual(header, CSV_FIELDS)
        self.assertNotIn("proxy_name", header)
        self.assertNotIn("model_selected", header)
        self.assertNotIn("latency_ms", header)
        self.assertNotIn("cost", header)

    def test_double_grade_fraction_matches_d6(self):
        records = fake_records(n_code=6, n_open=12, n_proxies=3, n_runs=3, error_every=10_000)  # khong loi
        stats = build_sheets(records, out_dir=self.out_dir)
        expected_total = 6 * 3 * 3 + 12 * 3 * 3  # 162, dung so trong docs/eval-prompts.md
        self.assertEqual(stats["total_gradeable"], expected_total)
        expected_double = round(expected_total * DOUBLE_GRADE_FRACTION)
        self.assertEqual(stats["double_graded"], expected_double)
        # ~49 theo docs/eval-prompts.md ghi nhận sẵn
        self.assertEqual(expected_double, 49)

    def test_double_graded_outputs_appear_in_both_sheets_identically_scored_blank(self):
        records = fake_records(error_every=10_000)
        build_sheets(records, out_dir=self.out_dir)
        hung = {r["output_id"]: r for r in _read_csv(self.out_dir / "sheet-hung.csv")}
        khoa = {r["output_id"]: r for r in _read_csv(self.out_dir / "sheet-khoa.csv")}
        shared_ids = set(hung) & set(khoa)
        self.assertGreater(len(shared_ids), 0)
        for oid in shared_ids:
            self.assertEqual(hung[oid]["answer_text"], khoa[oid]["answer_text"])
            self.assertEqual(hung[oid]["prompt_id"], khoa[oid]["prompt_id"])
            # diem con trong (chua cham), grader ghi dung ten cua tung file
            self.assertEqual(hung[oid]["on_task"], "")
            self.assertEqual(hung[oid]["grader"], "hung")
            self.assertEqual(khoa[oid]["grader"], "khoa")

    def test_reproducible_with_fixed_seed(self):
        records = fake_records()
        build_sheets(records, out_dir=self.out_dir)
        first = (self.out_dir / "answer-key.json").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp2:
            build_sheets(records, out_dir=Path(tmp2))
            second = (Path(tmp2) / "answer-key.json").read_text(encoding="utf-8")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
