import hmac
import json
import logging
import os

from fastapi import Body, FastAPI, File, Form, Header, HTTPException, UploadFile

from chunking import DEFAULT_METHOD, Chunk, chunk
from ingest import DocumentError, EmbeddingError, embed, extract_text

logger = logging.getLogger("ai-service")

app = FastAPI(title="Conduit AI Service")


def _setting(name: str, default: str) -> str:
    # Đọc lúc gọi (không phải lúc import) để test đổi được bằng biến môi trường.
    return os.getenv(name, default)


def _int_setting(name: str, default: int) -> int:
    return int(_setting(name, str(default)))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _require_internal_token(x_internal_token: str | None) -> None:
    expected_token = _setting("AI_SERVICE_TOKEN", "dev-only-ai-service-token")
    if not hmac.compare_digest((x_internal_token or "").encode(), expected_token.encode()):
        raise HTTPException(status_code=401, detail="Invalid internal token")


def _embed(texts: list[str]) -> tuple[str, list[list[float]], int | None]:
    model = _setting("EMBEDDING_MODEL", "text-embedding-3-small")
    try:
        vectors, prompt_tokens = embed(
            texts,
            base_url=_setting("LITELLM_BASE_URL", "http://localhost:4000/v1"),
            api_key=_setting("LITELLM_MASTER_KEY", "sk-1234"),
            model=model,
        )
    except EmbeddingError as exc:
        logger.warning("Embedding failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return model, vectors, prompt_tokens


class _BatchedEmbedder:
    """embed_fn cho chunker ngữ nghĩa: chia lô (OpenAI nhận tối đa 2.048 đầu vào mỗi request)
    và cộng dồn token để báo cáo chi phí cắt đoạn riêng với chi phí embedding đoạn."""

    def __init__(self) -> None:
        self.prompt_tokens = 0
        self.calls = 0

    def __call__(self, texts: list[str]) -> list[list[float]]:
        batch_size = _int_setting("EMBED_BATCH_SIZE", 2048)
        vectors: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            _, batch_vectors, tokens = _embed(texts[i:i + batch_size])
            vectors.extend(batch_vectors)
            self.prompt_tokens += tokens or 0
            self.calls += 1
        return vectors


def _read_document(file: UploadFile) -> str:
    max_bytes = _int_setting("MAX_FILE_BYTES", 5 * 1024 * 1024)
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    try:
        return extract_text(file.filename or "", data)
    except DocumentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _parse_params(method: str, params: str) -> dict:
    try:
        parsed = json.loads(params or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Field 'params' must be a JSON object") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=422, detail="Field 'params' must be a JSON object")
    if method == "fixed" and not parsed:
        # Hành vi cũ của /chunk-embed: kích thước lấy từ biến môi trường.
        parsed = {"size": _int_setting("CHUNK_SIZE", 1000), "overlap": _int_setting("CHUNK_OVERLAP", 150)}
    return parsed


def _chunk_document(text: str, method: str, params: dict) -> tuple[list[Chunk], _BatchedEmbedder]:
    embedder = _BatchedEmbedder()
    try:
        chunks = chunk(text, method, params, embed_fn=embedder)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not chunks:
        # Thường là PDF scan (ảnh), không có lớp chữ. Không làm OCR.
        raise HTTPException(status_code=422, detail="No extractable text in file")
    max_chunks = _int_setting("MAX_CHUNKS", 200)
    if len(chunks) > max_chunks:
        raise HTTPException(
            status_code=422, detail=f"File produces {len(chunks)} chunks, limit is {max_chunks}"
        )
    return chunks, embedder


@app.post("/embed")
def embed_query(
    payload: dict = Body(...),
    x_internal_token: str | None = Header(default=None),
) -> dict:
    """TASK-57b: embedding MỘT câu hỏi chat để truy hồi kb_chunks. Chỉ backend gọi."""
    _require_internal_token(x_internal_token)
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=422, detail="Field 'text' must be a non-empty string")
    # Chỉ cần đủ ý để so khớp; cắt bớt để câu rất dài không tốn thêm token embedding.
    text = " ".join(text.split())[: _int_setting("MAX_QUERY_CHARS", 2000)]
    model, vectors, prompt_tokens = _embed([text])
    return {"model": model, "prompt_tokens": prompt_tokens, "embedding": vectors[0]}


@app.post("/chunk")
def chunk_only(
    file: UploadFile = File(...),
    method: str = Form(DEFAULT_METHOD),
    params: str = Form("{}"),
    x_internal_token: str | None = Header(default=None),
) -> dict:
    """TASK-75: đọc file -> chia đoạn theo `method`/`params`, KHÔNG embedding đoạn.

    Dùng cho đường graph (TASK-78 gọi chunker chung) và xem trước cách cắt. Riêng "semantic" vẫn
    tốn phí embedding câu để tìm chỗ đổi chủ đề (`chunking_prompt_tokens`).
    """
    _require_internal_token(x_internal_token)
    text = _read_document(file)
    parsed = _parse_params(method, params)
    chunks, embedder = _chunk_document(text, method, parsed)
    logger.info("Chunked file=%s method=%s chunks=%d", file.filename, method, len(chunks))
    return {
        "source": file.filename,
        "method": method,
        "params": parsed,
        "chunking_prompt_tokens": embedder.prompt_tokens,
        "chunks": [c.to_dict() for c in chunks],
    }


@app.post("/chunk-embed")
def chunk_embed(
    file: UploadFile = File(...),
    method: str = Form(DEFAULT_METHOD),
    params: str = Form("{}"),
    x_internal_token: str | None = Header(default=None),
) -> dict:
    """Đọc file -> chia đoạn (TASK-75: theo `method`/`params`) -> embedding. Chỉ backend gọi.

    Không gửi `method` thì giữ hành vi cũ: cắt cố định CHUNK_SIZE/CHUNK_OVERLAP (mặc định 1000/150).
    Trường cũ (`index`, `text`, `embedding`) giữ nguyên tên; các trường mới chỉ thêm vào.
    """
    _require_internal_token(x_internal_token)
    text = _read_document(file)
    parsed = _parse_params(method, params)
    chunks, embedder = _chunk_document(text, method, parsed)

    model, vectors, prompt_tokens = _embed([c.text for c in chunks])

    logger.info(
        "Embedded file=%s method=%s chunks=%d model=%s prompt_tokens=%s chunking_prompt_tokens=%s",
        file.filename, method, len(chunks), model, prompt_tokens, embedder.prompt_tokens,
    )
    return {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "chunking_prompt_tokens": embedder.prompt_tokens,
        "source": file.filename,
        "method": method,
        "params": parsed,
        "chunks": [
            {**c.to_dict(), "embedding": vector} for c, vector in zip(chunks, vectors)
        ],
    }
