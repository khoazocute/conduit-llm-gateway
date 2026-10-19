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

from run_experiment import (  # noqa: E402
    load_prompts,
    plan_runs,
    select_prompts,
    skip_ran_items,
)

PROMPTS = load_prompts()
# Suy tu prompts.json thay vi ghi cung 40 - cho mo rong co mau (D14: 40 -> 80) khong lam
# test bao sai oan, nhung van kiem duoc cac TY LE quan trong (chia doi phai bang nhau,
# hai nua khong trung item nao).
N_TOTAL = len(PROMPTS)
N_HALF = N_TOTAL // 2


class SkipRanItems(unittest.TestCase):
    """--skip-ran (D14): dot mo rong chi chay item MOI, khong tra tien lai cho item cu."""

    def _file(self, tmp, ids):
        f = Path(tmp) / "ran.json"
        f.write_text(json.dumps([{"prompt_id": i, "run_index": 1} for i in ids]),
                     encoding="utf-8")
        return str(f)

    def test_bo_dung_item_da_chay(self):
        ps = select_prompts(PROMPTS, "mmlu", 0)
        with tempfile.TemporaryDirectory() as tmp:
            ran = [p["id"] for p in ps[:3]]
            kept = skip_ran_items(ps, [self._file(tmp, ran)])
        self.assertEqual([p["id"] for p in kept], [p["id"] for p in ps[3:]])

    def test_go_sai_duong_dan_thi_NO_chu_khong_chay_lai_het(self):
        """Neu am tham chay lai thi tra tien hai lan cho TOAN BO bo de."""
        with self.assertRaises(SystemExit):
            skip_ran_items(PROMPTS, ["khong/ton/tai/abc.json"])

    def test_khong_truyen_file_thi_NO(self):
        with self.assertRaises(SystemExit):
            skip_ran_items(PROMPTS, [])

    def test_moi_item_da_chay_het_thi_NO(self):
        ps = select_prompts(PROMPTS, "mmlu", 0)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                skip_ran_items(ps, [self._file(tmp, [p["id"] for p in ps])])


class SelectPrompts(unittest.TestCase):
    def test_khong_loc_thi_lay_het_moi_item(self):
        self.assertEqual(len(select_prompts(PROMPTS, "", 0)), N_TOTAL)

    def test_chia_doi_theo_bo_dung_mot_nua_moi_nguoi(self):
        a = select_prompts(PROMPTS, "mmlu,gsm8k", 0)
        b = select_prompts(PROMPTS, "humaneval,ifeval", 0)
        self.assertEqual(len(a), N_HALF)
        self.assertEqual(len(b), N_HALF)
        # Hai nua KHONG duoc trung item nao - neu trung thi co item chay 6 lan, item khac 0 lan
        self.assertEqual(set(p["id"] for p in a) & set(p["id"] for p in b), set())
        self.assertEqual(len(a) + len(b), N_TOTAL)

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
