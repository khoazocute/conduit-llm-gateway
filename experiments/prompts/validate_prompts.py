"""Kiểm tra prompts.json đúng SCHEMA.md. Chạy:
    PYTHONIOENCODING=utf-8 python experiments/prompts/validate_prompts.py
Thoát mã 1 nếu có lỗi (dùng được trong CI).

Bộ đề mới (D10, 2026-10-14): 4 bộ benchmark công khai, 10 item/bộ = 40 item, 0-shot.
Bộ 30 prompt tiếng Việt cũ nằm ở prompts-vi-30.json (phép thử nhạy ngôn ngữ, validate
bằng --vi).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
PROMPTS_FILE = HERE / "prompts.json"
VI_FILE = HERE / "prompts-vi-30.json"

EXPECTED_COUNTS = {"mmlu": 10, "gsm8k": 10, "humaneval": 10, "ifeval": 10}
METRIC_OF = {
    "mmlu": "accuracy_letter",
    "gsm8k": "exact_match_number",
    "humaneval": "pass_at_1",
    "ifeval": "ifeval_strict_prompt",
}
MMLU_LETTERS = ("A", "B", "C", "D")

# Schema cu (prompts-vi-30.json)
VI_COUNTS = {"closed_qa": 12, "code": 6, "open_ended": 12}
VI_MATCH_TYPES = ("exact", "contains", "regex")


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    for group in data:
        if group not in EXPECTED_COUNTS:
            errors.append(f"nhóm lạ '{group}' — chỉ cho phép {tuple(EXPECTED_COUNTS)}")

    for group, count in EXPECTED_COUNTS.items():
        items = data.get(group)
        if not isinstance(items, list):
            errors.append(f"thiếu nhóm '{group}'")
            continue
        if len(items) != count:
            errors.append(f"nhóm '{group}' cần {count} item, đang có {len(items)}")

        for item in items:
            pid = item.get("id")
            if not pid or not isinstance(pid, str):
                errors.append(f"[{group}] có item thiếu id")
                continue
            if pid in seen_ids:
                errors.append(f"id trùng: {pid}")
            seen_ids.add(pid)

            if not str(item.get("prompt", "")).strip():
                errors.append(f"{pid}: prompt rỗng")
            if item.get("metric") != METRIC_OF[group]:
                errors.append(f"{pid}: metric phải là '{METRIC_OF[group]}', đang là {item.get('metric')!r}")
            if "source_index" not in item:
                errors.append(f"{pid}: thiếu source_index (cần để tái lập mẫu)")

            # Truong bat buoc rieng cho tung metric - thieu la khong cham duoc
            if group == "mmlu":
                if item.get("expected_answer") not in MMLU_LETTERS:
                    errors.append(f"{pid}: expected_answer phải thuộc {MMLU_LETTERS}, "
                                  f"đang là {item.get('expected_answer')!r}")
                if item["prompt"].count("\n") < 2:
                    errors.append(f"{pid}: prompt MMLU phải có khối lựa chọn A-D nhiều dòng")
            elif group == "gsm8k":
                ans = str(item.get("expected_answer", "")).strip()
                if not re.fullmatch(r"-?\d+(\.\d+)?", ans):
                    errors.append(f"{pid}: expected_answer phải là một số, đang là {ans!r}")
            elif group == "humaneval":
                if not str(item.get("entry_point", "")).strip():
                    errors.append(f"{pid}: thiếu entry_point (cần để chạy pass@1)")
                if "def check(" not in str(item.get("test", "")):
                    errors.append(f"{pid}: thiếu bộ test gốc (cần 'def check(' để chạy pass@1)")
                if "def " not in str(item.get("signature_prompt", "")):
                    errors.append(f"{pid}: thiếu signature_prompt (cần để ghép code khi model chỉ trả về thân hàm)")
            elif group == "ifeval":
                ids = item.get("instruction_id_list")
                if not isinstance(ids, list) or not ids:
                    errors.append(f"{pid}: instruction_id_list phải là list không rỗng")
                if not isinstance(item.get("kwargs"), list):
                    errors.append(f"{pid}: kwargs phải là list (có thể rỗng)")

    total = sum(len(data.get(g, [])) for g in EXPECTED_COUNTS)
    if total != 40:
        errors.append(f"tổng phải là 40 item, đang có {total}")
    return errors


def validate_vi(data: dict) -> list[str]:
    """Schema cũ của bộ 30 prompt tiếng Việt — giữ để bộ thử nhạy ngôn ngữ còn dùng được."""
    errors: list[str] = []
    seen: set[str] = set()
    for group, count in VI_COUNTS.items():
        items = data.get(group)
        if not isinstance(items, list):
            errors.append(f"thiếu nhóm '{group}'")
            continue
        if len(items) != count:
            errors.append(f"nhóm '{group}' cần {count} prompt, đang có {len(items)}")
        for item in items:
            pid = item.get("id")
            if not pid:
                errors.append(f"[{group}] có prompt thiếu id")
                continue
            if pid in seen:
                errors.append(f"id trùng: {pid}")
            seen.add(pid)
            if not str(item.get("prompt", "")).strip():
                errors.append(f"{pid}: prompt rỗng")
            if group == "closed_qa":
                if not str(item.get("expected_answer", "")).strip():
                    errors.append(f"{pid}: closed_qa bắt buộc có expected_answer")
                if item.get("match_type") not in VI_MATCH_TYPES:
                    errors.append(f"{pid}: match_type phải thuộc {VI_MATCH_TYPES}")
                elif item["match_type"] == "regex":
                    try:
                        re.compile(item["expected_answer"])
                    except re.error as exc:
                        errors.append(f"{pid}: regex không hợp lệ ({exc})")
    return errors


if __name__ == "__main__":
    vi = "--vi" in sys.argv
    path = VI_FILE if vi else PROMPTS_FILE
    data = json.loads(path.read_text(encoding="utf-8"))
    problems = validate_vi(data) if vi else validate(data)
    if problems:
        print(f"{path.name} KHÔNG hợp lệ:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    if vi:
        print("prompts-vi-30.json hợp lệ: 12 closed_qa + 6 code + 12 open_ended = 30 prompt "
              "(bộ thử nhạy ngôn ngữ, không phải bộ đánh giá chính).")
    else:
        print("prompts.json hợp lệ: 10 mmlu + 10 gsm8k + 10 humaneval + 10 ifeval = 40 item, "
              "id duy nhất, đủ trường để chấm tự động.")
