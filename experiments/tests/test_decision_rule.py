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
    compute_quality_accuracy,
    compute_consistency_rate,
    compute_error_rate,
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
            "passed": pid in correct_ids,
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
        acc = compute_quality_accuracy(records, "p")
        # 13 dòng tổng (12 + 1 lượt lỗi thêm cho cq_01), 9 đúng -> lượt lỗi vẫn tính vào
        # mẫu số (đúng nguyên tắc D7: lượt lỗi tính là 1 lần lặp, không loại bỏ).
        self.assertAlmostEqual(acc, 9 / 13)

    def test_avg_cost_ignores_other_proxy(self):
        records = make_records("p", CLOSED_QA_IDS, cost=0.02, latency=100)
        records += make_records("q", CLOSED_QA_IDS, cost=99.0, latency=100)
        self.assertAlmostEqual(compute_avg_cost(records, "p"), 0.02)

    def test_avg_cost_excludes_errored_calls(self):
        # Khoa, 2026-10-03: lượt lỗi ghi cost=0.0 (không có usage thật) - nếu tính
        # vào trung bình sẽ làm proxy hay lỗi trông rẻ giả tạo. avg_cost chỉ tính
        # trên lượt status=success.
        records = make_records("p", CLOSED_QA_IDS, cost=0.02, latency=100)  # 12 thành công, 0.02/lượt
        for i in range(3):  # thêm 3 lượt lỗi, cost=0 - không được kéo trung bình xuống
            records.append({
                "proxy_name": "p", "prompt_id": "cq_01", "category": "closed_qa",
                "run_index": 10 + i, "model_selected": None, "cost": 0.0, "latency_ms": 100,
                "response": None, "status": "error",
            })
        self.assertAlmostEqual(compute_avg_cost(records, "p"), 0.02)  # không bị kéo xuống

    def test_error_rate(self):
        records = make_records("p", CLOSED_QA_IDS, cost=0.01, latency=100)  # 12 thành công
        for i in range(4):
            records.append({
                "proxy_name": "p", "prompt_id": "cq_01", "category": "closed_qa",
                "run_index": 10 + i, "model_selected": None, "cost": 0.0, "latency_ms": None,
                "response": None, "status": "error",
            })
        self.assertAlmostEqual(compute_error_rate(records, "p"), 4 / 16)
        self.assertEqual(compute_error_rate(records, "q"), 0.0)  # proxy khong co record nao

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
                             "latency_ms": 100, "response": "Canberra", "status": "success",
                             "passed": True})
        # prompt B: đổi model giữa các lần -> không nhất quán
        for run, model in ((1, "gpt-4o-mini"), (2, "gemini-flash"), (3, "gpt-4o-mini")):
            records.append({"proxy_name": "p", "prompt_id": "cq_02", "category": "closed_qa",
                             "run_index": run, "model_selected": model, "cost": 0.01,
                             "latency_ms": 100, "response": "Natri", "status": "success",
                             "passed": True})
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
                        "passed": True,
                    })
        result = apply_decision_rule(records, ["proxyF", "proxyG"])
        self.assertEqual(compute_avg_cost(records, "proxyF"), compute_avg_cost(records, "proxyG"))
        self.assertEqual(compute_p95_latency(records, "proxyF"), compute_p95_latency(records, "proxyG"))
        self.assertLess(compute_consistency_rate(records, "proxyF"), compute_consistency_rate(records, "proxyG"))
        self.assertEqual(result["selected_proxy"], "proxyG")

    def test_khong_proxy_nao_qua_cong_thi_BAO_CAO_chu_khong_nem_exception(self):
        """Đổi 2026-10-17: trước đây ném ValueError, nên nếu chạy thật mà không proxy nào
        qua 80% thì mất luôn bảng số liệu (gặp ở đợt kiểm 24 lượt). Giờ đó là MỘT KẾT QUẢ:
        no_proxy_passed_gate=True + số liệu đủ CẢ BA proxy + chọn theo luật dự phòng D13."""
        records = (make_records("proxyA", [], cost=0.01, latency=100)          # 0/12 đúng
                   + make_records("proxyB", CLOSED_QA_IDS[:3], cost=0.02, latency=200))  # 3/12
        result = apply_decision_rule(records, ["proxyA", "proxyB"])

        self.assertTrue(result["no_proxy_passed_gate"])
        # proxyA sai het -> chi phi/cau dat khong xac dinh -> D13 chon proxyB
        self.assertEqual(result["selected_proxy"], "proxyB")
        self.assertTrue(result["selected_by_fallback"])
        self.assertEqual(result["candidates_after_qa_filter"], [])
        # So lieu phai co cho CA HAI proxy du ca hai deu bi loai
        self.assertEqual(set(result["pareto_data"]), {"proxyA", "proxyB"})
        for name, row in result["pareto_data"].items():
            self.assertFalse(row["passed_gate"], name)
            self.assertIn("avg_cost", row)
            self.assertIn("p95_latency_ms", row)

    def test_D13_khong_ai_qua_cong_thi_chon_theo_chi_phi_moi_cau_dat(self):
        """D13 (đăng ký trước 2026-10-17): không ai đạt 80% thì xếp theo chi phí/câu đạt.
        Luật này chốt TRƯỚC khi thấy số nên vẫn khách quan."""
        # proxyRe: 3/12 dat, re  -> 12*0.001/3 = 0.004/cau dat
        # proxyDat: 6/12 dat, dat -> 12*0.010/6 = 0.020/cau dat
        records = (make_records("proxyRe", CLOSED_QA_IDS[:3], cost=0.001, latency=100)
                   + make_records("proxyDat", CLOSED_QA_IDS[:6], cost=0.010, latency=100))
        result = apply_decision_rule(records, ["proxyRe", "proxyDat"])

        self.assertTrue(result["no_proxy_passed_gate"])
        self.assertTrue(result["selected_by_fallback"])
        self.assertEqual(result["selected_proxy"], "proxyRe")
        self.assertLess(result["fallback_ranking"]["proxyRe"],
                        result["fallback_ranking"]["proxyDat"])

    def test_D13_proxy_sai_HET_khong_duoc_chon_du_chi_phi_bang_0(self):
        """Bẫy chia cho 0: proxy sai hết thì chi phí/câu đạt KHÔNG xác định, không được
        coi là 0 rồi thành 'rẻ nhất'."""
        records = (make_records("proxySaiHet", [], cost=0.001, latency=100)        # 0/12 dat
                   + make_records("proxyCoDat", CLOSED_QA_IDS[:4], cost=0.010, latency=100))
        result = apply_decision_rule(records, ["proxySaiHet", "proxyCoDat"])

        self.assertTrue(result["no_proxy_passed_gate"])
        self.assertIsNone(result["fallback_ranking"]["proxySaiHet"])
        self.assertEqual(result["selected_proxy"], "proxyCoDat")

    def test_D13_ca_hai_sai_het_thi_khong_chon_ai(self):
        records = (make_records("a", [], cost=0.001, latency=100)
                   + make_records("b", [], cost=0.002, latency=100))
        result = apply_decision_rule(records, ["a", "b"])
        self.assertIsNone(result["selected_proxy"])
        self.assertFalse(result["selected_by_fallback"])

    def test_qua_cong_thi_KHONG_dung_du_phong(self):
        records = make_records("p", CLOSED_QA_IDS, cost=0.01, latency=100)  # 12/12
        result = apply_decision_rule(records, ["p"])
        self.assertEqual(result["selected_proxy"], "p")
        self.assertFalse(result["selected_by_fallback"])
        self.assertFalse(result["no_proxy_passed_gate"])

    def test_pareto_data_co_ca_proxy_bi_loai(self):
        """Phát hiện E của Khoa: trước đây chỉ in số liệu của proxy QUA cổng, nên báo cáo
        không có số của proxy bị loại — không biết nó bị loại vì gì."""
        records = (make_records("proxyPass", CLOSED_QA_IDS, cost=0.02, latency=100)      # 12/12
                   + make_records("proxyFail", CLOSED_QA_IDS[:5], cost=0.001, latency=50))  # 5/12
        result = apply_decision_rule(records, ["proxyPass", "proxyFail"])

        self.assertEqual(result["selected_proxy"], "proxyPass")
        self.assertEqual(set(result["pareto_data"]), {"proxyPass", "proxyFail"})
        self.assertTrue(result["pareto_data"]["proxyPass"]["passed_gate"])
        self.assertFalse(result["pareto_data"]["proxyFail"]["passed_gate"])
        # proxyFail re hon nhung bi loai o buoc 1 - bao cao phai thay duoc dieu do
        self.assertLess(result["pareto_data"]["proxyFail"]["avg_cost"],
                        result["pareto_data"]["proxyPass"]["avg_cost"])

    def test_error_prone_proxy_no_longer_wins_on_cost(self):
        # Tái tạo đúng kịch bản Khoa phát hiện (log-khoa.md, 2026-10-03): proxyJ đắt
        # hơn proxyI 2%/lượt thành công, nhưng lỗi 4/36 lượt. Trước khi sửa,
        # avg_cost tính cả lượt lỗi (cost=0) khiến proxyJ trông RẺ HƠN proxyI dù
        # thực ra đắt hơn - luật sẽ chọn nhầm. Sau khi sửa: phải chọn proxyI (rẻ
        # hơn thật, 100% thành công) chứ không phải proxyJ.
        records = make_records("proxyI", CLOSED_QA_IDS, cost=0.0100, latency=200, run_index=1)
        records += make_records("proxyI", CLOSED_QA_IDS, cost=0.0100, latency=200, run_index=2)
        records += make_records("proxyI", CLOSED_QA_IDS, cost=0.0100, latency=200, run_index=3)
        for run_index in (1, 2, 3):
            n_error = {1: 2, 2: 1, 3: 1}[run_index]  # tổng 4/36 lỗi, rải qua các lần lặp
            correct_ids = CLOSED_QA_IDS[n_error:]
            for pid in CLOSED_QA_IDS:
                if pid in correct_ids:
                    records.append({
                        "proxy_name": "proxyJ", "prompt_id": pid, "category": "closed_qa",
                        "run_index": run_index, "model_selected": "m", "cost": 0.0102,
                        "latency_ms": 200, "response": GOOD_ANSWERS[pid], "status": "success",
                        "passed": True,
                    })
                else:
                    records.append({
                        "proxy_name": "proxyJ", "prompt_id": pid, "category": "closed_qa",
                        "run_index": run_index, "model_selected": None, "cost": 0.0,
                        "latency_ms": None, "response": None, "status": "error",
                    })

        # Trước khi sửa (cost tính cả lượt lỗi), proxyJ sẽ ra "rẻ hơn":
        buggy_avg_cost_j = sum(r["cost"] for r in records if r["proxy_name"] == "proxyJ") / 36
        self.assertLess(buggy_avg_cost_j, 0.0100, "sanity: kịch bản phải tái hiện đúng lỗi cũ")

        self.assertAlmostEqual(compute_avg_cost(records, "proxyJ"), 0.0102)  # chỉ tính 32 lượt thành công
        self.assertAlmostEqual(compute_error_rate(records, "proxyJ"), 4 / 36)
        self.assertEqual(compute_error_rate(records, "proxyI"), 0.0)

        result = apply_decision_rule(records, ["proxyI", "proxyJ"])
        self.assertEqual(result["selected_proxy"], "proxyI")  # rẻ hơn thật + không lỗi

    def test_tie_unresolved_flagged_not_silent(self):
        # Hòa tuyệt đối cả cost/latency/consistency -> không được âm thầm chọn
        # proxy đầu tiên trong list mà không báo (Khoa, 2026-10-03).
        records = []
        for proxy in ("proxyX", "proxyY"):
            for pid in CLOSED_QA_IDS:
                for run in (1, 2, 3):
                    records.append({
                        "proxy_name": proxy, "prompt_id": pid, "category": "closed_qa",
                        "run_index": run, "model_selected": "m", "cost": 0.01,
                        "latency_ms": 200, "response": GOOD_ANSWERS[pid], "status": "success",
                        "passed": True,
                    })
        result = apply_decision_rule(records, ["proxyY", "proxyX"])  # thu tu dau vao dao nguoc
        self.assertTrue(result["tie_unresolved"])
        self.assertEqual(result["tied_candidates"], ["proxyX", "proxyY"])
        self.assertEqual(result["selected_proxy"], "proxyX")  # tie-break: alphabet, khong theo thu tu input


if __name__ == "__main__":
    unittest.main()
