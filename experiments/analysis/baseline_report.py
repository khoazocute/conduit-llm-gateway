"""Phân tích baseline "một model cố định" (D18, docs/roadmap.md mục 4) — CHỈ TÍNH TOÁN.

Không gọi API, không đụng DB. Đọc 2 nguồn đã có sẵn trên đĩa:
  - 720 lượt của 3 proxy: experiments/results/d14-full-720/merged.json
  - 3 nhánh baseline (80 item × 1 lần/nhánh, đã chấm bằng grade_results.py):
    experiments/results/d18-baseline-<ngày>/<model>/run_*.json

Đúng D18 mục 5–7 (đăng ký trước 09/11, không đổi khi làm):
  (5) Kiểm đo đúng: nhánh gpt-4o-mini so theo TỪNG ITEM với kết quả đa số 3 lần của LiteLLM;
      lệch > 4/80 item thì báo con số như sàn nhiễu đo.
  (6) 6 điểm (3 proxy + 3 baseline): độ chính xác (lượt lỗi = sai, D7), chi phí TB/lượt thành
      công, chi phí/câu đạt. Đường biên Pareto = các điểm không bị điểm nào khác VỪA rẻ hơn
      VỪA chính xác hơn (đúng nguyên văn D18: trội chặt ở cả hai trục).
  (7) Cận trên lý thuyết: mỗi item lấy model RẺ NHẤT trả lời đúng trong 3 baseline; item không
      model nào đúng thì tính chi phí của gpt-4o-mini.

Kết quả KHÔNG dùng để chọn lại proxy (D18) — luật 4 bước đã áp trên 720 lượt.

Chạy (từ gốc repo):
  PYTHONIOENCODING=utf-8 python experiments/analysis/baseline_report.py \
      --baseline-dir experiments/results/d18-baseline-20261110
  ... --no-chart      # bỏ biểu đồ (không cần matplotlib)
"""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decision_rule import (  # noqa: E402  - dùng CHUNG định nghĩa chỉ số với 720 lượt
    _grade_of,
    compute_avg_cost,
    compute_cost_per_passing,
    compute_quality_accuracy,
    count_ungraded,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MERGED = ROOT / "experiments" / "results" / "d14-full-720" / "merged.json"

PROXIES = ["litellm", "bifrost", "portkey"]
# Xếp theo giá niêm yết rẻ -> đắt (model_pricing). Cũng là thứ tự chạy của TASK-72.
BASELINE_MODELS = ["gpt-4o-mini", "claude-haiku", "gpt-4o"]
FALLBACK_MODEL = "gpt-4o-mini"  # D18 (7): item không model nào đúng thì tính chi phí model này
MINI_CHECK_TOLERANCE = 4         # D18 (5): lệch > 4/80 item thì báo cáo con số lệch


def baseline_name(model: str) -> str:
    return f"baseline-{model}"


# ---------------------------------------------------------------------------- nạp dữ liệu

def dedupe_runs(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Mỗi (prompt_id, run_index) giữ đúng 1 bản ghi.

    `run_experiment.py --resume` GHI TIẾP lượt chạy lại vào cùng file, nên lượt lỗi cũ vẫn nằm
    trong file cạnh lượt thành công mới. Có lượt thành công thì giữ lượt thành công (lượt
    sau cùng), bỏ lượt lỗi; không có thì giữ bản ghi sau cùng. Trả về số lượt lỗi bị thay
    để báo cáo minh bạch, không âm thầm.
    """
    by_key: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for r in records:
        by_key.setdefault((r["prompt_id"], r.get("run_index", 1)), []).append(r)
    kept: list[dict[str, Any]] = []
    replaced = 0
    for rows in by_key.values():
        ok = [r for r in rows if r.get("status") == "success"]
        if ok:
            kept.append(ok[-1])
            replaced += sum(1 for r in rows if r.get("status") != "success")
        else:
            kept.append(rows[-1])
    return kept, replaced


def load_baseline_dir(base_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    """model -> bản ghi đã khử trùng, đổi nhãn proxy_name thành 'baseline-<model>'.

    File gốc ghi proxy_name='litellm' (đúng sự thật: đi qua LiteLLM) — đổi nhãn trên BẢN SAO
    để các hàm của decision_rule.py tách được 3 nhánh khỏi nhau và khỏi 720 lượt.
    """
    by_model: dict[str, list[dict[str, Any]]] = {}
    replaced: dict[str, int] = {}
    for model in BASELINE_MODELS:
        files = sorted((base_dir / model).glob("run_*.json"))
        if not files:
            raise SystemExit(f"Không thấy file kết quả cho nhánh {model} trong {base_dir / model}")
        raw: list[dict[str, Any]] = []
        for f in files:
            raw.extend(json.loads(f.read_text(encoding="utf-8")))
        kept, n_rep = dedupe_runs(raw)
        wrong_model = [r["prompt_id"] for r in kept
                       if r.get("status") == "success" and r.get("model_selected") != model]
        if wrong_model:
            raise SystemExit(f"Nhánh {model}: {len(wrong_model)} lượt do model khác trả lời "
                             f"({wrong_model[:5]}...) - sai thiết kế D18 (2), không phân tích tiếp")
        by_model[model] = [{**r, "proxy_name": baseline_name(model)} for r in kept]
        replaced[model] = n_rep
    return by_model, replaced


# ---------------------------------------------------------------------------- D18 (6)

def point_metrics(records: list[dict[str, Any]], name: str) -> dict[str, Any]:
    rows = [r for r in records if r["proxy_name"] == name]
    ok = [r for r in rows if r.get("status") == "success"]
    return {
        "name": name,
        "kind": "baseline" if name.startswith("baseline-") else "proxy",
        "n_runs": len(rows),
        "n_success": len(ok),
        "n_error": len(rows) - len(ok),
        "n_ungraded": count_ungraded(records, name),
        "n_passed": sum(1 for r in ok if _grade_of(r)),
        "accuracy": compute_quality_accuracy(records, name),
        "avg_cost": compute_avg_cost(records, name),
        "cost_total": sum(r.get("cost") or 0 for r in ok),
        "cost_per_passing": compute_cost_per_passing(records, name),
    }


def pareto_front(points: list[dict[str, Any]]) -> set[str]:
    """Tên các điểm KHÔNG bị điểm nào khác vừa rẻ hơn (avg_cost <) vừa chính xác hơn
    (accuracy >) — trội chặt ở cả hai trục, đúng nguyên văn D18 (6). Hệ quả cần biết: hai
    điểm bằng nhau ở một trục thì không điểm nào loại được điểm kia."""
    front = set()
    for p in points:
        dominated = any(q["avg_cost"] < p["avg_cost"] and q["accuracy"] > p["accuracy"]
                        for q in points if q["name"] != p["name"])
        if not dominated:
            front.add(p["name"])
    return front


def by_category(records: list[dict[str, Any]], names: list[str]) -> list[dict[str, Any]]:
    """Độ chính xác theo từng bộ benchmark (lỗi = sai), để thảo luận model nào mạnh ở đâu."""
    out = []
    for name in names:
        for cat in sorted({r["category"] for r in records if r["proxy_name"] == name}):
            rows = [r for r in records if r["proxy_name"] == name and r["category"] == cat]
            passed = sum(1 for r in rows if r.get("status") == "success" and _grade_of(r))
            out.append({"name": name, "category": cat, "n_runs": len(rows), "n_passed": passed,
                        "accuracy": passed / len(rows) if rows else 0.0})
    return out


# ---------------------------------------------------------------------------- D18 (7)

def upper_bound(by_model: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Cận trên lý thuyết trên 3 baseline (1 lần/item/model).

    Mỗi item: trong các model trả lời ĐÚNG, chọn model có chi phí THỰC trên chính item đó thấp
    nhất. Không model nào đúng -> tính chi phí của gpt-4o-mini trên item đó (lượt lỗi = $0).
    """
    index = {m: {r["prompt_id"]: r for r in rows} for m, rows in by_model.items()}
    items = sorted(set().union(*[set(ix) for ix in index.values()]))
    per_item = []
    for pid in items:
        correct = []
        for m in BASELINE_MODELS:
            r = index.get(m, {}).get(pid)
            if r and r.get("status") == "success" and _grade_of(r):
                correct.append((r.get("cost") or 0.0, BASELINE_MODELS.index(m), m))
        if correct:
            cost, _, model = min(correct)
            per_item.append({"prompt_id": pid, "model": model, "correct": True, "cost": cost})
        else:
            fb = index.get(FALLBACK_MODEL, {}).get(pid)
            cost = (fb.get("cost") or 0.0) if fb and fb.get("status") == "success" else 0.0
            per_item.append({"prompt_id": pid, "model": None, "correct": False, "cost": cost})
    n = len(per_item)
    covered = sum(1 for x in per_item if x["correct"])
    total = sum(x["cost"] for x in per_item)
    return {
        "n_items": n,
        "n_covered": covered,
        "accuracy": covered / n if n else 0.0,
        "cost_total": total,
        "avg_cost": total / n if n else 0.0,
        "cost_per_passing": total / covered if covered else None,
        "picks": dict(Counter(x["model"] or "none" for x in per_item)),
        "per_item": per_item,
    }


# ---------------------------------------------------------------------------- D18 (5)

def mini_check(mini_records: list[dict[str, Any]], merged: list[dict[str, Any]],
               proxy: str = "litellm") -> dict[str, Any]:
    """So nhánh gpt-4o-mini với kết quả ĐA SỐ 3 lần của LiteLLM (cũng 100% gpt-4o-mini), từng item.

    Đa số = đạt ở >= 2/3 lượt (lượt lỗi = không đạt). Lệch = hai bên khác nhau đúng/sai.
    """
    lite: dict[str, list[bool]] = {}
    for r in merged:
        if r["proxy_name"] == proxy:
            lite.setdefault(r["prompt_id"], []).append(r.get("status") == "success" and bool(_grade_of(r)))
    mini = {r["prompt_id"]: r.get("status") == "success" and bool(_grade_of(r)) for r in mini_records}
    mismatches = []
    for pid in sorted(set(lite) | set(mini)):
        runs = lite.get(pid, [])
        majority = sum(runs) * 2 > len(runs) if runs else None
        if pid not in mini or majority is None or majority != mini[pid]:
            mismatches.append({"prompt_id": pid, "litellm_passes": sum(runs), "litellm_runs": len(runs),
                               "litellm_majority": majority, "baseline_mini": mini.get(pid)})
    return {
        "n_items": len(set(lite) | set(mini)),
        "n_mismatch": len(mismatches),
        "tolerance": MINI_CHECK_TOLERANCE,
        "exceeds_tolerance": len(mismatches) > MINI_CHECK_TOLERANCE,
        "mismatches": mismatches,
    }


# ---------------------------------------------------------------------------- xuất kết quả

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # BOM: Excel đọc đúng tiếng Việt
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


LABELS = {
    "litellm": "LiteLLM", "bifrost": "Bifrost", "portkey": "Portkey",
    "baseline-gpt-4o-mini": "Chỉ gpt-4o-mini", "baseline-claude-haiku": "Chỉ claude-haiku",
    "baseline-gpt-4o": "Chỉ gpt-4o",
}


def draw_chart(points: list[dict[str, Any]], front: set[str], ub: dict[str, Any], out_png: Path) -> None:
    """Biểu đồ chi phí–chính xác cho báo cáo (ảnh tĩnh, nền sáng để in).

    Theo skill dataviz: tán xạ chỉ dùng tối đa 3 màu phân loại -> mã hóa theo NHÓM (proxy /
    baseline), phân biệt thêm bằng hình dạng; nhãn tên đặt trực tiếp cạnh điểm (không ghi số
    trên mọi điểm — số nằm ở bảng); lưới và trục nhạt; một trục y duy nhất.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

    surface, ink, ink2, muted, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
    color = {"proxy": "#2a78d6", "baseline": "#eb6834"}  # slot 1, slot 2 bảng màu mặc định
    marker = {"proxy": "o", "baseline": "s"}
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]

    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=200)
    fig.patch.set_facecolor(surface)
    ax.set_facecolor(surface)

    # Ngưỡng bước 1 của luật quyết định (đã khóa) — chỉ là bối cảnh
    ax.axhline(80, color=muted, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.text(1.0e-4 * 1.04, 80.4, "Ngưỡng 80% (bước 1 của luật quyết định)", color=ink2, fontsize=7.5,
            va="bottom")

    fpts = sorted([p for p in points if p["name"] in front], key=lambda p: p["avg_cost"])
    ax.plot([p["avg_cost"] for p in fpts], [p["accuracy"] * 100 for p in fpts],
            color=muted, lw=1.5, zorder=2, label="Đường biên Pareto (6 điểm)")

    for kind, lab in (("proxy", "Proxy (720 lượt, 3 lần/item)"), ("baseline", "Một model cố định (1 lần/item)")):
        ps = [p for p in points if p["kind"] == kind]
        ax.scatter([p["avg_cost"] for p in ps], [p["accuracy"] * 100 for p in ps], s=64,
                   marker=marker[kind], color=color[kind], edgecolors=surface, linewidths=2,
                   zorder=4, label=lab)
    ax.scatter([ub["avg_cost"]], [ub["accuracy"] * 100], s=80, marker="D", facecolors=surface,
               edgecolors=ink2, linewidths=1.5, zorder=4, label="Cận trên lý thuyết (3 baseline)")

    offsets = {  # tránh chồng nhãn: (dx điểm ảnh, dy điểm ảnh, căn lề)
        "litellm": (8, -12, "left"), "baseline-gpt-4o-mini": (8, 4, "left"),
        "bifrost": (8, -4, "left"), "portkey": (-8, 6, "right"),
        "baseline-claude-haiku": (0, -14, "center"), "baseline-gpt-4o": (8, 4, "left"),
    }
    for p in points:
        dx, dy, ha = offsets.get(p["name"], (8, 0, "left"))
        ax.annotate(LABELS.get(p["name"], p["name"]), (p["avg_cost"], p["accuracy"] * 100),
                    xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    fontsize=8.5, color=ink)
    ax.annotate("Cận trên", (ub["avg_cost"], ub["accuracy"] * 100), xytext=(8, 0),
                textcoords="offset points", ha="left", va="center", fontsize=8.5, color=ink2)

    ax.set_xscale("log")
    ticks = [1e-4, 2e-4, 5e-4, 1e-3, 2e-3]
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.4f}".rstrip("0").replace(".", ",")))
    ax.set_xlim(0.9e-4, 2.6e-3)
    lo = min(78.0, min(p["accuracy"] * 100 for p in points) - 2)
    ax.set_ylim(lo, 100)
    ax.yaxis.set_major_locator(FixedLocator([v for v in range(80, 101, 5) if v >= lo]))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("Chi phí trung bình mỗi lượt thành công (USD, thang log)", color=ink2, fontsize=9)
    ax.set_ylabel("Độ chính xác (80 item, lỗi tính là sai)", color=ink2, fontsize=9)
    ax.grid(True, color=grid, lw=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(grid)
    ax.tick_params(colors=ink2, labelsize=8, length=0)
    leg = ax.legend(loc="upper left", fontsize=7.5, frameon=False, labelcolor=ink2)
    leg.set_zorder(5)
    fig.tight_layout()
    fig.savefig(out_png, facecolor=surface)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-dir", required=True, type=Path)
    ap.add_argument("--merged", type=Path, default=DEFAULT_MERGED)
    ap.add_argument("--out-dir", type=Path, help="mặc định <baseline-dir>/tables")
    ap.add_argument("--no-chart", action="store_true")
    args = ap.parse_args()
    out_dir = args.out_dir or args.baseline_dir / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)

    merged = json.loads(args.merged.read_text(encoding="utf-8"))
    by_model, replaced = load_baseline_dir(args.baseline_dir)
    records = merged + [r for rows in by_model.values() for r in rows]

    names = PROXIES + [baseline_name(m) for m in BASELINE_MODELS]
    points = [point_metrics(records, n) for n in names]
    ungraded = {p["name"]: p["n_ungraded"] for p in points if p["n_ungraded"]}
    if ungraded:
        raise SystemExit(f"Còn lượt chưa chấm {ungraded} - chạy grade_results.py trước")
    front = pareto_front(points)
    for p in points:
        p["on_pareto"] = p["name"] in front
    ub = upper_bound(by_model)
    check = mini_check(by_model[FALLBACK_MODEL], merged)

    write_csv(out_dir / "points.csv", points,
              ["name", "kind", "n_runs", "n_success", "n_error", "n_passed", "accuracy",
               "avg_cost", "cost_total", "cost_per_passing", "on_pareto"])
    write_csv(out_dir / "by_category.csv", by_category(records, names),
              ["name", "category", "n_runs", "n_passed", "accuracy"])
    write_csv(out_dir / "upper_bound_items.csv", ub["per_item"], ["prompt_id", "model", "correct", "cost"])
    summary = {
        "note": "D18 - phan tich bo sung, KHONG dung de chon lai proxy",
        "replaced_error_runs": replaced,
        "pareto_front": sorted(front),
        "upper_bound": {k: v for k, v in ub.items() if k != "per_item"},
        "mini_check": check,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    if not args.no_chart:
        draw_chart(points, front, ub, out_dir / "cost_accuracy.png")

    print(f"{'diem':24} {'n':>4} {'dat':>4} {'chinh xac':>9} {'$/luot':>10} {'$/cau dat':>10} pareto")
    for p in points:
        cpp = p["cost_per_passing"]
        print(f"{p['name']:24} {p['n_runs']:>4} {p['n_passed']:>4} {p['accuracy']:>9.2%} "
              f"{p['avg_cost']:>10.6f} {cpp if cpp is None else f'{cpp:.6f}':>10} {p['on_pareto']}")
    print(f"\nCan tren: {ub['n_covered']}/{ub['n_items']} = {ub['accuracy']:.2%}, "
          f"$/item {ub['avg_cost']:.6f}, chon {ub['picks']}")
    print(f"Kiem mini vs LiteLLM: lech {check['n_mismatch']}/{check['n_items']} item "
          f"({'VUOT' if check['exceeds_tolerance'] else 'trong'} nguong {MINI_CHECK_TOLERANCE})")
    for m in check["mismatches"]:
        print(f"   {m}")
    print(f"Luot loi bi thay bang luot chay lai: {replaced}")
    print(f"\nDa ghi {out_dir}")


if __name__ == "__main__":
    main()
