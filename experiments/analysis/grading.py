"""Chấm tự động closed-QA: so khớp response với expected_answer theo match_type.

Dùng chung cho validate_prompts / test / decision_rule để luật chấm chỉ có 1 nơi.
Chuẩn hóa: Unicode NFC + hạ chữ thường (không bỏ dấu tiếng Việt — bỏ dấu sẽ làm
"Có" khớp nhầm "cô"/"cơ", "Chi" khớp nhầm "chị").
"""
import re
import unicodedata

MATCH_TYPES = ("exact", "contains", "regex")


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold().strip()


def _strip_edges(text: str) -> str:
    """Bỏ ký tự không phải chữ/số ở hai đầu (dấu chấm, **, ngoặc...)."""
    return re.sub(r"^[\W_]+|[\W_]+$", "", text)


def is_correct(response: str, expected_answer: str, match_type: str) -> bool:
    resp = normalize(response)
    expected = normalize(expected_answer)
    if match_type == "exact":
        return _strip_edges(resp) == _strip_edges(expected)
    if match_type == "contains":
        return expected in resp
    if match_type == "regex":
        # Không dùng `expected` đã casefold: casefold sẽ đổi \W thành \w, \D thành \d...
        pattern = unicodedata.normalize("NFC", expected_answer)
        return re.search(pattern, resp, flags=re.UNICODE | re.IGNORECASE) is not None
    raise ValueError(f"match_type không hợp lệ: {match_type!r}")
