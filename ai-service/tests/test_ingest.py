"""Test TASK-57a phía ai-service. Không gọi API thật: embedding được giả lập."""

import json
import os
import unittest
from unittest import mock

import httpx
from fastapi.testclient import TestClient

import main
from ingest import (
    EMBEDDING_DIMENSIONS,
    DocumentError,
    EmbeddingError,
    chunk_text,
    embed,
    extract_text,
)

TOKEN = "test-internal-token"


def minimal_pdf(text: str) -> bytes:
    """PDF một trang có lớp chữ, tự tính bảng xref (không cần thư viện tạo PDF)."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    return bytes(out)


def fake_embedding_transport(dimensions=EMBEDDING_DIMENSIONS, calls=None):
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if calls is not None:
            calls.append((str(request.url), request.headers.get("authorization"), payload))
        data = [
            {"index": i, "embedding": [float(i)] * dimensions}
            for i in reversed(range(len(payload["input"])))  # cố ý đảo thứ tự
        ]
        return httpx.Response(200, json={"data": data, "usage": {"prompt_tokens": 42}})

    return httpx.MockTransport(handler)


class ExtractTextTest(unittest.TestCase):
    def test_txt_utf8_with_bom(self):
        self.assertEqual(extract_text("a.TXT", "﻿Xin chào".encode("utf-8")), "Xin chào")

    def test_txt_not_utf8_is_rejected(self):
        with self.assertRaises(DocumentError):
            extract_text("a.txt", "Xin chào".encode("utf-16"))

    def test_pdf_text_layer_is_read(self):
        self.assertIn("Conduit RAG test", extract_text("doc.pdf", minimal_pdf("Conduit RAG test")))

    def test_file_named_pdf_but_not_pdf_is_rejected(self):
        with self.assertRaises(DocumentError):
            extract_text("doc.pdf", b"hello")

    def test_other_extensions_are_rejected(self):
        for name in ("a.docx", "a.md", "noext", ""):
            with self.subTest(name=name), self.assertRaises(DocumentError):
                extract_text(name, b"data")


class ChunkTextTest(unittest.TestCase):
    def test_short_text_is_one_chunk_with_whitespace_collapsed(self):
        self.assertEqual(chunk_text("  a\n\nb\t c ", size=100, overlap=10), ["a b c"])

    def test_empty_text_gives_no_chunk(self):
        self.assertEqual(chunk_text(" \n ", size=100, overlap=10), [])

    def test_chunks_respect_size_cut_at_words_and_overlap(self):
        words = [f"w{i:03d}" for i in range(300)]  # 300 từ, mỗi từ 4 ký tự
        chunks = chunk_text(" ".join(words), size=100, overlap=20)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 100)
            for token in chunk.split(" "):
                self.assertIn(token, words)  # không từ nào bị cắt đôi
        for left, right in zip(chunks, chunks[1:]):
            self.assertIn(left.split(" ")[-1], right.split(" "))  # có gối đầu
        # Không mất từ nào.
        self.assertEqual(sorted(set(" ".join(chunks).split(" "))), words)

    def test_word_longer_than_chunk_is_hard_cut_and_loop_terminates(self):
        chunks = chunk_text("x" * 250, size=100, overlap=10)
        self.assertEqual("".join(c for c in chunks)[:100], "x" * 100)
        self.assertTrue(all(len(c) <= 100 for c in chunks))

    def test_invalid_parameters(self):
        for size, overlap in ((0, 0), (100, 50), (100, -1)):
            with self.subTest(size=size, overlap=overlap), self.assertRaises(ValueError):
                chunk_text("abc", size=size, overlap=overlap)


class EmbedTest(unittest.TestCase):
    def test_one_request_for_all_chunks_and_order_is_restored(self):
        calls = []
        client = httpx.Client(transport=fake_embedding_transport(calls=calls))
        vectors, tokens = embed(
            ["a", "b", "c"], base_url="http://proxy/v1/", api_key="k", model="m", client=client
        )
        self.assertEqual(len(calls), 1)
        url, auth, payload = calls[0]
        self.assertEqual(url, "http://proxy/v1/embeddings")
        self.assertEqual(auth, "Bearer k")
        self.assertEqual(payload, {"model": "m", "input": ["a", "b", "c"]})
        self.assertEqual([v[0] for v in vectors], [0.0, 1.0, 2.0])
        self.assertEqual(tokens, 42)

    def test_wrong_dimension_is_rejected(self):
        client = httpx.Client(transport=fake_embedding_transport(dimensions=3))
        with self.assertRaises(EmbeddingError):
            embed(["a"], base_url="http://p", api_key="k", model="m", client=client)

    def test_proxy_error_is_raised(self):
        client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401)))
        with self.assertRaisesRegex(EmbeddingError, "401"):
            embed(["a"], base_url="http://p", api_key="k", model="m", client=client)


class ChunkEmbedEndpointTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(
            os.environ,
            {"AI_SERVICE_TOKEN": TOKEN, "CHUNK_SIZE": "100", "CHUNK_OVERLAP": "20", "MAX_CHUNKS": "5"},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(main.app)

    def post(self, name, data, token=TOKEN):
        headers = {"X-Internal-Token": token} if token is not None else {}
        return self.client.post("/chunk-embed", files={"file": (name, data)}, headers=headers)

    def test_missing_or_wrong_token_is_rejected_before_any_embedding(self):
        with mock.patch.object(main, "embed") as fake:
            self.assertEqual(self.post("a.txt", b"hello", token=None).status_code, 401)
            self.assertEqual(self.post("a.txt", b"hello", token="wrong").status_code, 401)
            fake.assert_not_called()

    def test_txt_is_chunked_and_embedded(self):
        def fake_embed(chunks, **kwargs):
            return [[0.5] * EMBEDDING_DIMENSIONS for _ in chunks], 7

        with mock.patch.object(main, "embed", side_effect=fake_embed) as fake:
            response = self.post("notes.txt", ("word " * 40).encode())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["model"], "text-embedding-3-small")
        self.assertEqual(body["prompt_tokens"], 7)
        self.assertEqual([c["index"] for c in body["chunks"]], list(range(len(body["chunks"]))))
        self.assertTrue(all(len(c["embedding"]) == EMBEDDING_DIMENSIONS for c in body["chunks"]))
        fake.assert_called_once()

    def test_unsupported_or_empty_or_oversized_file_never_calls_embedding(self):
        with mock.patch.object(main, "embed") as fake:
            self.assertEqual(self.post("a.docx", b"x").status_code, 422)
            self.assertEqual(self.post("a.txt", b"   ").status_code, 422)
            self.assertEqual(self.post("a.txt", ("word " * 400).encode()).status_code, 422)  # > 5 đoạn
            fake.assert_not_called()

    def test_embedding_failure_is_502(self):
        with mock.patch.object(main, "embed", side_effect=EmbeddingError("HTTP 503")):
            self.assertEqual(self.post("a.txt", b"hello").status_code, 502)


if __name__ == "__main__":
    unittest.main()
