"""Kiểm tra prompts.json đúng SCHEMA.md. Chạy: python experiments/prompts/validate_prompts.py
Thoát mã 1 nếu có lỗi (dùng được trong CI)."""
import json
import re
import sys
from pathlib import Path

PROMPTS_FILE = Path(__file__).parent / "prompts.json"
EXPECTED_COUNTS = {"closed_qa": 12, "code": 6, "open_ended": 12}
MATCH_TYPES = ("exact", "contains", "regex")


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    for group, count in EXPECTED_COUNTS.items():
        items = data.get(group)
        if not isinstance(items, list):
            errors.append(f"thiếu nhóm '{group}'")
            continue
        if len(items) != count:
            errors.append(f"nhóm '{group}' cần {count} prompt, đang có {len(items)}")

        for item in items:
            pid = item.get("id")
            if not pid or not isinstance(pid, str):
                errors.append(f"[{group}] có prompt thiếu id")
                continue
            if pid in seen_ids:
                errors.append(f"id trùng: {pid}")
            seen_ids.add(pid)
            if not str(item.get("prompt", "")).strip():
                errors.append(f"{pid}: prompt rỗng")

            has_answer = "expected_answer" in item or "match_type" in item
            if group == "closed_qa":
                if not str(item.get("expected_answer", "")).strip():
                    errors.append(f"{pid}: closed_qa bắt buộc có expected_answer")
                if item.get("match_type") not in MATCH_TYPES:
                    errors.append(f"{pid}: match_type phải thuộc {MATCH_TYPES}")
                elif item["match_type"] == "regex":
                    try:
                        re.compile(item["expected_answer"])
                    except re.error as exc:
                        errors.append(f"{pid}: regex không hợp lệ ({exc})")
            elif group == "open_ended" and has_answer:
                errors.append(f"{pid}: open_ended không có expected_answer/match_type")
            elif group == "code" and has_answer and item.get("match_type") not in MATCH_TYPES:
                errors.append(f"{pid}: match_type phải thuộc {MATCH_TYPES}")

    total = sum(len(data.get(g, [])) for g in EXPECTED_COUNTS)
    if total != 30:
        errors.append(f"tổng phải là 30 prompt, đang có {total}")
    return errors


if __name__ == "__main__":
    problems = validate(json.loads(PROMPTS_FILE.read_text(encoding="utf-8")))
    if problems:
        print("prompts.json KHÔNG hợp lệ:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("prompts.json hợp lệ: 12 closed_qa + 6 code + 12 open_ended = 30 prompt, id duy nhất.")
