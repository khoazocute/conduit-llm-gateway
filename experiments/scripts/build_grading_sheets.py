"""
Xuất bảng chấm mù cho 18 câu code+mở (D4/D6, CLAUDE.md mục 2) từ kết quả thô của
run_experiment.py. Script tự test được bằng dữ liệu giả (xem
experiments/tests/test_build_grading_sheets.py) — không cần chờ có dữ liệu thật mới
viết/kiểm tra được.

Input: 1 hoặc nhiều file experiments/results/run_*.json (mỗi file 1 proxy).
Output (experiments/results/grading/):
  - answer-key.json   map output_id -> prompt_id/proxy_name/run_index/model_selected.
    KHÔNG đưa file này cho người chấm trước khi chấm xong — làm lộ proxy_name thì
    mất tính "chấm mù" (docs/grading-rubric.md mục "Nguyên tắc chấm mù").
  - sheet-hung.csv / sheet-khoa.csv   bảng chấm của từng người, đúng cột theo
    docs/grading-rubric.md mục 4 (output_id, prompt_id, answer_text, 3 cột điểm,
    total, grader — KHÔNG có proxy_name/model/latency/cost).

Quy tắc:
  - Chỉ đưa vào bảng chấm: category in {code, open_ended} và status == "success".
    Lượt lỗi (status != success) không có nội dung để chấm — tự 0 điểm cả 3 tiêu
    chí theo D7, không đưa cho người chấm, chỉ ghi lại trong answer-key.json để
    không mất dấu vết (mục "Còn lượt lỗi" khi tính % agreement/thống kê).
  - Xáo trộn thứ tự bằng seed cố định (tái lập được, nhưng người chấm không đoán
    được proxy nào qua vị trí xuất hiện).
  - D6 (đã chốt 2026-09-23, docs/roadmap.md mục 4): 30% mẫu (theo lượt output, không
    theo prompt) do CẢ 2 người chấm độc lập — xuất hiện ở cả 2 file. 70% còn lại
    chia đôi, xen kẽ Hùng/Khoa.

Cách dùng:
  python experiments/scripts/build_grading_sheets.py experiments/results/run_*.json
"""

import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
GRADING_DIR = RESULTS_DIR / "grading"
DOUBLE_GRADE_FRACTION = 0.30  # D6
RANDOM_SEED = 42  # co dinh de tai lap duoc cung 1 cach xao/chia mau
CSV_FIELDS = ["output_id", "prompt_id", "answer_text", "on_task", "length_ok", "error_free", "total", "grader"]


def load_records(paths: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for p in paths:
        records.extend(json.loads(Path(p).read_text(encoding="utf-8")))
    return records


def _gradeable(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in records if r.get("category") in ("code", "open_ended")]


def _assign_graders(output_ids: list[str]) -> dict[str, list[str]]:
    """output_id -> danh sách người chấm (1 hoặc 2 tên). 30% đầu (sau khi đã xáo
    trộn ngẫu nhiên) là mẫu chấm kép; phần còn lại xen kẽ hung/khoa."""
    n_double = round(len(output_ids) * DOUBLE_GRADE_FRACTION)
    assignment: dict[str, list[str]] = {}
    for i, oid in enumerate(output_ids):
        if i < n_double:
            assignment[oid] = ["hung", "khoa"]
        else:
            assignment[oid] = ["hung"] if (i - n_double) % 2 == 0 else ["khoa"]
    return assignment


def build_sheets(records: list[dict[str, Any]], out_dir: Path = GRADING_DIR) -> dict[str, Any]:
    eligible = _gradeable(records)
    success = [r for r in eligible if r.get("status") == "success"]
    errored = [r for r in eligible if r.get("status") != "success"]

    rng = random.Random(RANDOM_SEED)
    shuffled = success[:]
    rng.shuffle(shuffled)
    output_ids = [f"o-{i + 1:04d}" for i in range(len(shuffled))]
    assignment = _assign_graders(output_ids)

    hung_rows: list[dict[str, Any]] = []
    khoa_rows: list[dict[str, Any]] = []
    answer_key: dict[str, Any] = {}

    for oid, record in zip(output_ids, shuffled):
        answer_key[oid] = {
            "prompt_id": record["prompt_id"],
            "proxy_name": record["proxy_name"],
            "run_index": record.get("run_index"),
            "model_selected": record.get("model_selected"),
            "graders": assignment[oid],
        }
        row = {
            "output_id": oid,
            "prompt_id": record["prompt_id"],
            "answer_text": (record.get("response") or "").replace("\r\n", "\n"),
            "on_task": "", "length_ok": "", "error_free": "", "total": "",
        }
        for grader in assignment[oid]:
            (hung_rows if grader == "hung" else khoa_rows).append({**row, "grader": grader})

    for record in errored:
        key = f"error-{record['proxy_name']}-{record['prompt_id']}-{record.get('run_index')}"
        answer_key[key] = {**{k: record.get(k) for k in ("prompt_id", "proxy_name", "run_index", "category", "status")},
                            "auto_score_reason": "loi (status != success) -> 0 diem ca 3 tieu chi, khong dua nguoi cham (D7)"}

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "sheet-hung.csv", hung_rows)
    _write_csv(out_dir / "sheet-khoa.csv", khoa_rows)
    (out_dir / "answer-key.json").write_text(
        json.dumps(answer_key, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "total_gradeable": len(shuffled),
        "double_graded": sum(1 for g in assignment.values() if len(g) == 2),
        "errored": len(errored),
        "hung_rows": len(hung_rows),
        "khoa_rows": len(khoa_rows),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_grading_sheets.py <result1.json> [result2.json ...]")
        sys.exit(1)
    stats = build_sheets(load_records(sys.argv[1:]))
    print(f"{stats['total_gradeable']} output cần chấm tay ({stats['errored']} lượt lỗi tự động 0 điểm, không đưa vào sheet)")
    print(f"Chấm kép (D6, {DOUBLE_GRADE_FRACTION:.0%}): {stats['double_graded']} output, cả 2 người cùng chấm")
    print(f"Hùng chấm: {stats['hung_rows']} dòng | Khoa chấm: {stats['khoa_rows']} dòng")
    print(f"Ghi vào {GRADING_DIR}/")
