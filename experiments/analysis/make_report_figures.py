"""Vẽ lại bốn hình kết quả của báo cáo (Hình 5.9 đến 5.12) từ dữ liệu trong repo, không tiêu đề trong ảnh
(tiêu đề nằm ở chú thích dưới ảnh trong báo cáo, nên số hình không bị lệch khi đánh số lại).

Nguồn số: experiments/results/d14-full-720/tables/*.csv (720 lượt), d18-baseline-20261110 (baseline),
docs/load-test.md (k6). Chạy: python experiments/analysis/make_report_figures.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "experiments" / "results" / "d14-full-720" / "tables"
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
COL = {"litellm": "#2563eb", "bifrost": "#d97706", "portkey": "#059669"}
NAME = {"litellm": "LiteLLM", "bifrost": "Bifrost", "portkey": "Portkey"}


def rows(name: str) -> list[dict]:
    with open(TABLES / name, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def clean(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)


def fig_cost() -> None:
    data = rows("summary_proxy_set.csv")
    sets = ["mmlu", "gsm8k", "humaneval", "ifeval"]
    label = {"mmlu": "MMLU", "gsm8k": "GSM8K", "humaneval": "HumanEval", "ifeval": "IFEval"}
    fig, ax = plt.subplots(figsize=(8, 4.6))
    w = 0.26
    for i, p in enumerate(["litellm", "bifrost", "portkey"]):
        ys = [float(next(r for r in data if r["proxy"] == p and r["benchmark"] == s)["cost_per_run_usd"]) for s in sets]
        ax.bar([x + (i - 1) * w for x in range(4)], ys, w, label=NAME[p], color=COL[p])
    ax.set_yscale("log")
    ax.set_xticks(range(4), [label[s] for s in sets])
    ax.set_ylabel("Chi phí trung bình mỗi câu hỏi (USD, thang log)")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.1), frameon=False)
    ax.grid(axis="y", alpha=0.25, which="both")
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "hinh-5-9-chi-phi.png", dpi=200)
    plt.close(fig)


def fig_mix() -> None:
    data = rows("model_mix.csv")
    order = ["litellm", "bifrost", "portkey"]
    models = [("gpt-4o-mini", "#93c5fd"), ("claude-haiku", "#86efac"), ("gpt-4o", "#fca5a5"), ("", "#9ca3af")]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    for yi, p in enumerate(order):
        left = 0
        for m, c in models:
            n = sum(int(r["n_runs"]) for r in data if r["proxy"] == p and r["model"] == m)
            if n:
                ax.barh(yi, n, left=left, color=c, edgecolor="white", label=("Lỗi" if m == "" else m) if yi == 1 else None)
                ax.text(left + n / 2, yi, str(n), ha="center", va="center", fontsize=9)
                left += n
    ax.set_yticks(range(3), [NAME[p] for p in order])
    ax.set_xlabel("Số lượt (trên tổng 240 lượt mỗi proxy)")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.22), frameon=False)
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "hinh-5-10-phan-bo-mo-hinh.png", dpi=200)
    plt.close(fig)


def fig_pareto(with_baselines: bool) -> None:
    s = {r["proxy"]: r for r in rows("summary_proxy.csv")}
    fig, ax = plt.subplots(figsize=(7.4, 5.4))
    for p in ["litellm", "bifrost", "portkey"]:
        x = float(s[p]["cost_per_run_usd"]) * 1e6
        y = float(s[p]["accuracy"]) * 100
        ax.scatter(x, y, s=130, color=COL[p], zorder=3)
        ax.annotate(f"{NAME[p]}\n({x:.0f} µUSD, {y:.1f}%)", (x, y), textcoords="offset points", xytext=(10, -26), fontsize=9)
    if with_baselines:
        base = [("Chỉ gpt-4o-mini", 122.1, 85.0, (10, 8)), ("Chỉ claude-haiku", 1164.4, 91.3, (-95, -42)), ("Chỉ gpt-4o", 1896.5, 91.3, (-70, 16))]
        for n, x, y, off in base:
            ax.scatter(x, y, s=110, facecolors="none", edgecolors="#374151", linewidths=1.6, zorder=3)
            ax.annotate(f"{n}\n({x:.0f} µUSD, {y:.1f}%)", (x, y), textcoords="offset points", xytext=off, fontsize=8, color="#374151")
    ax.axhline(80, color="#dc2626", ls=":", lw=1.4)
    ax.text(0.01, 80.3, "Ngưỡng tối thiểu 80%", color="#dc2626", fontsize=8, transform=ax.get_yaxis_transform())
    ax.axhline(97.5, color="#6b7280", ls=":", lw=1.4)
    ax.text(0.01, 97.7, "Cận trên lý thuyết 97,5%", color="#6b7280", fontsize=8, transform=ax.get_yaxis_transform())
    ax.set_xscale("log")
    ax.set_xticks([100, 200, 500, 1000, 2000], ["100", "200", "500", "1.000", "2.000"])
    ax.minorticks_off()
    ax.set_ylim(78, 100)
    ax.set_xlabel("Chi phí trung bình mỗi câu hỏi (µUSD, thang log)")
    ax.set_ylabel("Tỷ lệ đạt trên 4 bộ đề chuẩn (%)")
    ax.grid(alpha=0.25, which="both")
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / ("hinh-5-11-pareto-co-baseline.png" if with_baselines else "hinh-5-11-pareto.png"), dpi=200)
    plt.close(fig)


def fig_load() -> None:
    fig, ax = plt.subplots(figsize=(7, 4.6))
    labels = ["Chat (alias giả)\n25 người dùng ảo, 23.640 lượt", "Duyệt sàn, xem danh sách agent\n100 người dùng ảo"]
    vals = [211, 438]
    bars = ax.bar(labels, vals, 0.5, color=["#2563eb", "#059669"])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 8, f"{v} ms", ha="center", fontweight="bold")
    ax.axhline(500, color="#dc2626", ls=":", lw=1.4)
    ax.text(1.28, 508, "Ngưỡng p95 đặt trước: 500 ms", color="#dc2626", fontsize=8, ha="right")
    ax.set_ylim(0, 600)
    ax.set_ylabel("Độ trễ p95 (ms)")
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "hinh-5-12-kiem-thu-tai.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig_cost()
    fig_mix()
    fig_pareto(False)
    fig_pareto(True)
    fig_load()
    print("saved to", OUT)
