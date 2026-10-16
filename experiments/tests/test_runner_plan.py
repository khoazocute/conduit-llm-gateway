"""Test chọn item (--sets/--per-set) và chạy tiếp (--resume) của runner.

Không gọi API, không cần backend. Hai cơ chế này bảo vệ tiền thật:
  - select_prompts: gõ sai tên bộ thì phải nổ, không âm thầm chạy sai bộ
  - plan_runs: đợt chạy bị dứt giữa chừng thì chạy tiếp, KHÔNG trả tiền hai lần
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_experiment import load_prompts, plan_runs, select_prompts  # noqa: E402

PROMPTS = load_prompts()


class SelectPrompts(unittest.TestCase):
    def test_khong_loc_thi_lay_het_40_item(self):
        self.assertEqual(len(select_prompts(PROMPTS, "", 0)), 40)

    def test_chia_doi_theo_bo_dung_20_20(self):
        a = select_prompts(PROMPTS, "mmlu,gsm8k", 0)
        b = select_prompts(PROMPTS, "humaneval,ifeval", 0)
        self.assertEqual(len(a), 20)
        self.assertEqual(len(b), 20)
        # Hai nua KHONG duoc trung item nao - neu trung thi co item chay 6 lan, item khac 0 lan
        self.assertEqual(set(p["id"] for p in a) & set(p["id"] for p in b), set())
        self.assertEqual(len(a) + len(b), 40)

    def test_per_set_1_cho_dry_run(self):
        ps = select_prompts(PROMPTS, "", 1)
        self.assertEqual(len(ps), 4)
        self.assertEqual({p["category"] for p in ps}, {"mmlu", "gsm8k", "humaneval", "ifeval"})

    def test_go_sai_ten_bo_thi_NO_chu_khong_chay_sai(self):
        with self.assertRaises(SystemExit):
            select_prompts(PROMPTS, "mmlu,humanevl", 0)   # thieu chu 'a'
        with self.assertRaises(SystemExit):
            select_prompts(PROMPTS, "MMLU", 0)            # sai hoa/thuong


class PlanRuns(unittest.TestCase):
    ITEMS = [{"id": "a", "category": "mmlu"}, {"id": "b", "category": "mmlu"}]

    def _file(self, records):
        f = Path(tempfile.mkdtemp()) / "prev.json"
        f.write_text(json.dumps(records), encoding="utf-8")
        return f

    def test_khong_resume_thi_chay_het(self):
        planned, skipped = plan_runs(self.ITEMS, 3, None)
        self.assertEqual(len(planned), 6)
        self.assertEqual(skipped, 0)

    def test_resume_bo_qua_dung_nhung_luot_DA_THANH_CONG(self):
        prev = self._file([
            {"prompt_id": "a", "run_index": 1, "status": "success"},
            {"prompt_id": "a", "run_index": 2, "status": "success"},
        ])
        planned, skipped = plan_runs(self.ITEMS, 3, prev)
        self.assertEqual(skipped, 2)
        self.assertEqual(len(planned), 4)
        self.assertNotIn(("a", 1), [(p["id"], i) for p, i in planned])
        self.assertIn(("a", 3), [(p["id"], i) for p, i in planned])

    def test_luot_LOI_phai_chay_lai_chu_khong_bo_qua(self):
        """Lượt lỗi không tốn tiền và mỗi item cần đủ 3 lần lặp (D7) -> phải chạy lại."""
        prev = self._file([
            {"prompt_id": "a", "run_index": 1, "status": "error"},
            {"prompt_id": "a", "run_index": 2, "status": "success"},
        ])
        planned, skipped = plan_runs(self.ITEMS, 3, prev)
        self.assertEqual(skipped, 1)
        self.assertIn(("a", 1), [(p["id"], i) for p, i in planned])

    def test_resume_tren_file_da_xong_thi_khong_chay_luot_nao(self):
        prev = self._file([{"prompt_id": pid, "run_index": i, "status": "success"}
                           for pid in ("a", "b") for i in (1, 2, 3)])
        planned, skipped = plan_runs(self.ITEMS, 3, prev)
        self.assertEqual(skipped, 6)
        self.assertEqual(planned, [], "file đã xong thì không được gọi thêm lượt nào")


if __name__ == "__main__":
    unittest.main()
