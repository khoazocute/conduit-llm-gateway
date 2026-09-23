"""Test luật chấm closed-QA: mỗi câu ≥2 đáp án đúng + ≥2 đáp án sai (gồm cả bẫy).
Chạy: python -m unittest discover -s experiments/tests -v  (từ thư mục gốc repo)
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "prompts"))

from grading import is_correct  # noqa: E402
from validate_prompts import validate  # noqa: E402

PROMPTS = json.loads((ROOT / "prompts" / "prompts.json").read_text(encoding="utf-8"))
CLOSED_QA = {p["id"]: p for p in PROMPTS["closed_qa"]}

# id -> (câu trả lời ĐÚNG, câu trả lời SAI). Sai gồm các bẫy: số chứa đáp án (15 vs 5),
# từ chứa đáp án (chính vs Chi), phủ định (Không có), đáp án của phương án đối lập.
SAMPLES = {
    "cq_01": (
        ["Canberra", "Thủ đô của Úc là **Canberra**, không phải Sydney."],
        ["Sydney", "Melbourne là thủ đô của Úc."],
    ),
    "cq_02": (
        ["Natri", "Na là ký hiệu của Natri (Sodium)."],
        ["Kali (K)", "Đó là Potassium."],
    ),
    "cq_03": (
        ["Nguyễn Du", "Truyện Kiều do đại thi hào **Nguyễn Du** sáng tác."],
        ["Nguyễn Trãi", "Nguyễn Dữ là tác giả."],
    ),
    "cq_04": (
        ["Sao Thủy", "Sao Thuỷ (Mercury) là hành tinh gần Mặt Trời nhất."],
        ["Sao Kim", "Hành tinh gần nhất là Venus."],
    ),
    "cq_05": (
        ["408", "17 × 24 = **408**"],
        ["418", "17 × 24 = 4080"],
    ),
    "cq_06": (
        ["84", "Diện tích = 12 × 7 = 84 cm²"],
        ["38 cm² ", "Diện tích là 184 cm²"],
    ),
    "cq_07": (
        ["x = 5", "3x = 15 nên **x = 5**"],
        ["x = 15", "x = 55"],
    ),
    "cq_08": (
        ["36", "15% của 240 là 36."],
        ["3.6", "Kết quả là 360."],
    ),
    "cq_09": (
        ["Có", "**Có**, Tom là động vật.", "Trả lời: Có"],
        ["Không", "Không có cơ sở để kết luận.", "Có thể, nhưng chưa chắc chắn."],
    ),
    "cq_10": (
        ["Chi", "Người thấp nhất là **Chi**.", "Chi là người thấp nhất trong ba người."],
        ["Bình", "Bình cao hơn Chi. Bình thấp nhất.", "Chính là An."],
    ),
    "cq_11": (
        ["(b)", "b", "**(b)** Cần cân nhắc khả năng nhìn nhầm.", "Đáp án: (b)"],
        ["(a)", "a", "(a) Chắc chắn taxi màu xanh."],
    ),
    "cq_12": (
        ["32", "Số tiếp theo là **32** (nhân đôi mỗi lần)."],
        ["30", "Số tiếp theo là 320."],
    ),
}


class GradingRules(unittest.TestCase):
    def test_every_closed_qa_has_samples(self):
        self.assertEqual(set(SAMPLES), set(CLOSED_QA))
        for pid, (good, bad) in SAMPLES.items():
            self.assertGreaterEqual(len(good), 2, pid)
            self.assertGreaterEqual(len(bad), 2, pid)

    def test_correct_answers_pass_and_wrong_fail(self):
        for pid, (good, bad) in SAMPLES.items():
            item = CLOSED_QA[pid]
            for resp in good:
                with self.subTest(pid=pid, kind="đúng", resp=resp):
                    self.assertTrue(is_correct(resp, item["expected_answer"], item["match_type"]))
            for resp in bad:
                with self.subTest(pid=pid, kind="sai", resp=resp):
                    self.assertFalse(is_correct(resp, item["expected_answer"], item["match_type"]))


class MatchTypes(unittest.TestCase):
    def test_exact_ignores_case_and_edge_punctuation(self):
        self.assertTrue(is_correct("**Chi.**", "chi", "exact"))
        self.assertFalse(is_correct("Chi là người thấp nhất", "chi", "exact"))

    def test_contains(self):
        self.assertTrue(is_correct("Là CANBERRA đó", "canberra", "contains"))

    def test_unknown_type_raises(self):
        with self.assertRaises(ValueError):
            is_correct("x", "x", "fuzzy")


class PromptsFile(unittest.TestCase):
    def test_schema_valid(self):
        self.assertEqual(validate(PROMPTS), [])


if __name__ == "__main__":
    unittest.main()
