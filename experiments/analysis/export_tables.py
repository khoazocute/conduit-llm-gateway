"""Xuất kết quả thí nghiệm ra CSV để đọc/vẽ biểu đồ + in bảng tổng hợp ra console.

Chạy sau khi đã chấm (`grade_results.py`):
  PYTHONIOENCODING=utf-8 python experiments/analysis/export_tables.py experiments/results/run_*.json
  ... -o experiments/results/phase3-20261018      # thư mục xuất (mặc định: cạnh file đầu tiên)

Sinh 4 file CSV:
  runs.csv              1 dòng/lượt gọi — bảng phẳng, mở Excel/pandas vẽ được ngay
  summary_proxy.csv     1 dòng/proxy — các chỉ số của luật quyết định + chi phí/câu đạt
  summary_proxy_set.csv 1 dòng/(proxy × bộ benchmark) — xem proxy mạnh/yếu ở bộ nào
  model_mix.csv         1 dòng/(proxy × model) — BẮT BUỘC có trong báo cáo: không có bảng
                        này thì con số accuracy vô nghĩa (docs/experiment-design.md mục 6.2)

Không gọi API, không tốn tiền — chạy lại bao nhiêu lần cũng được.
"""
import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Tier suy tu model: map tier -> model la 1:1 nen khong can ghi cot rieng trong DB
# (docs/experiment-design.md muc 10).
TIER_OF = {"gpt-4o-mini": "SIMPLE", "claude-haiku": "MEDIUM", "gpt-4o": "COMPLEX"}

RUN_FIELDS = ["proxy", "benchmark", "prompt_id", "run_index", "model", "tier",
              "status", "passed", "score", "cost_usd", "credit", "latency_ms",
              "metric", "timestamp"]


def load(patterns: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_files: list[Path] = []
    for pattern in patterns:
        p = Path(pattern)
        matches = sorted(p.parent.glob(p.name)) if (p.is_absolute() or "/" in pattern
                                                    or "\\" in pattern) else sorted(Path().glob(pattern))
        for path in matches or [p]:
            if not path.exists():
                print(f"  ! bỏ qua {path} (không tồn tại)")
                continue
            records += json.loads(path.read_text(encoding="utf-8"))
            seen_files.append(path)
    if not records:
        sys.exit("Không đọc được bản ghi nào.")
    print(f"Đã đọc {len(records)} lượt từ {len(seen_files)} file")
    return records


def pct(x: float) -> str:
    return f"{x:.1%}"


def write_runs(records: list[dict[str, Any]], out: Path) -> None:
    with (out / "runs.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=RUN_FIELDS)
        w.writeheader()
        for r in records:
            model = r.get("model_selected")
            w.writerow({
                "proxy": r.get("proxy_name"),
                "benchmark": r.get("category"),
                "prompt_id": r.get("prompt_id"),
                "run_index": r.get("run_index"),
                "model": model,
                "tier": TIER_OF.get(model, ""),
                "status": r.get("status"),
                # de trong neu chua cham - KHONG ghi False (khong duoc coi "chua cham" la "sai")
                "passed": "" if r.get("passed") is None else int(bool(r.get("passed"))),
                "score": "" if r.get("score") is None else r.get("score"),
                "cost_usd": r.get("cost"),
                "credit": r.get("credit_charged"),
                "latency_ms": r.get("latency_ms"),
                "metric": r.get("metric"),
                "timestamp": r.get("timestamp"),
            })


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Chỉ số cho 1 nhóm lượt. Quy ước khớp decision_rule.py (D7)."""
    ok = [r for r in rows if r.get("status") == "success"]
    graded = [r for r in rows if r.get("status") != "success" or r.get("passed") is not None]
    n_passed = sum(1 for r in ok if r.get("passed"))
    cost_total = sum(r.get("cost") or 0 for r in ok)       # luot loi khong tinh phi
    lats = [r["latency_ms"] for r in ok if r.get("latency_ms") is not None]
    return {
        "n_runs": len(rows),
        "n_success": len(ok),
        "n_error": len(rows) - len(ok),
        "n_graded": len(graded),
        "n_ungraded": len(ok) - sum(1 for r in ok if r.get("passed") is not None),
        "n_passed": n_passed,
        "accuracy": n_passed / len(graded) if graded else 0.0,
        "error_rate": (len(rows) - len(ok)) / len(rows) if rows else 0.0,
        "cost_total_usd": cost_total,
        "cost_per_run_usd": cost_total / len(ok) if ok else 0.0,
        # Chi so dien giai chinh (y cua Khoa): gop ca 2 ve muc tieu cua thay vao 1 so.
        # Re ma sai thi van bi tinh la dat. Rong neu khong co cau nao dat.
        "cost_per_passing_usd": (cost_total / n_passed) if n_passed else None,
        "p95_latency_ms": (statistics.quantiles(lats, n=20)[18] if len(lats) >= 20
                           else (max(lats) if lats else 0.0)),
        "mean_latency_ms": (statistics.mean(lats) if lats else 0.0),
    }


def consistency(rows: list[dict[str, Any]]) -> float:
    """Tỷ lệ item mà proxy chọn CÙNG một model qua mọi lần lặp (bước 4 luật quyết định)."""
    by_item: dict[str, set] = defaultdict(set)
    for r in rows:
        by_item[r.get("prompt_id")].add(r.get("model_selected"))
    if not by_item:
        return 0.0
    return sum(1 for v in by_item.values() if len(v) == 1) / len(by_item)


def write_summaries(records: list[dict[str, Any]], out: Path) -> dict[str, dict]:
    by_proxy: dict[str, list] = defaultdict(list)
    by_proxy_set: dict[tuple, list] = defaultdict(list)
    for r in records:
        by_proxy[r.get("proxy_name")].append(r)
        by_proxy_set[(r.get("proxy_name"), r.get("category"))].append(r)

    cols = ["proxy", "n_runs", "n_success", "n_error", "n_ungraded", "n_passed",
            "accuracy", "error_rate", "cost_total_usd", "cost_per_run_usd",
            "cost_per_passing_usd", "p95_latency_ms", "mean_latency_ms", "consistency_rate"]
    summary = {}
    with (out / "summary_proxy.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for proxy in sorted(by_proxy):
            s = summarise(by_proxy[proxy])
            s["consistency_rate"] = consistency(by_proxy[proxy])
            summary[proxy] = s
            w.writerow({"proxy": proxy, **{k: s[k] for k in cols if k != "proxy"}})

    with (out / "summary_proxy_set.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["proxy", "benchmark"] + [c for c in cols if c != "proxy"])
        w.writeheader()
        for (proxy, bench) in sorted(by_proxy_set):
            s = summarise(by_proxy_set[(proxy, bench)])
            s["consistency_rate"] = consistency(by_proxy_set[(proxy, bench)])
            w.writerow({"proxy": proxy, "benchmark": bench,
                        **{k: s[k] for k in cols if k != "proxy"}})
    return summary


def write_model_mix(records: list[dict[str, Any]], out: Path) -> dict[str, list]:
    by: dict[tuple, list] = defaultdict(list)
    for r in records:
        by[(r.get("proxy_name"), r.get("model_selected"))].append(r)
    totals: dict[str, int] = defaultdict(int)
    for (proxy, _), rows in by.items():
        totals[proxy] += len(rows)

    mix: dict[str, list] = defaultdict(list)
    with (out / "model_mix.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["proxy", "model", "tier", "n_runs", "share", "n_passed",
                    "accuracy", "cost_total_usd", "cost_per_run_usd"])
        for (proxy, model) in sorted(by, key=lambda k: (k[0] or "", k[1] or "")):
            rows = by[(proxy, model)]
            s = summarise(rows)
            share = len(rows) / totals[proxy] if totals[proxy] else 0.0
            w.writerow([proxy, model, TIER_OF.get(model, ""), len(rows), round(share, 4),
                        s["n_passed"], round(s["accuracy"], 4),
                        s["cost_total_usd"], s["cost_per_run_usd"]])
            mix[proxy].append((model, len(rows), share, s["accuracy"]))
    return mix


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="file kết quả thô (run_*.json), đã chấm")
    ap.add_argument("-o", "--out", help="thư mục xuất CSV (mặc định: cạnh file đầu tiên)")
    args = ap.parse_args()

    records = load(args.files)
    out = Path(args.out) if args.out else Path(args.files[0]).parent / "tables"
    out.mkdir(parents=True, exist_ok=True)

    write_runs(records, out)
    summary = write_summaries(records, out)
    mix = write_model_mix(records, out)

    print()
    print("=" * 100)
    print(f"{'proxy':10s}{'đạt':>8s}{'độ c.xác':>10s}{'lỗi':>7s}{'chi phí TB':>12s}"
          f"{'/câu đạt':>11s}{'p95 ms':>9s}{'nhất quán':>11s}{'chưa chấm':>11s}")
    print("-" * 100)
    for proxy, s in sorted(summary.items()):
        cpp = f"{s['cost_per_passing_usd']:.6f}" if s["cost_per_passing_usd"] else "—"
        print(f"{proxy:10s}{s['n_passed']:>4d}/{s['n_graded']:<3d}{pct(s['accuracy']):>10s}"
              f"{pct(s['error_rate']):>7s}{s['cost_per_run_usd']:>12.6f}{cpp:>11s}"
              f"{s['p95_latency_ms']:>9.0f}{s['consistency_rate']:>11.2f}{s['n_ungraded']:>11d}")
    print("=" * 100)
    print()
    print("Tỷ lệ model mỗi proxy đã chọn (BẮT BUỘC có trong báo cáo):")
    for proxy in sorted(mix):
        parts = [f"{m} {n} lượt ({sh:.0%}, đạt {acc:.0%})" for m, n, sh, acc in
                 sorted(mix[proxy], key=lambda x: -x[1])]
        print(f"  {proxy:10s} " + " · ".join(parts))
    print()
    print(f"Đã xuất 4 file CSV vào {out}")
    for name in ("runs.csv", "summary_proxy.csv", "summary_proxy_set.csv", "model_mix.csv"):
        print(f"  - {name}")


if __name__ == "__main__":
    main()
