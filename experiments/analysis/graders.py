"""Bộ chấm tự động cho 4 bộ benchmark (H7, D10 — xem docs/benchmark-survey.md mục 3).

Chạy OFFLINE, sau khi runner đã thu output — không chấm trong lúc chạy. Lý do: `pass@1`
phải chạy code trong sandbox và IFEval phải chạy verifier, nên thu output và chấm điểm
tách nhau; một bộ chấm chưa xong vẫn không chặn việc chạy thí nghiệm.

Mỗi hàm trả về `GradeResult(passed, score, detail)`:
  - `passed`  bool  — dùng cho bước 1 của luật quyết định (cổng 80%)
  - `score`   float — điểm liên tục khi metric có (IFEval instruction-level), nếu không thì 0/1
  - `detail`  dict  — vì sao, để truy vết khi đối chiếu tay

IFEval dùng **verifier chính thức** của paper, vendor nguyên văn ở
`experiments/analysis/vendor/instruction_following_eval/` (Apache-2.0).
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "vendor"))

# Dòng chỉ thị đã thêm vào prompt HumanEval (build_prompts.py) — cần để cắt khỏi response
# nếu model lặp lại nó.
HUMANEVAL_INSTR = "Complete the function above. Reply with the complete function implementation only."
HUMANEVAL_TIMEOUT = 15  # giây/bài


@dataclass
class GradeResult:
    passed: bool
    score: float
    detail: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------- MMLU

_MMLU_PATTERNS = (
    r"^\s*\(?([ABCD])\)?\s*[.):\-]?\s*$",            # ca ly tuong: chi 1 chu cai
    r"(?:answer|đáp án)\s*(?:is|:|là)?\s*\(?([ABCD])\)?\b",
    r"^\s*\(?([ABCD])\)?[.):\-\s]",                   # bat dau bang chu cai roi giai thich
    r"\b([ABCD])\b",                                  # cuoi cung: chu cai don le bat ky
)


def extract_mmlu_letter(response: str) -> str | None:
    if not response:
        return None
    text = response.strip()
    for pat in _MMLU_PATTERNS:
        m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).upper()
    return None


def grade_mmlu(response: str | None, item: dict[str, Any]) -> GradeResult:
    got = extract_mmlu_letter(response or "")
    want = str(item["expected_answer"]).strip().upper()
    ok = got == want
    return GradeResult(ok, 1.0 if ok else 0.0, {"extracted": got, "expected": want})


# ---------------------------------------------------------------- GSM8K

_NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def extract_last_number(response: str) -> str | None:
    """Quy ước 0-shot phổ biến: lấy SỐ CUỐI CÙNG trong câu trả lời.

    Không phải quy định của paper — xem docs/benchmark-survey.md mục 3, đây là 1 trong 3
    chỗ cần đối chiếu tay.
    """
    if not response:
        return None
    nums = _NUMBER.findall(response)
    if not nums:
        return None
    return nums[-1].replace(",", "")


def grade_gsm8k(response: str | None, item: dict[str, Any]) -> GradeResult:
    got = extract_last_number(response or "")
    want = str(item["expected_answer"]).strip().replace(",", "")
    ok = False
    if got is not None:
        try:
            ok = abs(float(got) - float(want)) < 1e-9
        except ValueError:
            ok = got == want
    return GradeResult(ok, 1.0 if ok else 0.0, {"extracted": got, "expected": want})


# ---------------------------------------------------------------- HumanEval (pass@1)

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S | re.IGNORECASE)


def extract_code(response: str, entry_point: str) -> str:
    """Lấy code từ câu trả lời: ưu tiên khối ```...```, nếu không có thì lấy nguyên văn."""
    if not response:
        return ""
    blocks = _FENCE.findall(response)
    if blocks:
        # Khối nào có đúng hàm cần viết thì lấy khối đó, không thì lấy khối đầu.
        for b in blocks:
            if f"def {entry_point}" in b:
                return b
        return blocks[0]
    return response.replace(HUMANEVAL_INSTR, "")


def grade_humaneval(response: str | None, item: dict[str, Any]) -> GradeResult:
    """pass@1: ghép code model sinh ra với BỘ TEST GỐC của bài rồi chạy.

    ⚠️ Chạy code do model sinh ra trong subprocess có timeout, thư mục tạm. KHÔNG phải
    sandbox đầy đủ (không chặn mạng/filesystem) — harness chính thức của OpenAI cũng
    thực thi code như vậy và kèm cảnh báo tương tự. Ghi vào phần giới hạn của báo cáo.
    """
    entry = item["entry_point"]
    code = extract_code(response or "", entry)
    if not code.strip():
        return GradeResult(False, 0.0, {"reason": "không trích được code nào"})

    # Model co the chi tra ve than ham -> ghep lai voi signature goc.
    if f"def {entry}" not in code:
        code = item["signature_prompt"] + "\n" + code

    program = f"{code}\n\n{item['test']}\n\ncheck({entry})\n"
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "candidate.py"
        f.write_text(program, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(f)],
                capture_output=True, text=True, timeout=HUMANEVAL_TIMEOUT, cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return GradeResult(False, 0.0, {"reason": f"timeout > {HUMANEVAL_TIMEOUT}s"})
    ok = proc.returncode == 0
    detail: dict[str, Any] = {"returncode": proc.returncode}
    if not ok:
        detail["stderr_tail"] = (proc.stderr or "")[-400:]
    return GradeResult(ok, 1.0 if ok else 0.0, detail)


# ---------------------------------------------------------------- IFEval

def _registry():
    from instruction_following_eval import instructions_registry  # noqa: PLC0415
    return instructions_registry.INSTRUCTION_DICT


def grade_ifeval(response: str | None, item: dict[str, Any]) -> GradeResult:
    """Chạy verifier CHÍNH THỨC cho từng `instruction_id` của item.

    `passed` = **prompt-level strict**: đạt chỉ khi MỌI ràng buộc của item đều được tuân
    thủ. Chọn mức prompt-level vì cổng ở bước 1 của luật quyết định là nhị phân "item
    đạt/không", khớp với 3 bộ còn lại.
    `score` = **instruction-level strict**: tỷ lệ ràng buộc tuân thủ được — báo cáo thêm,
    không dùng cho cổng.
    """
    text = response or ""
    reg = _registry()
    ids = item["instruction_id_list"]
    kwargs_list = item.get("kwargs") or [{}] * len(ids)
    per: list[dict[str, Any]] = []

    for iid, kw in zip(ids, kwargs_list):
        cls = reg.get(iid)
        if cls is None:
            per.append({"id": iid, "followed": False, "error": "không có verifier"})
            continue
        try:
            inst = cls(iid)
            inst.build_description(**{k: v for k, v in (kw or {}).items() if v is not None})
            # Verifier chinh thuc coi response rong la khong theo.
            followed = bool(text.strip()) and bool(inst.check_following(text))
            per.append({"id": iid, "followed": followed})
        except Exception as exc:  # verifier loi thi ghi lai, khong am tham cho la dat
            per.append({"id": iid, "followed": False, "error": f"{type(exc).__name__}: {exc}"})

    n = len(per)
    followed_n = sum(1 for p in per if p["followed"])
    return GradeResult(
        passed=(n > 0 and followed_n == n),
        score=(followed_n / n if n else 0.0),
        detail={"instruction_level": followed_n / n if n else 0.0,
                "followed": followed_n, "total": n, "per_instruction": per},
    )


# ---------------------------------------------------------------- dispatch

GRADERS = {
    "accuracy_letter": grade_mmlu,
    "exact_match_number": grade_gsm8k,
    "pass_at_1": grade_humaneval,
    "ifeval_strict_prompt": grade_ifeval,
}


def grade(response: str | None, item: dict[str, Any]) -> GradeResult:
    """Chấm 1 lượt theo `item["metric"]`. Metric lạ thì nổ, không âm thầm cho 0."""
    metric = item.get("metric")
    fn = GRADERS.get(metric)
    if fn is None:
        raise ValueError(f"metric không hỗ trợ: {metric!r} (item {item.get('id')})")
    return fn(response, item)
