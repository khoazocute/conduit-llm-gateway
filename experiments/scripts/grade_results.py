"""Chấm offline file kết quả thô của runner (H8, D10).

Runner chỉ thu output (`passed: null`); script này chấm theo metric chuẩn của từng bộ rồi
ghi `passed` / `score` / `grade_detail` vào CHÍNH file kết quả, và (tuỳ chọn) nạp
`routing_decisions.response_quality_score` vào DB.

Chạy:
  PYTHONIOENCODING=utf-8 python experiments/scripts/grade_results.py experiments/results/run_*.json
  ... --skip pass_at_1     # bỏ 1 metric (phương án lùi: HumanEval chấm sau)
  ... --db                 # nạp luôn response_quality_score vào routing_decisions
  ... --dry-run            # chỉ in thống kê, không ghi file

An toàn khi chạy lại: chấm lại từ `response` đã lưu, không gọi API, không tốn tiền.
"""
import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = SCRIPT_DIR.parent
PROMPTS_FILE = EXPERIMENTS_DIR / "prompts" / "prompts.json"

sys.path.insert(0, str(EXPERIMENTS_DIR / "analysis"))
from graders import GRADERS, grade  # noqa: E402

PG = ["docker", "exec", "-i", "conduit-postgres", "psql", "-U", "conduit", "-d", "conduit", "-tAc"]


def load_items() -> dict[str, dict[str, Any]]:
    """id -> item (kèm category), gộp cả 4 nhóm."""
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for category, items in data.items():
        for it in items:
            out[it["id"]] = {**it, "category": category}
    return out


def record_quality_score(message_id: str, score: float) -> None:
    """routing_decisions.response_quality_score, thang 0-1 chung cho mọi bộ."""
    uuid.UUID(message_id)  # message_id đi thẳng vào SQL - chặn mọi thứ không phải UUID
    sql = (f"UPDATE routing_decisions SET response_quality_score = {score} "
           f"WHERE message_id = '{message_id}';")
    subprocess.run([*PG, sql], check=True, capture_output=True, text=True)


def grade_file(path: Path, items: dict[str, dict[str, Any]], skip: set[str],
               write_db: bool, dry_run: bool) -> dict[str, Any]:
    records = json.loads(path.read_text(encoding="utf-8"))
    stats = {"total": len(records), "graded": 0, "passed": 0, "skipped_metric": 0,
             "error_status": 0, "no_item": 0, "db_written": 0}

    for r in records:
        pid = r.get("prompt_id")
        item = items.get(pid)
        if item is None:
            stats["no_item"] += 1
            continue

        metric = item["metric"]
        if metric in skip:
            stats["skipped_metric"] += 1
            continue

        # Luot loi: tinh la sai (D7), khong goi grader (khong co response de cham).
        if r.get("status") != "success":
            r["passed"] = False
            r["score"] = 0.0
            r["grade_detail"] = {"reason": f"status={r.get('status')}"}
            stats["error_status"] += 1
            stats["graded"] += 1
            continue

        res = grade(r.get("response"), item)
        r["passed"] = res.passed
        r["score"] = res.score
        r["grade_detail"] = res.detail
        stats["graded"] += 1
        stats["passed"] += int(res.passed)

        if write_db and r.get("message_id"):
            record_quality_score(r["message_id"], res.score)
            stats["db_written"] += 1

    if not dry_run:
        path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="file kết quả thô của runner (run_*.json)")
    ap.add_argument("--skip", action="append", default=[], metavar="METRIC",
                    help=f"bỏ qua 1 metric, lặp lại được. Chọn trong {sorted(GRADERS)}")
    ap.add_argument("--db", action="store_true",
                    help="nạp response_quality_score vào routing_decisions")
    ap.add_argument("--dry-run", action="store_true", help="chỉ in thống kê, không ghi file")
    args = ap.parse_args()

    bad = [m for m in args.skip if m not in GRADERS]
    if bad:
        sys.exit(f"--skip không hợp lệ: {bad}. Chọn trong {sorted(GRADERS)}")
    skip = set(args.skip)
    if skip:
        print(f"BỎ QUA metric: {sorted(skip)} — những lượt đó giữ passed=null (chưa chấm)\n")

    items = load_items()
    grand = {"total": 0, "graded": 0, "passed": 0, "skipped_metric": 0,
             "error_status": 0, "no_item": 0, "db_written": 0}

    for pattern in args.files:
        for path in sorted(Path().glob(pattern)) or [Path(pattern)]:
            if not path.exists():
                print(f"  ! bỏ qua {path} (không tồn tại)")
                continue
            st = grade_file(path, items, skip, args.db, args.dry_run)
            acc = st["passed"] / st["graded"] if st["graded"] else 0.0
            print(f"{path.name}: {st['graded']}/{st['total']} chấm được, "
                  f"đạt {st['passed']} ({acc:.1%})"
                  + (f", {st['error_status']} lượt lỗi tính là sai" if st["error_status"] else "")
                  + (f", {st['skipped_metric']} bỏ qua theo --skip" if st["skipped_metric"] else "")
                  + (f", {st['no_item']} KHÔNG khớp item nào" if st["no_item"] else ""))
            for k in grand:
                grand[k] += st[k]

    print()
    acc = grand["passed"] / grand["graded"] if grand["graded"] else 0.0
    print(f"TỔNG: {grand['graded']}/{grand['total']} lượt đã chấm, đạt {grand['passed']} ({acc:.1%})")
    if grand["skipped_metric"]:
        print(f"  chưa chấm (--skip): {grand['skipped_metric']} — phải nêu rõ trong báo cáo")
    if grand["no_item"]:
        print(f"  ⚠️  {grand['no_item']} record không khớp item nào trong prompts.json — kiểm lại")
    if args.db:
        print(f"  đã nạp response_quality_score cho {grand['db_written']} dòng routing_decisions")
    if args.dry_run:
        print("  (dry-run: KHÔNG ghi file)")


if __name__ == "__main__":
    main()
