"""Các phương pháp chia đoạn (chunking) cho RAG (TASK-75).

Mọi chunker làm việc trên văn bản đã qua `normalize()` và trả về danh sách `Chunk` có vị trí ký tự.
Bất biến bắt buộc cho mọi đoạn `c` của văn bản `t`:

    normalize(t)[c.start_char:c.end_char] == c.text

Đánh giá truy hồi (TASK-76) dựa vào vị trí này để biết đoạn nào chứa bằng chứng, nên mọi chunker
chỉ được dời chỉ số, không được sửa chữ trong đoạn (không strip, không ghép tiêu đề vào text).
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

# Khoảng trắng bất kỳ trừ xuống dòng (dấu cách, tab,  , ...).
_INLINE_WHITESPACE = re.compile(r"[^\S\n]+")
_MANY_NEWLINES = re.compile(r"\n{3,}")


@dataclass
class Chunk:
    text: str
    index: int
    start_char: int  # vị trí bắt đầu trong văn bản đã normalize
    end_char: int  # vị trí kết thúc, không tính (giống slice Python)
    method: str  # "fixed" | "recursive" | "semantic" | "structure"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "text": self.text,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "method": self.method,
            "metadata": self.metadata,
        }


def normalize(text: str) -> str:
    """Chuẩn hóa văn bản nhưng GIỮ ranh giới dòng và đoạn văn.

    - Unicode NFC (tiếng Việt từ PDF/macOS hay ở dạng tổ hợp NFD, cùng chữ nhưng khác chuỗi).
    - `\\r\\n`, `\\r` -> `\\n`.
    - Trong một dòng: gộp khoảng trắng liên tiếp thành một dấu cách, bỏ khoảng trắng hai đầu dòng.
    - Từ 3 lần xuống dòng trở lên -> `\\n\\n` (ranh giới đoạn văn).
    - Bỏ khoảng trắng hai đầu cả văn bản.

    Hàm lũy đẳng: normalize(normalize(x)) == normalize(x).
    """
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_INLINE_WHITESPACE.sub(" ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return _MANY_NEWLINES.sub("\n\n", text).strip()


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    """Bỏ khoảng trắng hai đầu đoạn text[start:end] bằng cách dời chỉ số (không tạo chuỗi mới)."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _rfind_whitespace(text: str, lo: int, hi: int) -> int:
    """Vị trí khoảng trắng cuối cùng trong text[lo:hi], -1 nếu không có.

    Văn bản đã normalize chỉ còn hai loại khoảng trắng là " " và "\\n".
    """
    return max(text.rfind(" ", lo, hi), text.rfind("\n", lo, hi))


def _find_whitespace(text: str, lo: int, hi: int) -> int:
    """Vị trí khoảng trắng đầu tiên trong text[lo:hi], -1 nếu không có."""
    hits = [i for i in (text.find(" ", lo, hi), text.find("\n", lo, hi)) if i != -1]
    return min(hits) if hits else -1


def _validate_size_overlap(size: int, overlap: int) -> None:
    if size <= 0 or overlap < 0 or overlap >= size // 2:
        raise ValueError("Require size > 0 and 0 <= overlap < size/2")


# ---------------------------------------------------------------------------------------------
# 1. Cắt cố định
# ---------------------------------------------------------------------------------------------


def chunk_fixed(text: str, size: int = 1000, overlap: int = 150) -> list[Chunk]:
    """Chia theo số ký tự cố định, cắt ở ranh giới từ, hai đoạn liền nhau gối lên nhau tối đa `overlap` ký tự.

    Cùng thuật toán với `ingest.chunk_text` cũ, khác ở chỗ: giữ xuống dòng, trả về vị trí ký tự.
    Từ dài hơn nửa đoạn (ví dụ URL) thì cắt cứng.
    """
    _validate_size_overlap(size, overlap)

    text = normalize(text)
    length = len(text)
    chunks: list[Chunk] = []
    start = 0
    while start < length:
        # Đầu đoạn không nằm trên khoảng trắng, để không phí chỗ trong `size`.
        while start < length and text[start].isspace():
            start += 1
        if start >= length:
            break
        end = min(start + size, length)
        if end < length:
            # Lùi về khoảng trắng gần nhất (kể cả chính vị trí `end`), nhưng không lùi quá nửa đoạn.
            cut = _rfind_whitespace(text, start + size // 2, end + 1)
            if cut != -1:
                end = cut
        s, e = _trim(text, start, end)
        if s < e:
            chunks.append(Chunk(text[s:e], len(chunks), s, e, "fixed"))
        if end >= length:
            break
        # end >= start + size/2 và overlap < size/2 nên next_start > start: vòng lặp luôn tiến.
        next_start = end - overlap
        space = _find_whitespace(text, next_start, end)
        if space != -1:
            next_start = space + 1  # đoạn sau bắt đầu ở đầu một từ, không giữa từ
        start = next_start
    return chunks


# ---------------------------------------------------------------------------------------------
# 2. Cắt đệ quy
# ---------------------------------------------------------------------------------------------

# Thứ tự từ ranh giới "thô" đến "mịn": đoạn văn -> dòng -> câu -> từ.
RECURSIVE_SEPARATORS: tuple[str, ...] = ("\n\n", "\n", ". ", "? ", "! ", " ")


def _recursive_spans(
    text: str, start: int, end: int, size: int, overlap: int, separators: tuple[str, ...]
) -> list[tuple[int, int]]:
    """Thuật toán của LangChain `RecursiveCharacterTextSplitter._split_text`, giữ vị trí ký tự.

    1. Chọn dấu tách THÔ NHẤT có mặt trong khoảng, tách thành các mảnh cùng cấp.
    2. Mảnh vừa `size` -> để dành; các mảnh để dành LIỀN NHAU được gộp lại (`_merge_spans`).
    3. Gặp mảnh quá dài -> gộp xong nhóm đang để dành, rồi đệ quy RIÊNG mảnh đó với dấu tách mịn hơn.
       Vì vậy một đoạn không bao giờ trộn phần đầu của mảnh quá dài với mảnh vừa đứng trước nó.
    4. Hết dấu tách (vd một từ dài hơn size) -> cắt cứng theo size.

    Khác LangChain (có chủ ý): dấu tách dính vào mảnh BÊN TRÁI (LangChain mặc định dính vào mảnh bên
    phải), để câu giữ dấu chấm của nó; độ dài tính trên chữ gốc giữa hai đầu đoạn, không cộng dấu tách.
    """
    s, e = _trim(text, start, end)
    if s >= e:
        return []
    if e - s <= size:
        return [(s, e)]

    for level, sep in enumerate(separators):
        bounds: list[int] = []
        pos = text.find(sep, s, e)
        while pos != -1:
            cut = pos + len(sep)
            if cut < e:
                bounds.append(cut)
            pos = text.find(sep, cut, e)
        if bounds:
            break  # dấu tách thô nhất có trong khoảng
    else:
        hard = [_trim(text, i, min(i + size, e)) for i in range(s, e, size)]
        return [(a, b) for a, b in hard if a < b]

    finer = separators[level + 1:]
    result: list[tuple[int, int]] = []
    fitting: list[tuple[int, int]] = []  # các mảnh vừa size, liền nhau, chờ gộp
    prev = s
    for b in bounds + [e]:
        ps, pe = _trim(text, prev, b)
        prev = b
        if ps >= pe:
            continue
        if pe - ps <= size:
            fitting.append((ps, pe))
            continue
        if fitting:
            result.extend(_merge_spans(fitting, size, overlap))
            fitting = []
        result.extend(_recursive_spans(text, ps, pe, size, overlap, finer))
    if fitting:
        result.extend(_merge_spans(fitting, size, overlap))
    return result


def chunk_recursive(
    text: str,
    size: int = 1000,
    overlap: int = 150,
    separators: tuple[str, ...] = RECURSIVE_SEPARATORS,
) -> list[Chunk]:
    """Level 2 (Kamradt) = thuật toán `RecursiveCharacterTextSplitter` của LangChain (`_recursive_spans`).

    Tách bằng dấu tách thô nhất (đoạn văn), gộp các mảnh liền nhau cùng cấp cho gần `size`; chỉ mảnh
    nào quá dài mới bị tách tiếp bằng dấu mịn hơn (dòng -> câu -> từ), và được cắt RIÊNG.
    Gối đầu theo NGUYÊN MẢNH (như LangChain): đoạn mới mang theo các mảnh cuối của đoạn trước, tổng
    không quá `overlap` ký tự — luôn là câu/từ trọn vẹn; mảnh cuối dài hơn `overlap` thì không gối
    (khác cắt cố định, luôn gối gần đủ `overlap`).
    """
    _validate_size_overlap(size, overlap)
    if not separators:
        raise ValueError("separators must not be empty")

    text = normalize(text)
    spans = _recursive_spans(text, 0, len(text), size, overlap, tuple(separators))
    return [Chunk(text[s:e], i, s, e, "recursive") for i, (s, e) in enumerate(spans)]


def _merge_spans(
    pieces: list[tuple[int, int]], size: int, overlap: int = 0
) -> list[tuple[int, int]]:
    """Gộp tham lam các mảnh liền nhau (mỗi mảnh <= size) thành khoảng <= size.

    Gối đầu theo nguyên mảnh: khoảng mới mang theo các mảnh cuối của khoảng trước, tổng <= overlap.
    """
    merged: list[tuple[int, int]] = []
    current: list[tuple[int, int]] = []
    for piece in pieces:
        if current and piece[1] - current[0][0] > size:
            merged.append((current[0][0], current[-1][1]))
            # Không bao giờ giữ cả khoảng trước (bỏ current[0]), và phải còn chỗ cho mảnh mới.
            keep: list[tuple[int, int]] = []
            for prev in reversed(current[1:]):
                if current[-1][1] - prev[0] > overlap or piece[1] - prev[0] > size:
                    break
                keep.insert(0, prev)
            current = keep
        current.append(piece)
    if current:
        merged.append((current[0][0], current[-1][1]))
    return merged


# ---------------------------------------------------------------------------------------------
# 3. Cắt ngữ nghĩa (Kamradt, "5 Levels of Text Splitting", cấp 4)
# ---------------------------------------------------------------------------------------------

# Nhận danh sách chuỗi, trả về vector theo đúng thứ tự. Truyền từ ngoài vào để: service dùng embedding
# thật qua LiteLLM, test dùng embedding giả (không mạng, không phí).
EmbedFn = Callable[[list[str]], Sequence[Sequence[float]]]

# Ranh giới câu: khoảng trắng sau . ? ! hoặc xuống dòng (văn bản đã normalize).
_SENTENCE_GAP = re.compile(r"(?<=[.?!])[ \n]+|\n+")


def _sentence_spans(text: str, max_size: int) -> list[tuple[int, int]]:
    """Tách văn bản đã normalize thành câu (vị trí ký tự), cùng biểu thức `(?<=[.?!])\\s+` với bản gốc
    của Kamradt và `SemanticChunker` (LangChain). Câu dài hơn max_size -> chia thành vài mảnh gần
    max_size theo ranh giới từ (không chia thành từng từ lẻ)."""
    spans: list[tuple[int, int]] = []
    prev = 0
    for gap in list(_SENTENCE_GAP.finditer(text)) + [None]:
        end = gap.start() if gap else len(text)
        s, e = _trim(text, prev, end)
        if s < e:
            spans.extend(_recursive_spans(text, s, e, max_size, 0, (" ",)))
        if gap:
            prev = gap.end()
    return spans


def _cosine_distance(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 1.0
    return 1.0 - dot / (na * nb)


def _percentile(values: list[float], p: float) -> float:
    """Phân vị nội suy tuyến tính (giống numpy.percentile mặc định), để không phụ thuộc numpy."""
    xs = sorted(values)
    k = (len(xs) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def chunk_semantic(
    text: str,
    embed_fn: EmbedFn,
    *,
    breakpoint_percentile: float = 95,
    buffer: int = 1,
    min_size: int = 200,
    max_size: int = 1000,
) -> list[Chunk]:
    """Cắt ở chỗ nội dung đổi chủ đề, đo bằng khoảng cách embedding giữa các câu liền nhau.

    1. Tách câu. Mỗi câu ghép với `buffer` câu trước và sau thành một "cửa sổ" (giảm nhiễu do câu ngắn).
    2. Embedding mọi cửa sổ trong MỘT lần gọi `embed_fn` (D1: một lượt gọi có phí cho cả tài liệu).
    3. Khoảng cách cosine giữa hai cửa sổ liền nhau. Khoảng cách > phân vị `breakpoint_percentile`
       của mọi khoảng cách -> cắt ở đó (đổi chủ đề).
    4. Nhóm dài hơn `max_size` -> gộp lại theo câu cho vừa; nhóm ngắn hơn `min_size` -> gộp vào nhóm
       bên cạnh nếu tổng vẫn <= max_size.

    Không gối đầu. `metadata.sentences` = số câu trong đoạn.
    """
    if max_size <= 0 or min_size < 0 or min_size > max_size:
        raise ValueError("Require max_size > 0 and 0 <= min_size <= max_size")
    if not 0 <= breakpoint_percentile <= 100:
        raise ValueError("breakpoint_percentile must be in [0, 100]")
    if buffer < 0:
        raise ValueError("buffer must be >= 0")

    text = normalize(text)
    sentences = _sentence_spans(text, max_size)
    if not sentences:
        return []

    # Nhóm câu theo chủ đề: mỗi nhóm là danh sách chỉ số câu liền nhau.
    groups: list[list[int]] = [list(range(len(sentences)))]
    if len(sentences) >= 2:
        windows = []
        for i in range(len(sentences)):
            lo = max(0, i - buffer)
            hi = min(len(sentences) - 1, i + buffer)
            windows.append(text[sentences[lo][0]:sentences[hi][1]])
        vectors = list(embed_fn(windows))
        if len(vectors) != len(windows):
            raise ValueError(f"embed_fn returned {len(vectors)} vectors for {len(windows)} inputs")
        distances = [_cosine_distance(vectors[i], vectors[i + 1]) for i in range(len(vectors) - 1)]
        threshold = _percentile(distances, breakpoint_percentile)
        groups = []
        current = [0]
        for i, d in enumerate(distances):
            if d > threshold:  # cắt giữa câu i và i+1
                groups.append(current)
                current = []
            current.append(i + 1)
        groups.append(current)

    # Nhóm quá dài -> gộp theo câu cho vừa max_size.
    spans: list[tuple[int, int, int]] = []  # (start, end, số câu)
    for group in groups:
        for s, e in _merge_spans([sentences[i] for i in group], max_size):
            count = sum(1 for i in group if s <= sentences[i][0] and sentences[i][1] <= e)
            spans.append((s, e, count))

    # Nhóm quá ngắn -> gộp vào nhóm trước (hoặc nhóm sau, nếu là nhóm đầu) khi tổng vẫn vừa.
    merged: list[tuple[int, int, int]] = []
    for s, e, n in spans:
        if merged:
            ps, pe, pn = merged[-1]
            too_short = (pe - ps) < min_size or (e - s) < min_size
            if too_short and e - ps <= max_size:
                merged[-1] = (ps, e, pn + n)
                continue
        merged.append((s, e, n))

    return [
        Chunk(text[s:e], i, s, e, "semantic", {"sentences": n})
        for i, (s, e, n) in enumerate(merged)
    ]


# ---------------------------------------------------------------------------------------------
# 4. Cắt theo cấu trúc tài liệu (Document Specific Splitting, Kamradt cấp 3)
# ---------------------------------------------------------------------------------------------

# Markdown: "# Tiêu đề" ... "###### Tiêu đề".
_MD_HEADING = re.compile(r"^(#{1,6}) +(\S.*)$")
# Văn bản pháp luật/quy chế VN: "Chương I", "CHƯƠNG 2: ...", "Điều 5. ...". Sau số phải là dấu câu hoặc hết
# dòng, để dòng bị ngắt giữa câu kiểu "...quy định tại\nĐiều 5 của Luật này" KHÔNG bị nhận là đầu mục.
_LEGAL_HEADING = re.compile(
    r"^(Phần|PHẦN|Chương|CHƯƠNG|Mục|MỤC|Điều|ĐIỀU) +(\d+[a-z]?|[IVXLCDM]+)(?:[.:\-–]|$)"
)
_LEGAL_LEVEL = {"phần": 1, "chương": 2, "mục": 3, "điều": 4}
# Mục đánh số của bài báo/báo cáo: "1 Introduction", "2.1 Data", "3.2.1. Kết quả".
_NUMBERED_HEADING = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})\.? +(\S.*)$")
# Tên mục chuẩn đứng một mình trên một dòng.
_NAMED_HEADING = re.compile(
    r"^(?:abstract|introduction|related work|background|methods?|methodology|approach|"
    r"experiments?|experimental setup|results?|evaluation|discussion|conclusions?|limitations|"
    r"references|acknowledge?ments?|appendix|tóm tắt|giới thiệu|tổng quan|phương pháp|"
    r"thực nghiệm|kết quả|thảo luận|kết luận|tài liệu tham khảo):?$",
    re.IGNORECASE,
)


def _heading(line: str) -> tuple[int, str] | None:
    """(cấp, tiêu đề) nếu dòng là đầu mục, ngược lại None. Cấp nhỏ = mục lớn."""
    m = _MD_HEADING.match(line)
    if m:
        return len(m.group(1)), m.group(2)
    m = _LEGAL_HEADING.match(line)
    if m:
        return _LEGAL_LEVEL[m.group(1).lower()], line
    m = _NUMBERED_HEADING.match(line)
    if m:
        title = m.group(2)
        # Phân biệt với mục liệt kê "1. Hỏi rõ vị trí ứng tuyển.": tiêu đề ngắn, viết hoa đầu,
        # không kết thúc bằng dấu câu.
        if (len(line) <= 80 and title[0].isupper() and title[-1] not in ".:;,?!"
                and len(title.split()) <= 12):
            return m.group(1).count(".") + 1, line
        return None
    if _NAMED_HEADING.match(line):
        return 1, line.rstrip(":")
    return None


@dataclass
class _Section:
    start: int  # đầu dòng tiêu đề (hoặc 0 với phần mở đầu không có tiêu đề)
    body_start: int  # sau dòng tiêu đề
    end: int
    path: list[str]  # tiêu đề các cấp, từ mục lớn đến mục chứa nó


def _sections(text: str) -> list[_Section]:
    """Chia văn bản đã normalize thành các mục liền nhau, phủ kín văn bản."""
    sections = [_Section(0, 0, len(text), [])]  # phần mở đầu trước đầu mục đầu tiên
    stack: list[tuple[int, str]] = []
    in_code_fence = False
    pos = 0
    for line in text.split("\n"):
        line_start, line_end = pos, pos + len(line)
        pos = line_end + 1
        if line.startswith("```"):
            in_code_fence = not in_code_fence  # "# comment" trong khối code không phải tiêu đề
            continue
        if in_code_fence:
            continue
        found = _heading(line)
        if not found:
            continue
        level, title = found
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        sections[-1].end = line_start
        sections.append(_Section(line_start, line_end, len(text), [t for _, t in stack]))
    return [s for s in sections if _span_length(text, s.start, s.end) > 0]


def _span_length(text: str, start: int, end: int) -> int:
    s, e = _trim(text, start, end)
    return e - s


def _main_section(sections: list[_Section], start: int, end: int) -> _Section:
    """Mục mà đoạn [start, end) chứa nhiều NỘI DUNG nhất (không tính dòng tiêu đề)."""
    best, best_overlap = sections[0], -math.inf
    for sec in sections:
        if sec.start >= end:
            break
        if sec.end <= start:
            continue
        overlap = min(end, sec.end) - max(start, sec.body_start)
        if overlap > best_overlap:
            best, best_overlap = sec, overlap
    return best


def chunk_structure(
    text: str, size: int = 1000, overlap: int = 150, min_size: int = 200
) -> list[Chunk]:
    """Cắt tại đầu mục của tài liệu: mỗi mục (Markdown #, Chương/Điều, mục bài báo) là một đơn vị.

    1. Tìm đầu mục, chia văn bản thành các mục liền nhau (phần trước đầu mục đầu tiên là một mục riêng).
    2. Mục ngắn hơn `min_size` gộp với mục sau nếu tổng vẫn <= size. Mục chỉ có tiêu đề (ví dụ
       "Chương I" ngay trước "Điều 1") luôn gộp vào mục sau, để tiêu đề không đứng trơ một mình.
    3. Nhóm dài hơn `size` -> cắt đệ quy BÊN TRONG nhóm (gối đầu `overlap`), không vượt ranh giới mục.
    4. Không có đầu mục nào -> cả văn bản là một mục, kết quả giống hệt `chunk_recursive`.

    Tiêu đề KHÔNG ghép vào `text` (giữ bất biến vị trí); lưu ở `metadata.heading` (tiêu đề mục chính
    của đoạn) và `metadata.heading_path` (các cấp tiêu đề, ví dụ ["Chương I", "Điều 3"]).
    Đoạn đầu của mục vẫn chứa dòng tiêu đề vì đó là chữ gốc của tài liệu.
    """
    _validate_size_overlap(size, overlap)
    if not 0 <= min_size <= size:
        raise ValueError("Require 0 <= min_size <= size")

    text = normalize(text)
    sections = _sections(text)
    if not sections:
        return []

    # Gộp mục ngắn: mỗi nhóm là [start, end, có_nội_dung].
    groups: list[list] = []
    for sec in sections:
        has_body = _span_length(text, sec.body_start, sec.end) > 0
        if groups:
            g = groups[-1]
            if _span_length(text, g[0], g[1]) < min_size and (
                _span_length(text, g[0], sec.end) <= size or not g[2]
            ):
                g[1] = sec.end
                g[2] = g[2] or has_body
                continue
        groups.append([sec.start, sec.end, has_body])
    # Nhóm cuối quá ngắn -> gộp ngược vào nhóm trước nếu vừa.
    if (len(groups) >= 2 and _span_length(text, groups[-1][0], groups[-1][1]) < min_size
            and _span_length(text, groups[-2][0], groups[-1][1]) <= size):
        groups[-2][1] = groups.pop()[1]

    chunks: list[Chunk] = []
    for g_start, g_end, _ in groups:
        for s, e in _recursive_spans(text, g_start, g_end, size, overlap, RECURSIVE_SEPARATORS):
            sec = _main_section(sections, s, e)
            chunks.append(Chunk(
                text[s:e], len(chunks), s, e, "structure",
                {"heading": sec.path[-1] if sec.path else None, "heading_path": list(sec.path)},
            ))
    return chunks


# ---------------------------------------------------------------------------------------------
# Điểm vào chung (hợp đồng: chunk(document, method, params) -> [Chunk])
# ---------------------------------------------------------------------------------------------

# Tham số hợp lệ của từng phương pháp. Giá trị mặc định nằm ở chữ ký từng hàm chunk_*.
METHOD_PARAMS: dict[str, frozenset[str]] = {
    "fixed": frozenset({"size", "overlap"}),
    "recursive": frozenset({"size", "overlap"}),
    "semantic": frozenset({"breakpoint_percentile", "buffer", "min_size", "max_size"}),
    "structure": frozenset({"size", "overlap", "min_size"}),
}
DEFAULT_METHOD = "fixed"
# Trần độ dài đoạn: text-embedding-3-small nhận tối đa 8.191 token mỗi đầu vào; 8.000 ký tự an toàn
# cả với tiếng Việt (nhiều token hơn trên mỗi ký tự so với tiếng Anh).
MAX_CHUNK_CHARS = 8000


def chunk(
    text: str,
    method: str = DEFAULT_METHOD,
    params: dict | None = None,
    embed_fn: EmbedFn | None = None,
) -> list[Chunk]:
    """Gọi đúng chunker theo tên. Tham số lạ, sai kiểu hoặc vượt trần -> ValueError.

    `embed_fn` chỉ cần cho "semantic" (phương pháp duy nhất tốn phí embedding lúc cắt).
    """
    if method not in METHOD_PARAMS:
        raise ValueError(f"Unknown chunking method '{method}', expected one of {sorted(METHOD_PARAMS)}")
    params = dict(params or {})
    unknown = set(params) - METHOD_PARAMS[method]
    if unknown:
        raise ValueError(f"Unknown parameter(s) for '{method}': {sorted(unknown)}")
    for name, value in params.items():
        # bool là lớp con của int trong Python: chặn riêng để true/false không lọt thành 1/0.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Parameter '{name}' must be a number")
        if name != "breakpoint_percentile":
            if value != int(value):
                raise ValueError(f"Parameter '{name}' must be an integer")
            params[name] = int(value)
    for name in ("size", "max_size"):
        if params.get(name, 0) > MAX_CHUNK_CHARS:
            raise ValueError(f"Parameter '{name}' must be <= {MAX_CHUNK_CHARS}")

    if method == "fixed":
        return chunk_fixed(text, **params)
    if method == "recursive":
        return chunk_recursive(text, **params)
    if method == "structure":
        return chunk_structure(text, **params)
    if embed_fn is None:
        raise ValueError("Method 'semantic' requires an embedding function")
    return chunk_semantic(text, embed_fn, **params)
