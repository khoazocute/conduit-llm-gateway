"""Phân tích phép thử tiêm lỗi provider — D15 (`docs/roadmap.md` mục 4).

Chỉ số chính (đã đăng ký trước, nhị phân): **recovered** = lượt có `status=success` dù
`OPENAI_API_KEY` đã bị làm sai. Kèm: model nào thực sự trả lời (đích dự phòng), và độ
trễ so với **độ trễ nền của đúng (proxy, item) đó** trong thí nghiệm 720 lượt.

⚠️ Kết quả này **KHÔNG** được dùng để chọn lại proxy (D15). Luật 4 bước đã khóa và đã
áp trên 720 lượt — đây là bằng chứng bổ sung cho phần giới hạn.

Chạy (offline, miễn phí):
  PYTHONIOENCODING=utf-8 python experiments/analysis/fault_report.py experiments/results/fault-injection-<ts>
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "results" / "d14-full-720" / "merged.json"
PROXIES = ("litellm", "bifrost", "portkey")


def load_dir(d: Path) -> list[dict[str, Any]]:
    files = sorted(d.glob("run_*.json"))
    if not files:
        sys.exit(f"Không thấy file run_*.json nào trong {d}")
    recs: list[dict[str, Any]] = []
    for f in files:
        recs += json.loads(f.read_text(encoding="utf-8"))
    print(f"Đã đọc {len(recs)} lượt từ {len(files)} file trong {d.name}\n")
    return recs


def baseline_latency() -> dict[tuple[str, str], float]:
    """Độ trễ trung bình của từng (proxy, item) ở điều kiện BÌNH THƯỜNG (720 lượt)."""
    if not BASELINE.exists():
        return {}
    by: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in json.loads(BASELINE.read_text(encoding="utf-8")):
        if r.get("latency_ms") is not None:
            by[(r["proxy_name"], r["prompt_id"])].append(r["latency_ms"])
    return {k: statistics.mean(v) for k, v in by.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("result_dir")
    args = ap.parse_args()

    recs = load_dir(Path(args.result_dir))
    base = baseline_latency()

    print("=" * 92)
    print(f"{'proxy':10s}{'phục hồi':>12s}{'tỷ lệ':>9s}{'model đã trả lời':>34s}"
          f"{'độ trễ TB':>12s}{'so với nền':>13s}")
    print("-" * 92)
    rows = {}
    for px in PROXIES:
        rs = [r for r in recs if r.get("proxy_name") == px]
        if not rs:
            continue
        ok = [r for r in rs if r.get("status") == "success"]
        models = defaultdict(int)
        for r in ok:
            models[r.get("model_selected") or "?"] += 1
        mix = " · ".join(f"{m} {n}" for m, n in sorted(models.items(), key=lambda x: -x[1])) or "—"
        lats = [r["latency_ms"] for r in rs if r.get("latency_ms") is not None]
        mean_lat = statistics.mean(lats) if lats else 0.0
        bl = [base[(px, r["prompt_id"])] for r in rs if (px, r["prompt_id"]) in base]
        base_mean = statistics.mean(bl) if bl else 0.0
        delta = f"+{mean_lat - base_mean:.0f} ms" if base_mean else "—"
        rows[px] = dict(n=len(rs), ok=len(ok), rate=len(ok) / len(rs), mix=mix,
                        mean_lat=mean_lat, base=base_mean)
        print(f"{px:10s}{len(ok):>6d}/{len(rs):<5d}{len(ok)/len(rs):>8.0%}{mix:>34s}"
              f"{mean_lat:>10.0f}ms{delta:>13s}")
    print("=" * 92)

    print("\nChi tiết theo item (model đã trả lời / '—' = không phục hồi):")
    items = sorted({r["prompt_id"] for r in recs})
    print(f"  {'item':12s}" + "".join(f"{px:>22s}" for px in PROXIES))
    for it in items:
        line = f"  {it:12s}"
        for px in PROXIES:
            rs = [r for r in recs if r["proxy_name"] == px and r["prompt_id"] == it]
            ok = [r for r in rs if r.get("status") == "success"]
            ms = sorted({r.get("model_selected") or "?" for r in ok})
            label = f"{len(ok)}/{len(rs)} " + (",".join(ms) if ms else "—")
            line += f"{label:>22s}"
        print(line)

    print("\nĐối chiếu 3 dự đoán đã đăng ký trước (D15):")
    preds = {
        "litellm": (True, "P1 — phục hồi (4 deployment cùng model group conduit-pool)"),
        "bifrost": (True, "P2 — phục hồi qua chuỗi fallback đã cấu hình"),
        "portkey": (False, "P3 — KHÔNG phục hồi (conditional + retry per-target, không có fallback)"),
    }
    for px, (expect_recover, text) in preds.items():
        if px not in rows:
            print(f"  {px:9s} (không có dữ liệu)")
            continue
        got = rows[px]["rate"] > 0.5
        mark = "ĐÚNG" if got == expect_recover else "SAI"
        print(f"  {px:9s} {text}\n            -> thực tế phục hồi {rows[px]['rate']:.0%} => {mark}")

    print("\n⚠️  Nhắc lại ràng buộc D15: KHÔNG dùng kết quả này để chọn lại proxy.")
    print("   Luật 4 bước đã khóa, đã áp trên 720 lượt, kết luận là litellm.")
    print("   Đây là bằng chứng cho phần giới hạn: cái GIÁ của lựa chọn đã chốt.")


if __name__ == "__main__":
    main()
