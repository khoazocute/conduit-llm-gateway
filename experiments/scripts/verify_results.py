"""Kiểm tính toàn vẹn file kết quả thô TRƯỚC khi áp luật quyết định.

Chạy:
  PYTHONIOENCODING=utf-8 python experiments/scripts/verify_results.py experiments/results/run_*.json
Thoát mã 1 nếu có vấn đề (dùng được trong dry_run.sh / CI).

Vì sao cần: `ChatService.unitPrice()` trả về 0 khi không tìm thấy dòng `model_pricing`
khớp — nên một lượt ghi sai tên model sẽ được ghi là **tốn $0** mà không báo gì. Bước 2
của luật quyết định là "chi phí trung bình thấp nhất", nên proxy nào bị lỗi đó sẽ trông
như **miễn phí** và thắng — vì một cái bug, không vì nó tốt. Đây là loại lỗi "sai mà không
báo" nên phải có bước kiểm chặn lại, không dựa vào việc nhớ kiểm tay.

Kiểm 5 thứ:
  1. Tên model nằm trong `model_pricing` (hỏi DB; không có DB thì dùng danh sách alias dự phòng)
  2. Lượt `success` phải có `cost > 0`
  3. Lượt `success` phải có `response` không rỗng
  4. Mỗi (prompt_id, run_index) chỉ xuất hiện 1 lần
  5. Số lượt khớp kỳ vọng (nếu truyền --expect)
"""
import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PG = ["docker", "exec", "-i", "conduit-postgres", "psql", "-U", "conduit", "-d", "conduit", "-tAc"]
# Dung khi khong goi duoc DB - pool 5 model o CLAUDE.md muc 2.
FALLBACK_ALIASES = {"gpt-4o-mini", "gemini-flash", "claude-haiku", "gpt-4o", "claude-sonnet"}


def known_models() -> tuple[set[str], str]:
    try:
        out = subprocess.run([*PG, "SELECT DISTINCT model FROM model_pricing;"],
                             capture_output=True, text=True, timeout=30)
        models = {m.strip() for m in out.stdout.splitlines() if m.strip()}
        if models:
            return models, "model_pricing (DB)"
    except Exception:
        pass
    return FALLBACK_ALIASES, "danh sách dự phòng (KHÔNG gọi được DB)"


def check(path: Path, models: set[str], expect: int | None) -> list[str]:
    problems: list[str] = []
    records: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    if expect is not None and len(records) != expect:
        problems.append(f"có {len(records)} lượt, kỳ vọng {expect}")

    seen = Counter((r.get("prompt_id"), r.get("run_index")) for r in records)
    for key, n in seen.items():
        if n > 1:
            problems.append(f"{key[0]} run{key[1]} xuất hiện {n} lần (trùng lượt)")

    for i, r in enumerate(records):
        tag = f"{r.get('prompt_id')} run{r.get('run_index')}"
        model = r.get("model_selected")
        status = r.get("status")

        if status == "success":
            if not model:
                problems.append(f"{tag}: success nhưng không có model_selected")
            elif model not in models:
                problems.append(
                    f"{tag}: model {model!r} KHÔNG có trong {len(models)} model đã biết "
                    f"-> chi phí sẽ bị ghi 0 trong im lặng")
            cost = r.get("cost")
            if not cost or float(cost) <= 0:
                problems.append(f"{tag}: success nhưng cost={cost!r} (phải > 0)")
            if not (r.get("response") or "").strip():
                problems.append(f"{tag}: success nhưng response rỗng")
        elif status is None:
            problems.append(f"lượt #{i}: thiếu status")

    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--expect", type=int, default=None,
                    help="Số lượt kỳ vọng trong MỖI file (vd 60 = 20 item x 3 lần).")
    args = ap.parse_args()

    models, source = known_models()
    print(f"Model đã biết ({len(models)}) từ {source}: {sorted(models)}\n")

    total_problems = 0
    for pattern in args.files:
        for path in sorted(Path().glob(pattern)) or [Path(pattern)]:
            if not path.exists():
                print(f"  ! bỏ qua {path} (không tồn tại)")
                continue
            problems = check(path, models, args.expect)
            if problems:
                print(f"⛔ {path.name}: {len(problems)} vấn đề")
                for p in problems[:25]:
                    print(f"     - {p}")
                if len(problems) > 25:
                    print(f"     ... và {len(problems) - 25} vấn đề nữa")
            else:
                print(f"✅ {path.name}: không có vấn đề")
            total_problems += len(problems)

    print()
    if total_problems:
        print(f"TỔNG: {total_problems} vấn đề — KHÔNG áp luật quyết định lên dữ liệu này "
              f"trước khi xử lý xong.")
        sys.exit(1)
    print("TỔNG: dữ liệu sạch, áp luật quyết định được.")


if __name__ == "__main__":
    main()
