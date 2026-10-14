"""Tải 4 bộ benchmark từ nguồn chính thức, lấy mẫu 10 item/bộ bằng seed cố định,
sinh prompts.json + manifest.json (D10, xem docs/experiment-design.md mục 5).

Chạy:  PYTHONIOENCODING=utf-8 python experiments/prompts/build_prompts.py

Tái lập được: manifest.json ghi URL nguồn, sha256 file đã tải, tổng số row, seed,
và index đã chọn — chạy lại cùng seed ra đúng 40 item đó.

0-shot (D10): KHÔNG dùng few-shot của protocol gốc. Lý do: few-shot làm prompt rất
dài -> nhánh Portkey định tuyến theo metadata.prompt_len sẽ đẩy mọi câu sang model
đắt, heuristic mất nghĩa. Nhóm không so với điểm công bố, chỉ so GIỮA 3 proxy trên
cùng bộ đề. Mọi chỗ lệch khỏi protocol gốc được ghi ở PROMPT_NOTES và phải nêu
trong báo cáo.
"""
import gzip
import hashlib
import io
import json
import random
import sys
from datetime import date
from pathlib import Path

import requests

HERE = Path(__file__).parent
CACHE = HERE / ".cache"
SEED = 20261014  # ngày chốt bộ đề
N_PER_SET = 10
TIMEOUT = 60

SOURCES = {
    "gsm8k": {
        "url": "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl",
        "paper": "Cobbe et al. 2021, Training Verifiers to Solve Math Word Problems (arXiv:2110.14168)",
        "repo": "openai/grade-school-math",
        "split": "test",
        "metric": "exact_match_number",
        "license": "MIT",
    },
    "humaneval": {
        "url": "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz",
        "paper": "Chen et al. 2021, Evaluating Large Language Models Trained on Code (arXiv:2107.03374)",
        "repo": "openai/human-eval",
        "split": "test (bộ duy nhất, 164 bài)",
        "metric": "pass_at_1",
        "license": "MIT",
    },
    "ifeval": {
        "url": "https://raw.githubusercontent.com/google-research/google-research/master/instruction_following_eval/data/input_data.jsonl",
        "paper": "Zhou et al. 2023, Instruction-Following Evaluation for Large Language Models (arXiv:2311.07911)",
        "repo": "google-research/google-research (instruction_following_eval)",
        "split": "input_data (bộ duy nhất)",
        "metric": "ifeval_strict_prompt",
        "license": "Apache-2.0",
    },
    "mmlu": {
        # Dùng datasets-server API của HF thay vì tar gốc 166MB của Hendrycks.
        "url": "https://datasets-server.huggingface.co/rows?dataset=cais%2Fmmlu&config=all&split=test",
        "paper": "Hendrycks et al. 2021, Measuring Massive Multitask Language Understanding (arXiv:2009.03300)",
        "repo": "cais/mmlu (HuggingFace)",
        "split": "all/test",
        "metric": "accuracy_letter",
        "license": "MIT",
    },
}

# Chỗ lệch khỏi protocol gốc - phải nêu trong báo cáo (docs/benchmark-survey.md).
PROMPT_NOTES = {
    "mmlu": (
        "0-shot thay vì 5-shot của paper gốc. Giữ layout Hendrycks (câu hỏi + 4 lựa chọn A-D) "
        "nhưng thêm 1 dòng chỉ thị 'Answer with the letter only' — cần cho chat model, vì "
        "protocol gốc thiết kế cho completion model có few-shot dẫn dắt định dạng."
    ),
    "gsm8k": (
        "0-shot thay vì 8-shot CoT của paper gốc. Prompt là câu hỏi NGUYÊN VĂN, không thêm chỉ "
        "thị nào. Chấm bằng cách trích số cuối cùng trong câu trả lời, so với số sau '####' "
        "trong đáp án gốc."
    ),
    "humaneval": (
        "Prompt gốc (signature + docstring) giữ nguyên, thêm 1 dòng chỉ thị trả về hàm hoàn "
        "chỉnh — cần cho chat model, vì protocol gốc là completion thuần. pass@1 chạy đúng "
        "bộ test gốc của từng bài, temperature 0."
    ),
    "ifeval": (
        "Prompt NGUYÊN VĂN, tuyệt đối không thêm gì — IFEval kiểm tra chính việc tuân thủ chỉ "
        "thị, thêm chữ nào cũng có thể phá ràng buộc đang được kiểm (vd. ràng buộc về số từ, "
        "về từ bị cấm)."
    ),
}

MMLU_LETTERS = ["A", "B", "C", "D"]


def fetch(name: str, url: str) -> bytes:
    """Tải (có cache) rồi trả bytes thô, để sha256 tính trên đúng cái đã dùng."""
    CACHE.mkdir(exist_ok=True)
    ext = ".jsonl.gz" if url.endswith(".gz") else ".json" if "datasets-server" in url else ".jsonl"
    path = CACHE / f"{name}{ext}"
    if path.exists():
        print(f"  {name}: dùng cache {path.name}")
        return path.read_bytes()
    print(f"  {name}: tải {url[:80]}...")
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    path.write_bytes(r.content)
    return r.content


def read_jsonl(raw: bytes, gz: bool = False) -> list[dict]:
    if gz:
        raw = gzip.decompress(raw)
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def pick(n_total: int, seed_offset: int) -> list[int]:
    """Index đã chọn, sắp tăng dần để dễ đối chiếu tay."""
    rng = random.Random(SEED + seed_offset)
    return sorted(rng.sample(range(n_total), N_PER_SET))


def build_gsm8k() -> tuple[list[dict], dict]:
    raw = fetch("gsm8k", SOURCES["gsm8k"]["url"])
    rows = read_jsonl(raw)
    idx = pick(len(rows), 1)
    items = []
    for i, k in enumerate(idx, 1):
        row = rows[k]
        answer = row["answer"].split("####")[-1].strip().replace(",", "")
        items.append({
            "id": f"gsm8k_{i:02d}",
            "prompt": row["question"].strip(),
            "metric": "exact_match_number",
            "expected_answer": answer,
            "source_index": k,
        })
    return items, {"n_total": len(rows), "sha256": hashlib.sha256(raw).hexdigest(), "indices": idx}


def build_humaneval() -> tuple[list[dict], dict]:
    raw = fetch("humaneval", SOURCES["humaneval"]["url"])
    rows = read_jsonl(raw, gz=True)
    idx = pick(len(rows), 2)
    instr = "\n\nComplete the function above. Reply with the complete function implementation only."
    items = []
    for i, k in enumerate(idx, 1):
        row = rows[k]
        items.append({
            "id": f"humaneval_{i:02d}",
            "prompt": row["prompt"] + instr,
            "signature_prompt": row["prompt"],  # prompt goc, chua them dong chi thi
            "metric": "pass_at_1",
            "entry_point": row["entry_point"],
            "test": row["test"],
            "source_id": row["task_id"],
            "source_index": k,
        })
    return items, {"n_total": len(rows), "sha256": hashlib.sha256(raw).hexdigest(), "indices": idx}


def build_ifeval() -> tuple[list[dict], dict]:
    raw = fetch("ifeval", SOURCES["ifeval"]["url"])
    rows = read_jsonl(raw)
    idx = pick(len(rows), 3)
    items = []
    for i, k in enumerate(idx, 1):
        row = rows[k]
        items.append({
            "id": f"ifeval_{i:02d}",
            "prompt": row["prompt"],  # NGUYEN VAN - xem PROMPT_NOTES
            "metric": "ifeval_strict_prompt",
            "instruction_id_list": row["instruction_id_list"],
            "kwargs": row.get("kwargs", []),
            "source_key": row["key"],
            "source_index": k,
        })
    return items, {"n_total": len(rows), "sha256": hashlib.sha256(raw).hexdigest(), "indices": idx}


def build_mmlu() -> tuple[list[dict], dict]:
    base = SOURCES["mmlu"]["url"]
    head = json.loads(fetch("mmlu", f"{base}&offset=0&length=1").decode("utf-8"))
    n_total = head["num_rows_total"]
    idx = pick(n_total, 4)
    items, digest = [], hashlib.sha256()
    for i, k in enumerate(idx, 1):
        r = requests.get(f"{base}&offset={k}&length=1", timeout=TIMEOUT)
        r.raise_for_status()
        digest.update(r.content)
        row = json.loads(r.content)["rows"][0]["row"]
        choices = row["choices"]
        if len(choices) != 4:
            raise SystemExit(f"MMLU index {k}: cần đúng 4 lựa chọn, có {len(choices)}")
        block = "\n".join(f"{MMLU_LETTERS[j]}. {c}" for j, c in enumerate(choices))
        items.append({
            "id": f"mmlu_{i:02d}",
            "prompt": f"{row['question'].strip()}\n\n{block}\n\n"
                      "Answer with the letter only (A, B, C, or D).",
            "metric": "accuracy_letter",
            "expected_answer": MMLU_LETTERS[int(row["answer"])],
            "subject": row.get("subject"),
            "source_index": k,
        })
    return items, {"n_total": n_total, "sha256": digest.hexdigest(), "indices": idx}


BUILDERS = {"mmlu": build_mmlu, "gsm8k": build_gsm8k, "humaneval": build_humaneval, "ifeval": build_ifeval}


def main() -> None:
    print(f"Seed = {SEED}, {N_PER_SET} item/bộ\n")
    prompts, manifest_sets = {}, {}
    for name, fn in BUILDERS.items():
        items, meta = fn()
        prompts[name] = items
        manifest_sets[name] = {**SOURCES[name], **meta, "n_sampled": len(items),
                               "prompt_note": PROMPT_NOTES[name]}
        print(f"  {name}: {len(items)}/{meta['n_total']} item, sha256 {meta['sha256'][:16]}...")

    (HERE / "prompts.json").write_text(
        json.dumps(prompts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    lengths = {g: sorted(len(it["prompt"]) for it in items) for g, items in prompts.items()}
    all_len = sorted(l for v in lengths.values() for l in v)

    # Nguong metadata.prompt_len cho Portkey (H3, khoa 2026-10-14) - TINH O DAY chu khong
    # ghi tay vao manifest, vi script nay ghi de manifest.json moi lan chay.
    # Dung tercile cua phan bo that: dat so tron tuy y rat de lam 1 tier nhan 0 item ->
    # nhanh Portkey suy bien thanh "luon chon 1 model" va khong do duoc gi.
    n = len(all_len)
    t1 = all_len[round((1 / 3) * (n - 1))]
    t2 = all_len[round((2 / 3) * (n - 1))]
    split = {
        "cheap": sum(1 for x in all_len if x < t1),
        "mid": sum(1 for x in all_len if t1 <= x < t2),
        "expensive": sum(1 for x in all_len if x >= t2),
    }
    manifest = {
        "built_on": date.today().isoformat(),
        "seed": SEED,
        "n_per_set": N_PER_SET,
        "n_total": sum(len(v) for v in prompts.values()),
        "shot": "0-shot (D10) — xem prompt_note của từng bộ để biết chỗ lệch khỏi protocol gốc",
        "decoding": {"max_tokens": 512, "temperature": 0,
                     "note": "temperature 0 là yêu cầu của pass@1; dùng chung cho cả 4 bộ để nhất quán"},
        "sets": manifest_sets,
        "portkey_prompt_len_thresholds": {
            "unit": "ký tự của prompt",
            "cheap_below": t1,
            "expensive_at_or_above": t2,
            "tier_models": {"cheap": "gpt-4o-mini", "mid": "claude-haiku", "expensive": "claude-sonnet"},
            "derivation": "tercile của phân bố độ dài 40 item (cùng seed) — xem docs/routing-policy.md mục 7",
            "split": split,
            "locked_on": "2026-10-14",
        },
        "prompt_length_chars": {
            "per_set": {g: {"min": v[0], "median": v[len(v) // 2], "max": v[-1]} for g, v in lengths.items()},
            "all_40": {"min": all_len[0], "p25": all_len[len(all_len) // 4],
                       "median": all_len[len(all_len) // 2],
                       "p75": all_len[3 * len(all_len) // 4], "max": all_len[-1]},
        },
    }
    (HERE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"\nprompts.json: {manifest['n_total']} item")
    print("Phân bố độ dài prompt (ký tự) — dùng để chốt ngưỡng metadata.prompt_len cho Portkey:")
    for g, v in lengths.items():
        print(f"  {g:10s} min={v[0]:5d}  median={v[len(v)//2]:5d}  max={v[-1]:5d}")
    a = manifest["prompt_length_chars"]["all_40"]
    print(f"  {'TẤT CẢ':10s} min={a['min']:5d}  p25={a['p25']:5d}  median={a['median']:5d}"
          f"  p75={a['p75']:5d}  max={a['max']:5d}")
    print()
    print(f"Ngưỡng Portkey (tercile): < {t1} rẻ | {t1}-{t2 - 1} trung | >= {t2} đắt"
          f"  -> chia {split['cheap']}/{split['mid']}/{split['expensive']}")


if __name__ == "__main__":
    sys.exit(main())
