"""Test 4 bộ chấm tự động (H7). Mỗi metric có ≥2 ca ĐÚNG + ≥2 ca SAI, gồm cả bẫy.
Không gọi API, không tốn tiền. HumanEval có chạy code thật trong subprocess.

Chạy: PYTHONIOENCODING=utf-8 python -m unittest discover -s experiments/tests -v
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from graders import (  # noqa: E402
    extract_code,
    extract_last_number,
    extract_mmlu_letter,
    grade,
    grade_gsm8k,
    grade_humaneval,
    grade_ifeval,
    grade_mmlu,
)

PROMPTS = json.loads((ROOT / "prompts" / "prompts.json").read_text(encoding="utf-8"))


class MmluGrader(unittest.TestCase):
    ITEM = {"id": "t", "metric": "accuracy_letter", "expected_answer": "B"}

    def test_dung(self):
        for resp in ("B", "  b  ", "B. Martin Luther", "The answer is B.",
                     "Answer: (B)", "**B**"):
            with self.subTest(resp=resp):
                self.assertTrue(grade_mmlu(resp, self.ITEM).passed, resp)

    def test_sai(self):
        for resp in ("A", "C. Luther Vandross", "The answer is D", "", None,
                     "Tôi không biết"):
            with self.subTest(resp=resp):
                self.assertFalse(grade_mmlu(resp, self.ITEM).passed, resp)

    def test_bay_chu_cai_trong_tu(self):
        """'Choice A is wrong, B is right' -> phải ra B, không phải A."""
        self.assertEqual(extract_mmlu_letter("The answer is B, not A."), "B")

    def test_cau_tra_loi_bi_cat_giua_lap_luan_KHONG_duoc_cham_dat(self):
        """Lỗi chấm ĐẠT OAN gặp ở dry-run 16/10: claude-haiku viết 1400+ ký tự lập luận rồi
        bị cắt ở max_tokens, CHƯA HỀ đưa ra đáp án. Text đầy `A[i]` / `Array A` (tên biến
        trong đề về cache) nên pattern cũ `([ABCD])` bắt ra 'A' và trùng đáp án đúng
        -> passed=True oan, đẩy Bifrost từ 75% lên 92% giả tạo."""
        truncated = (
            "I need to analyze the cache behavior for this loop with a write-back policy.\n\n"
            "**Cache Parameters:**\n- Size: 2K bytes = 2048 bytes\n- Block size: 8 bytes\n"
            "Array A occupies 256 blocks, and each write to A[i] evicts the block holding "
            "B data, so A[i] misses while B[i] hits. Actually, let me")
        self.assertIsNone(extract_mmlu_letter(truncated),
                          "câu trả lời bị cắt, không có đáp án -> phải trả None")
        item = {"id": "t", "metric": "accuracy_letter", "expected_answer": "A"}
        self.assertFalse(grade_mmlu(truncated, item).passed,
                         "không có đáp án thì phải tính là KHÔNG đạt")

    def test_mao_tu_a_KHONG_duoc_doc_thanh_dap_an_A(self):
        """Khoa phát hiện khi review Phase 3 (19/10): "The answer is a bit tricky" bị đọc
        thành đáp án A vì chữ "a" mạo từ khớp pattern. Chỉ 'a' gây nhầm — 'b'/'c'/'d'
        thường không phải từ tiếng Anh nên vẫn nhận được."""
        for text in ("The answer is a bit tricky.",
                     "Well, the answer is a little complicated.",
                     "The answer is a reasonable guess",
                     "Honestly the answer is a toss-up"):
            with self.subTest(text=text):
                self.assertIsNone(extract_mmlu_letter(text), text)

    def test_sua_mao_tu_KHONG_lam_cham_truot_oan_chieu_nguoc(self):
        """Sửa thành 'chỉ nhận chữ in hoa' sẽ chấm trượt oan các ca hợp lệ này."""
        for text, want in (("I think the answer is b", "B"),
                           ("the answer is (a)", "A"),       # (a) la nhan lua chon
                           ("  a  ", "A"),                    # ca response chi 1 chu cai
                           ("The answer is A.", "A"),
                           ("Final answer: A", "A")):
            with self.subTest(text=text):
                self.assertEqual(extract_mmlu_letter(text), want, text)

    def test_lay_dap_an_CHOT_o_cuoi_khong_phai_cai_dau(self):
        """Model lập luận rồi mới chốt — phải lấy đáp án cuối."""
        self.assertEqual(extract_mmlu_letter(
            "Option A looks plausible.\nBut B fits better.\n\nFinal answer: B"), "B")

    def test_khong_trich_duoc(self):
        self.assertIsNone(extract_mmlu_letter("không có chữ cái lựa chọn nào"))


class Gsm8kGrader(unittest.TestCase):
    ITEM = {"id": "t", "metric": "exact_match_number", "expected_answer": "63"}

    def test_dung(self):
        for resp in ("63", "The answer is 63", "18/2 = 9, 9*7 = 63.",
                     "His brother eats 63 pretzels.", "63.0", "1,063 - 1000 = 63"):
            with self.subTest(resp=resp):
                self.assertTrue(grade_gsm8k(resp, self.ITEM).passed, resp)

    def test_sai(self):
        for resp in ("64", "The answer is 126", "", None, "sixty-three"):
            with self.subTest(resp=resp):
                self.assertFalse(grade_gsm8k(resp, self.ITEM).passed, resp)

    def test_lay_so_cuoi_cung_khong_phai_so_dau(self):
        """Bẫy: các bước trung gian có số khác — chỉ số CUỐI mới là đáp án."""
        self.assertEqual(extract_last_number("18 a day, half is 9, times 7 days = 63"), "63")

    def test_bo_dau_phay_hang_nghin(self):
        self.assertEqual(extract_last_number("tổng là 1,234"), "1234")


class HumanEvalGrader(unittest.TestCase):
    ITEM = {
        "id": "t", "metric": "pass_at_1", "entry_point": "add_one",
        "signature_prompt": "def add_one(x: int) -> int:\n    \"\"\"Return x + 1.\"\"\"\n",
        "test": "def check(candidate):\n    assert candidate(1) == 2\n    assert candidate(-5) == -4\n",
    }

    def test_dung_code_tran(self):
        r = grade_humaneval("def add_one(x: int) -> int:\n    return x + 1\n", self.ITEM)
        self.assertTrue(r.passed, r.detail)

    def test_dung_code_trong_khoi_markdown(self):
        resp = "Here you go:\n\n```python\ndef add_one(x: int) -> int:\n    return x + 1\n```\n"
        self.assertTrue(grade_humaneval(resp, self.ITEM).passed)

    def test_dung_khi_model_chi_tra_ve_than_ham(self):
        """Model chỉ viết thân hàm -> phải ghép với signature_prompt rồi mới chạy."""
        self.assertTrue(grade_humaneval("    return x + 1\n", self.ITEM).passed)

    def test_dung_khi_model_viet_lai_ham_nhung_bo_dong_import_cua_de(self):
        """Lỗi gặp ở dry-run 16/10 (humaneval_01): đề có `from typing import List`, model viết
        lại cả hàm nhưng bỏ dòng import -> trước đây NameError dù lời giải đúng. Harness chính
        thức chạy đề + câu trả lời nên phải chấm đạt."""
        item = {
            "id": "t2", "metric": "pass_at_1", "entry_point": "first",
            "signature_prompt": "from typing import List\n\n\ndef first(xs: List[int]) -> int:\n"
                                "    \"\"\"Return the first element.\"\"\"\n",
            "test": "def check(candidate):\n    assert candidate([3, 4]) == 3\n",
        }
        resp = "```python\ndef first(xs: List[int]) -> int:\n    return xs[0]\n```"
        self.assertTrue(grade_humaneval(resp, item).passed)

    def test_sai_logic(self):
        r = grade_humaneval("def add_one(x: int) -> int:\n    return x + 2\n", self.ITEM)
        self.assertFalse(r.passed)
        self.assertEqual(r.detail["returncode"], 1)

    def test_sai_cu_phap(self):
        self.assertFalse(grade_humaneval("def add_one(x:\n    return", self.ITEM).passed)

    def test_sai_khong_co_code(self):
        r = grade_humaneval("Tôi không thể giúp việc này.", self.ITEM)
        self.assertFalse(r.passed)

    def test_rong(self):
        self.assertFalse(grade_humaneval("", self.ITEM).passed)
        self.assertFalse(grade_humaneval(None, self.ITEM).passed)

    def test_vong_lap_vo_han_bi_timeout_chu_khong_treo(self):
        from graders import HUMANEVAL_TIMEOUT
        item = dict(self.ITEM)
        r = grade_humaneval("def add_one(x):\n    while True:\n        pass\n", item)
        self.assertFalse(r.passed)
        self.assertIn("timeout", r.detail.get("reason", ""))
        self.assertGreater(HUMANEVAL_TIMEOUT, 0)

    def test_uu_tien_khoi_co_dung_ham_can_viet(self):
        resp = ("```python\ndef helper():\n    pass\n```\n"
                "```python\ndef add_one(x):\n    return x + 1\n```")
        self.assertIn("add_one", extract_code(resp, "add_one"))


class IfEvalGrader(unittest.TestCase):
    QUOTE_ITEM = {
        "id": "t", "metric": "ifeval_strict_prompt",
        "instruction_id_list": ["startend:quotation"], "kwargs": [{}],
    }

    def test_dung(self):
        for resp in ('"Laugh here nightly."', '"Nhiều câu. Vẫn trong ngoặc kép."'):
            with self.subTest(resp=resp):
                self.assertTrue(grade_ifeval(resp, self.QUOTE_ITEM).passed, resp)

    def test_sai(self):
        for resp in ("Laugh here nightly.", 'Chỉ "một phần" trong ngoặc kép.', "", None):
            with self.subTest(resp=resp):
                self.assertFalse(grade_ifeval(resp, self.QUOTE_ITEM).passed, resp)

    def test_nhieu_rang_buoc_phai_theo_HET_moi_dat(self):
        """prompt-level strict: thiếu 1 ràng buộc là không đạt, nhưng score vẫn 0.5."""
        item = {
            "id": "t2", "metric": "ifeval_strict_prompt",
            "instruction_id_list": ["startend:quotation", "keywords:existence"],
            "kwargs": [{}, {"keywords": ["banana"]}],
        }
        r = grade_ifeval('"Không có từ khoá cần thiết."', item)
        self.assertFalse(r.passed)
        self.assertAlmostEqual(r.score, 0.5)

        ok = grade_ifeval('"This mentions banana."', item)
        self.assertTrue(ok.passed)
        self.assertAlmostEqual(ok.score, 1.0)

    def test_moi_verifier_cua_bo_de_that_deu_build_va_chay_duoc(self):
        """Không để tới lúc chạy 360 lượt mới phát hiện thiếu verifier."""
        for item in PROMPTS["ifeval"]:
            with self.subTest(item=item["id"]):
                r = grade_ifeval("Một câu trả lời bất kỳ để thử verifier.", item)
                errs = [p for p in r.detail["per_instruction"] if "error" in p]
                self.assertEqual(errs, [], f"{item['id']}: verifier lỗi {errs}")
                self.assertEqual(r.detail["total"], len(item["instruction_id_list"]))


class Dispatch(unittest.TestCase):
    def test_dispatch_dung_theo_metric(self):
        self.assertTrue(grade("B", {"id": "t", "metric": "accuracy_letter",
                                    "expected_answer": "B"}).passed)
        self.assertTrue(grade("63", {"id": "t", "metric": "exact_match_number",
                                     "expected_answer": "63"}).passed)

    def test_metric_la_thi_no_chu_khong_am_tham_cho_0(self):
        with self.assertRaises(ValueError):
            grade("x", {"id": "t", "metric": "metric_khong_ton_tai"})

    def test_moi_item_trong_bo_de_deu_co_grader(self):
        from graders import GRADERS
        for group, items in PROMPTS.items():
            for it in items:
                with self.subTest(item=it["id"]):
                    self.assertIn(it["metric"], GRADERS, f"{it['id']} ({group})")


if __name__ == "__main__":
    unittest.main()
