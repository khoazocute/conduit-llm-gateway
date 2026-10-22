"""Mở rộng bộ đề từ 10 lên 20 item/bộ theo D14 (đăng ký trước, `docs/roadmap.md` mục 4).

Không lấy mẫu mới: dùng **đúng** seed `20261014` và `seed_offset` từng bộ, chỉ đổi `k`
từ 10 → 20. 10 index cũ của cả 4 bộ là **tập con thật** của mẫu k=20, nên 360 lượt đã
chạy vẫn hợp lệ và script này chỉ dựng **40 item mới**.

Ba chỗ dễ sai âm thầm mà script chặn cứng (abort chứ không cảnh báo):

1. **Gán lại ID.** Sinh lại thẳng với `N_PER_SET=20` sẽ dịch 36/40 ID (vd. `mmlu_01`
   nhảy từ `source_index` 1044 sang 917) → 360 lượt cũ bị ghép với đề khác. Nên 40 item
   cũ giữ **nguyên văn**, item mới đánh `*_11..*_20` (D14 ràng buộc 3).
2. **Mẫu cũ không còn là tập con.** Nếu vì lý do nào đó `set(idx10) ⊆ set(idx20)` sai thì
   gộp 2 đợt là so hai bộ đề khác nhau → dừng (D14 ràng buộc 2).
3. **Dữ liệu nguồn thượng nguồn đã đổi.** Script dựng lại 40 item cũ bằng chính code
   hiện tại rồi **so khớp từng ký tự** với `prompts.json`. Lệch một ký tự là dừng — vừa
   chứng minh refactor `build_prompts.py` không đổi hành vi, vừa phát hiện dataset
   thượng nguồn bị sửa.

**KHÔNG** tính lại ngưỡng `prompt_len` của Portkey (D14 ràng buộc 4): ngưỡng là một phần
cấu hình của nhánh Portkey, tính lại theo phân bố 80 item là đổi nhánh giữa thí nghiệm
khiến 2 đợt không gộp được.

Chạy (chỉ gọi dataset server, KHÔNG gọi LLM, không tốn tiền):
  PYTHONIOENCODING=utf-8 python experiments/prompts/extend_prompts.py
  ... --dry-run     # chỉ kiểm + in, không ghi file
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_prompts as bp  # noqa: E402

PROMPTS_FILE = HERE / "prompts.json"
MANIFEST_FILE = HERE / "manifest.json"

N_NEW = 20          # k mới
SEED_OFFSETS = {"gsm8k": 1, "humaneval": 2, "ifeval": 3, "mmlu": 4}


def fail(msg: str) -> None:
    sys.exit(f"\nDỪNG: {msg}")


def plan() -> dict[str, dict]:
    """Tính index đợt mở rộng cho từng bộ + kiểm ràng buộc tập con."""
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    if manifest["seed"] != bp.SEED:
        fail(f"seed lệch: manifest {manifest['seed']} vs build_prompts {bp.SEED}")

    out = {}
    for name, offset in SEED_OFFSETS.items():
        meta = manifest["sets"][name]
        n_total = meta["n_total"]
        old = sorted(meta["indices"])
        if len(old) != 10:
            fail(f"{name}: manifest ghi {len(old)} index, kỳ vọng 10")

        rng = random.Random(bp.SEED + offset)
        new_k = sorted(rng.sample(range(n_total), N_NEW))

        if not set(old) <= set(new_k):
            missing = sorted(set(old) - set(new_k))
            fail(f"{name}: 10 index cũ KHÔNG phải tập con của mẫu k={N_NEW} "
                 f"(thiếu {missing}) → gộp 2 đợt là so hai bộ đề khác nhau")

        added = sorted(set(new_k) - set(old))
        if len(added) != N_NEW - 10:
            fail(f"{name}: ra {len(added)} index mới, kỳ vọng {N_NEW - 10}")

        out[name] = {"n_total": n_total, "old": old, "all": new_k, "added": added}
        print(f"  {name:10s} n={n_total:6d}  cũ {len(old)} + mới {len(added)} = {len(new_k)}")
    return out


def build(name: str, indices: list[int], id_start: int) -> tuple[list[dict], dict]:
    """Dựng item bằng CHÍNH builder của build_prompts.py (không viết lại logic)."""
    bp.INDEX_OVERRIDE = {name: indices}
    bp.ID_START = id_start
    try:
        return bp.BUILDERS[name]()
    finally:
        bp.INDEX_OVERRIDE = {}
        bp.ID_START = 1


def check_old_unchanged(name: str, old_idx: list[int], existing: list[dict]) -> None:
    """Dựng lại 40 item cũ rồi so khớp từng ký tự với prompts.json."""
    rebuilt, _ = build(name, old_idx, 1)
    if len(rebuilt) != len(existing):
        fail(f"{name}: dựng lại ra {len(rebuilt)} item, prompts.json có {len(existing)}")
    for a, b in zip(rebuilt, existing):
        if a != b:
            diff = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
            fail(f"{name}/{b.get('id')}: dựng lại KHÁC prompts.json ở trường {diff}\n"
                 f"  dựng lại: {json.dumps({k: a.get(k) for k in diff}, ensure_ascii=False)[:300]}\n"
                 f"  đang có : {json.dumps({k: b.get(k) for k in diff}, ensure_ascii=False)[:300]}")
    print(f"  {name:10s} 10 item cũ dựng lại KHỚP từng ký tự")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="chỉ kiểm, không ghi file")
    args = ap.parse_args()

    prompts = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))

    print(f"D14 — mở rộng 10 → {N_NEW} item/bộ. Seed {bp.SEED}, giữ nguyên seed_offset.\n")
    print("1) Tính index đợt mở rộng + kiểm ràng buộc tập con:")
    pl = plan()

    print("\n2) Kiểm 40 item cũ không đổi (chứng minh refactor + dataset nguồn chưa đổi):")
    for name in SEED_OFFSETS:
        check_old_unchanged(name, pl[name]["old"], prompts[name])

    print("\n3) Dựng 40 item mới (ID bắt đầu từ 11):")
    new_items: dict[str, list[dict]] = {}
    for name in SEED_OFFSETS:
        items, _ = build(name, pl[name]["added"], 11)
        ids = [it["id"] for it in items]
        want = [f"{name}_{i:02d}" for i in range(11, 11 + len(pl[name]["added"]))]
        if ids != want:
            fail(f"{name}: ID mới ra {ids}, kỳ vọng {want}")
        clash = set(ids) & {it["id"] for it in prompts[name]}
        if clash:
            fail(f"{name}: ID mới trùng ID cũ: {sorted(clash)}")
        got_idx = [it["source_index"] for it in items]
        if got_idx != pl[name]["added"]:
            fail(f"{name}: source_index ra {got_idx}, kỳ vọng {pl[name]['added']}")
        new_items[name] = items
        print(f"  {name:10s} {ids[0]}..{ids[-1]}  source_index {got_idx}")

    if args.dry_run:
        print("\n--dry-run: không ghi file. Mọi phép kiểm đã qua.")
        return

    print("\n4) Ghi file:")
    for name in SEED_OFFSETS:
        prompts[name] = prompts[name] + new_items[name]
        meta = manifest["sets"][name]
        meta["indices_phase3"] = pl[name]["old"]        # 10 item đã chạy 360 lượt
        meta["indices_extension"] = pl[name]["added"]   # 10 item đợt mở rộng
        meta["indices"] = pl[name]["all"]
        meta["n_sampled"] = len(prompts[name])
    PROMPTS_FILE.write_text(json.dumps(prompts, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")

    lens = [len(it["prompt"]) for items in prompts.values() for it in items]
    lens.sort()
    manifest["n_per_set"] = N_NEW
    manifest["n_total"] = sum(len(v) for v in prompts.values())
    manifest["extension_d14"] = {
        "decided_on": "2026-10-20",
        "why": ("cổng 80% không phân giải được ở cỡ mẫu 40 item: LiteLLM 81,7%, CI95 "
                "[74,7%; 88,6%] theo lượt và [69,7%; 93,7%] theo item, đều chứa 80%"),
        "method": f"cùng seed {bp.SEED} và cùng seed_offset, chỉ đổi k từ 10 sang {N_NEW}",
        "old_items_still_valid": ("10 index cũ của cả 4 bộ là tập con thật của mẫu k=20, "
                                  "đã kiểm; 360 lượt đã chạy không phải chạy lại"),
        "ids_not_reassigned": ("40 item cũ giữ nguyên ID; item mới đánh *_11..*_20. Sinh "
                               "lại thẳng với N_PER_SET=20 sẽ dịch 36/40 ID và ghép sai "
                               "dữ liệu cũ một cách âm thầm"),
        "portkey_thresholds_unchanged": ("giữ 211/385 khóa 14/10 — ngưỡng là cấu hình của "
                                         "nhánh Portkey, tính lại là đổi nhánh giữa thí "
                                         "nghiệm nên 2 đợt không gộp được"),
    }
    # Phan bo do dai cua 80 item - ghi de truy vet, KHONG dung de tinh lai nguong.
    manifest["prompt_length_chars_80_items"] = {
        "note": "CHỈ để truy vết. Ngưỡng prompt_len của Portkey KHÔNG tính lại (D14).",
        "min": lens[0], "median": lens[len(lens) // 2], "max": lens[-1],
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")

    print(f"  prompts.json  : {manifest['n_total']} item "
          f"({' + '.join(f'{len(v)} {k}' for k, v in prompts.items())})")
    print(f"  manifest.json : n_per_set={N_NEW}, đã ghi indices_phase3 / indices_extension")
    print("\nXong. Ngưỡng prompt_len của Portkey GIỮ NGUYÊN 211/385 (D14 ràng buộc 4).")
    print("Bước tiếp: validate_prompts.py, rồi chạy 40 item mới × 3 proxy × 3 lần = 360 lượt.")


if __name__ == "__main__":
    main()
