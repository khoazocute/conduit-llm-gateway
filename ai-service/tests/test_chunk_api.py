"""TASK-75: điểm vào chung chunk() và hai endpoint /chunk, /chunk-embed nhận method/params.

Không gọi mạng: `main.embed` (gọi LiteLLM) được thay bằng hàm giả.
"""

import json
import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

import main
from chunking import METHOD_PARAMS, chunk, normalize
from ingest import EMBEDDING_DIMENSIONS

TOKEN = "test-token"

DOC = (
    "# Giới thiệu\n" + "RAG truy hồi tài liệu trước khi trả lời câu hỏi. " * 8 + "\n\n"
    "# Chi phí\n" + "Embedding có giá rất thấp so với gọi mô hình ngôn ngữ. " * 8 + "\n"
)


def fake_embed(texts, **kwargs):
    """Thay ingest.embed: vector 1536 chiều phụ thuộc nội dung, 1 token mỗi đầu vào."""
    vectors = []
    for t in texts:
        v = [0.0] * EMBEDDING_DIMENSIONS
        v[0] = float(t.count("RAG"))
        # Trọng số khác nhau để hai khoảng cách quanh chỗ đổi chủ đề không bằng nhau tuyệt đối
        # (bằng nhau thì ngưỡng phân vị 95 trùng đỉnh và quy tắc "> ngưỡng" không cắt).
        v[1] = 2.0 * t.count("Embedding")
        v[2] = 1.0
        vectors.append(v)
    return vectors, len(texts)


class ChunkDispatchTest(unittest.TestCase):
    def test_each_method_is_dispatched(self):
        for method in METHOD_PARAMS:
            with self.subTest(method=method):
                embed_fn = (lambda texts: fake_embed(texts)[0]) if method == "semantic" else None
                chunks = chunk(DOC, method, {}, embed_fn=embed_fn)
                self.assertTrue(chunks)
                self.assertTrue(all(c.method == method for c in chunks))
                norm = normalize(DOC)
                self.assertTrue(all(norm[c.start_char:c.end_char] == c.text for c in chunks))

    def test_default_is_fixed(self):
        self.assertEqual(chunk("Xin chào.")[0].method, "fixed")

    def test_params_are_passed(self):
        small = chunk(DOC, "recursive", {"size": 200, "overlap": 0})
        self.assertTrue(all(len(c.text) <= 200 for c in small))
        self.assertGreater(len(small), len(chunk(DOC, "recursive", {"size": 1000, "overlap": 0})))

    def test_integral_float_is_accepted(self):
        self.assertTrue(chunk(DOC, "fixed", {"size": 300.0, "overlap": 50}))

    def test_rejected_inputs(self):
        cases = [
            ("agentic", {}),                               # phương pháp không có
            ("fixed", {"min_size": 10}),                   # tham số không thuộc phương pháp
            ("fixed", {"size": "1000"}),                   # sai kiểu
            ("fixed", {"size": True}),                     # bool không phải số
            ("fixed", {"size": 300.5}),                    # không nguyên
            ("recursive", {"size": 9000, "overlap": 100}),  # vượt trần 8.000 ký tự
            ("semantic", {"max_size": 9000}),
            ("fixed", {"size": 100, "overlap": 80}),       # lỗi từ chính chunker
            ("semantic", {}),                              # thiếu embed_fn
        ]
        for method, params in cases:
            with self.subTest(method=method, params=params):
                with self.assertRaises(ValueError):
                    chunk(DOC, method, params)


class EndpointTestBase(unittest.TestCase):
    path = ""

    def setUp(self):
        patcher = mock.patch.dict(os.environ, {"AI_SERVICE_TOKEN": TOKEN, "CHUNK_SIZE": "300",
                                               "CHUNK_OVERLAP": "50", "MAX_CHUNKS": "50"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(main.app)

    def post(self, method=None, params=None, token=TOKEN, name="doc.txt", data=DOC.encode()):
        form = {}
        if method is not None:
            form["method"] = method
        if params is not None:
            form["params"] = params if isinstance(params, str) else json.dumps(params)
        headers = {"X-Internal-Token": token} if token is not None else {}
        return self.client.post(self.path, files={"file": (name, data)}, data=form, headers=headers)


class ChunkEndpointTest(EndpointTestBase):
    path = "/chunk"

    def test_token_required(self):
        with mock.patch.object(main, "embed") as fake:
            self.assertEqual(self.post(token=None).status_code, 401)
            self.assertEqual(self.post(token="wrong").status_code, 401)
            fake.assert_not_called()

    def test_default_is_fixed_with_env_sizes_and_no_embedding(self):
        with mock.patch.object(main, "embed") as fake:
            r = self.post()
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual((body["source"], body["method"], body["params"]),
                         ("doc.txt", "fixed", {"size": 300, "overlap": 50}))
        self.assertEqual(body["chunking_prompt_tokens"], 0)
        self.assertTrue(all(len(c["text"]) <= 300 for c in body["chunks"]))
        self.assertTrue(all("embedding" not in c for c in body["chunks"]))
        fake.assert_not_called()

    def test_structure_returns_offsets_and_headings(self):
        r = self.post("structure", {"size": 1000, "overlap": 100, "min_size": 0})
        self.assertEqual(r.status_code, 200)
        chunks = r.json()["chunks"]
        norm = normalize(DOC)
        self.assertEqual([c["metadata"]["heading"] for c in chunks], ["Giới thiệu", "Chi phí"])
        for c in chunks:
            self.assertEqual(norm[c["start_char"]:c["end_char"]], c["text"])
            self.assertEqual(c["method"], "structure")

    def test_semantic_uses_embedding_and_reports_tokens(self):
        with mock.patch.object(main, "embed", side_effect=fake_embed) as fake:
            r = self.post("semantic", {"min_size": 0})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(fake.call_count, 1)  # một lượt cho mọi cửa sổ câu
        self.assertEqual(body["chunking_prompt_tokens"], 18)  # 16 câu + 2 dòng tiêu đề = 18 cửa sổ
        self.assertEqual(len(body["chunks"]), 2)  # cắt đúng chỗ đổi chủ đề

    def test_semantic_windows_are_sent_in_batches(self):
        with mock.patch.dict(os.environ, {"EMBED_BATCH_SIZE": "5"}):
            with mock.patch.object(main, "embed", side_effect=fake_embed) as fake:
                r = self.post("semantic", {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(fake.call_count, 4)  # 18 cửa sổ / lô 5 = 4 lượt
        self.assertTrue(all(len(call.args[0]) <= 5 for call in fake.call_args_list))

    def test_invalid_method_or_params_is_422_without_embedding(self):
        with mock.patch.object(main, "embed") as fake:
            for method, params in [("agentic", None), ("fixed", "not json"), ("fixed", "[1, 2]"),
                                   ("fixed", {"size": 100, "overlap": 90}), ("recursive", {"foo": 1})]:
                with self.subTest(method=method, params=params):
                    self.assertEqual(self.post(method, params).status_code, 422)
            fake.assert_not_called()

    def test_too_many_chunks_is_422(self):
        with mock.patch.dict(os.environ, {"MAX_CHUNKS": "2"}):
            r = self.post("fixed", {"size": 200, "overlap": 0})
        self.assertEqual(r.status_code, 422)
        self.assertIn("limit is 2", r.json()["detail"])


class ChunkEmbedEndpointMethodTest(EndpointTestBase):
    path = "/chunk-embed"

    def test_backward_compatible_without_method(self):
        with mock.patch.object(main, "embed", side_effect=fake_embed) as fake:
            r = self.post()
        self.assertEqual(r.status_code, 200)
        body = r.json()
        fake.assert_called_once()  # chỉ embedding đoạn
        self.assertEqual(body["method"], "fixed")
        for i, c in enumerate(body["chunks"]):
            # Ba trường backend Java đang đọc (ChunkEmbeddingResult.Chunk) giữ nguyên.
            self.assertEqual(c["index"], i)
            self.assertIsInstance(c["text"], str)
            self.assertEqual(len(c["embedding"]), EMBEDDING_DIMENSIONS)

    def test_method_is_applied_before_embedding(self):
        with mock.patch.object(main, "embed", side_effect=fake_embed) as fake:
            r = self.post("recursive", {"size": 200, "overlap": 0})
        self.assertEqual(r.status_code, 200)
        chunks = r.json()["chunks"]
        self.assertTrue(all(c["method"] == "recursive" and len(c["text"]) <= 200 for c in chunks))
        self.assertEqual(fake.call_args.args[0], [c["text"] for c in chunks])

    def test_semantic_embeds_windows_then_chunks(self):
        with mock.patch.object(main, "embed", side_effect=fake_embed) as fake:
            r = self.post("semantic", {"min_size": 0})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(fake.call_count, 2)  # 1 lượt cửa sổ câu + 1 lượt các đoạn
        self.assertEqual(body["chunking_prompt_tokens"], 18)
        self.assertEqual(body["prompt_tokens"], len(body["chunks"]))

    def test_invalid_method_never_embeds(self):
        with mock.patch.object(main, "embed") as fake:
            self.assertEqual(self.post("agentic").status_code, 422)
            fake.assert_not_called()


if __name__ == "__main__":
    unittest.main()
