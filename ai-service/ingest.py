"""Nạp tài liệu cho RAG (TASK-57a): đọc PDF/TXT -> chia đoạn -> embedding.

Embedding đi qua LiteLLM (`/v1/embeddings`), không gọi thẳng OpenAI: CLAUDE.md mục 5, mọi lời gọi
model đi qua lớp adapter/proxy. Toàn bộ đoạn của một file gửi trong MỘT request, nên một file nhỏ
chỉ tốn một lượt gọi có phí (D1).

Service này không giữ trạng thái và không có quyền vào DB: backend kiểm ABAC, lưu file, rồi tự ghi
`kb_chunks` từ kết quả trả về.
"""

from __future__ import annotations

import io

import httpx
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# kb_chunks.embedding là vector(1536), khớp text-embedding-3-small.
EMBEDDING_DIMENSIONS = 1536

SUPPORTED_EXTENSIONS = (".pdf", ".txt")


class DocumentError(ValueError):
    """File không đọc được hoặc không được hỗ trợ. Lỗi phía người tải lên."""


class EmbeddingError(RuntimeError):
    """Proxy embedding lỗi hoặc trả kết quả sai định dạng."""


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".txt"):
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentError("TXT file must be UTF-8 encoded") from exc
    if name.endswith(".pdf"):
        if not data.startswith(b"%PDF"):
            raise DocumentError("File is not a valid PDF")
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise DocumentError("Encrypted PDF is not supported")
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except PdfReadError as exc:
            raise DocumentError("File is not a valid PDF") from exc
    raise DocumentError("Only .pdf and .txt files are supported")


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Chia theo số ký tự, cắt ở ranh giới từ, các đoạn liền nhau gối lên nhau `overlap` ký tự.

    Khoảng trắng liên tiếp (kể cả xuống dòng) được gộp thành một dấu cách.
    """
    if size <= 0 or overlap < 0 or overlap >= size // 2:
        raise ValueError("Require size > 0 and 0 <= overlap < size/2")

    text = " ".join(text.split())
    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + size, length)
        if end < length:
            # Lùi về dấu cách gần nhất, nhưng không lùi quá nửa đoạn (từ quá dài thì cắt cứng).
            cut = text.rfind(" ", start + size // 2, end)
            if cut != -1:
                end = cut
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        # end >= start + size/2 và overlap < size/2 nên next_start > start: vòng lặp luôn tiến.
        next_start = end - overlap
        space = text.find(" ", next_start, end)
        if space != -1:
            next_start = space + 1
        start = next_start
    return chunks


def embed(
    chunks: list[str],
    *,
    base_url: str,
    api_key: str,
    model: str,
    client: httpx.Client | None = None,
    timeout_seconds: float = 60.0,
) -> tuple[list[list[float]], int | None]:
    """Trả về (vector theo đúng thứ tự `chunks`, số token đầu vào nhà cung cấp tính)."""
    if not chunks:
        return [], 0
    own_client = client is None
    http = client or httpx.Client(timeout=timeout_seconds)
    try:
        response = http.post(
            f"{base_url.rstrip('/')}/embeddings",
            json={"model": model, "input": chunks},
            headers={"Authorization": f"Bearer {api_key}"},
        )
    except httpx.HTTPError as exc:
        raise EmbeddingError(f"Embedding proxy unreachable: {type(exc).__name__}") from exc
    finally:
        if own_client:
            http.close()

    if response.status_code != 200:
        raise EmbeddingError(f"Embedding proxy returned HTTP {response.status_code}")
    try:
        body = response.json()
        data = sorted(body["data"], key=lambda item: item["index"])
        vectors = [item["embedding"] for item in data]
    except (ValueError, KeyError, TypeError) as exc:
        raise EmbeddingError("Embedding proxy returned an unexpected body") from exc

    if len(vectors) != len(chunks):
        raise EmbeddingError(f"Expected {len(chunks)} embeddings, got {len(vectors)}")
    for vector in vectors:
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise EmbeddingError(
                f"Expected {EMBEDDING_DIMENSIONS}-dimension embeddings, got {len(vector)}"
            )
    usage = body.get("usage") or {}
    return vectors, usage.get("prompt_tokens")
