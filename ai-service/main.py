import hmac
import logging
import os

from fastapi import Body, FastAPI, File, Header, HTTPException, UploadFile

from ingest import DocumentError, EmbeddingError, chunk_text, embed, extract_text

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


@app.post("/chunk-embed")
def chunk_embed(
    file: UploadFile = File(...),
    x_internal_token: str | None = Header(default=None),
) -> dict:
    """Đọc file -> chia đoạn -> embedding. Chỉ backend gọi (token nội bộ), không mở ra ngoài."""
    _require_internal_token(x_internal_token)

    max_bytes = _int_setting("MAX_FILE_BYTES", 5 * 1024 * 1024)
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    try:
        text = extract_text(file.filename or "", data)
    except DocumentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    chunks = chunk_text(
        text,
        size=_int_setting("CHUNK_SIZE", 1000),
        overlap=_int_setting("CHUNK_OVERLAP", 150),
    )
    if not chunks:
        # Thường là PDF scan (ảnh), không có lớp chữ. Không làm OCR.
        raise HTTPException(status_code=422, detail="No extractable text in file")
    max_chunks = _int_setting("MAX_CHUNKS", 200)
    if len(chunks) > max_chunks:
        raise HTTPException(
            status_code=422, detail=f"File produces {len(chunks)} chunks, limit is {max_chunks}"
        )

    model, vectors, prompt_tokens = _embed(chunks)

    logger.info(
        "Embedded file=%s chunks=%d model=%s prompt_tokens=%s",
        file.filename, len(chunks), model, prompt_tokens,
    )
    return {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "chunks": [
            {"index": i, "text": chunk, "embedding": vector}
            for i, (chunk, vector) in enumerate(zip(chunks, vectors))
        ],
    }
