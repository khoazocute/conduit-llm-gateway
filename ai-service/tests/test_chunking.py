"""Unit test cho chunking.py (TASK-75). Không gọi mạng, không tốn phí."""

import random
import unicodedata
import unittest

from chunking import (
    Chunk,
    chunk_fixed,
    chunk_recursive,
    chunk_semantic,
    chunk_structure,
    normalize,
)


def make_document(seed: int = 42, paragraphs: int = 12) -> str:
    """Văn bản giả có nhiều đoạn văn, xuống dòng, khoảng trắng thừa và \\r\\n (cố định theo seed)."""
    rng = random.Random(seed)
    words = ["dữ", "liệu", "truy", "hồi", "mô", "hình", "embedding", "vector", "chunking",
             "retrieval", "augmented", "generation", "PostgreSQL", "pgvector", "đoạn", "văn"]
    paras = []
    for _ in range(paragraphs):
        sentences = []
        for _ in range(rng.randint(2, 6)):
            n = rng.randint(5, 18)
            sentences.append(" ".join(rng.choice(words) for _ in range(n)).capitalize() + ".")
        paras.append("  ".join(sentences))  # khoảng trắng thừa giữa câu
    return "\r\n\r\n\r\n".join(paras) + "\n   \n"


class ChunkAssertions(unittest.TestCase):
    """Kiểm tra dùng chung cho MỌI chunker (bước 2–4 gọi lại)."""

    def assert_valid_chunks(self, text: str, chunks: list[Chunk], max_size: int, method: str):
        norm = normalize(text)
        covered = [False] * len(norm)
        for i, c in enumerate(chunks):
            # 1. Bất biến vị trí.
            self.assertEqual(norm[c.start_char:c.end_char], c.text, f"chunk {i}: offset mismatch")
            # 2. index liên tục.
            self.assertEqual(c.index, i)
            # 3. Không vượt kích thước.
            self.assertLessEqual(len(c.text), max_size, f"chunk {i} too long")
            # 4. Không rỗng, không có khoảng trắng hai đầu.
            self.assertTrue(c.text, f"chunk {i} empty")
            self.assertFalse(c.text[0].isspace() or c.text[-1].isspace(), f"chunk {i} not trimmed")
            self.assertEqual(c.method, method)
            for p in range(c.start_char, c.end_char):
                covered[p] = True
        # 5. Không mất chữ: mọi ký tự không phải khoảng trắng đều nằm trong ít nhất một đoạn.
        lost = [p for p, ch in enumerate(norm) if not ch.isspace() and not covered[p]]
        self.assertEqual(lost, [], f"{len(lost)} characters not covered by any chunk")


class NormalizeTest(unittest.TestCase):
    def test_crlf_and_cr_become_lf(self):
        self.assertEqual(normalize("a\r\nb\rc"), "a\nb\nc")

    def test_inline_whitespace_collapsed(self):
        self.assertEqual(normalize("a  \t b  c"), "a b c")

    def test_three_or_more_newlines_become_paragraph_break(self):
        self.assertEqual(normalize("a\n\n\n\nb"), "a\n\nb")

    def test_single_and_double_newlines_kept(self):
        self.assertEqual(normalize("a\nb\n\nc"), "a\nb\n\nc")

    def test_lines_and_document_are_trimmed(self):
        self.assertEqual(normalize("  a  \n  b  "), "a\nb")
        self.assertEqual(normalize("\n\n  a\n\n"), "a")

    def test_whitespace_only_lines_count_as_blank(self):
        self.assertEqual(normalize("a\n   \n \t \nb"), "a\n\nb")

    def test_vietnamese_nfd_becomes_nfc(self):
        nfd = unicodedata.normalize("NFD", "Tiếng Việt")
        self.assertNotEqual(nfd, "Tiếng Việt")
        self.assertEqual(normalize(nfd), "Tiếng Việt")

    def test_idempotent(self):
        doc = make_document()
        once = normalize(doc)
        self.assertEqual(normalize(once), once)

    def test_empty(self):
        self.assertEqual(normalize(""), "")
        self.assertEqual(normalize(" \r\n\t "), "")


class ChunkFixedTest(ChunkAssertions):
    def test_empty_or_whitespace_gives_no_chunk(self):
        self.assertEqual(chunk_fixed(""), [])
        self.assertEqual(chunk_fixed("  \n\r\n\t "), [])

    def test_short_text_is_one_chunk(self):
        chunks = chunk_fixed("  Xin   chào\r\nthế giới  ", size=100, overlap=10)
        self.assertEqual(len(chunks), 1)
        c = chunks[0]
        self.assertEqual((c.text, c.index, c.start_char, c.method), ("Xin chào\nthế giới", 0, 0, "fixed"))
        self.assertEqual(c.end_char, len(c.text))
        self.assertEqual(c.metadata, {})

    def test_long_document_is_valid(self):
        doc = make_document()
        for size, overlap in [(1000, 150), (300, 50), (120, 0)]:
            with self.subTest(size=size, overlap=overlap):
                chunks = chunk_fixed(doc, size=size, overlap=overlap)
                self.assertGreater(len(chunks), 2)
                self.assert_valid_chunks(doc, chunks, size, "fixed")

    def test_neighbours_overlap_at_most_overlap_chars(self):
        chunks = chunk_fixed(make_document(), size=300, overlap=50)
        for a, b in zip(chunks, chunks[1:]):
            self.assertLess(a.start_char, b.start_char)
            shared = a.end_char - b.start_char
            self.assertGreater(shared, 0, "consecutive chunks should overlap")
            self.assertLessEqual(shared, 50)

    def test_no_overlap_when_overlap_is_zero(self):
        chunks = chunk_fixed(make_document(), size=200, overlap=0)
        for a, b in zip(chunks, chunks[1:]):
            self.assertLessEqual(a.end_char, b.start_char)

    def test_cuts_at_word_boundaries(self):
        doc = make_document()
        norm = normalize(doc)
        for c in chunk_fixed(doc, size=200, overlap=30):
            self.assertTrue(c.start_char == 0 or norm[c.start_char - 1].isspace(), c.text[:20])
            self.assertTrue(c.end_char == len(norm) or norm[c.end_char].isspace(), c.text[-20:])

    def test_cut_exactly_at_space_uses_full_size(self):
        chunks = chunk_fixed("aaaa bbbb", size=4, overlap=0)
        self.assertEqual([(c.text, c.start_char, c.end_char) for c in chunks],
                         [("aaaa", 0, 4), ("bbbb", 5, 9)])

    def test_newline_is_a_valid_cut_point(self):
        chunks = chunk_fixed("aaaa\nbbbb", size=6, overlap=0)
        self.assertEqual([c.text for c in chunks], ["aaaa", "bbbb"])

    def test_word_longer_than_chunk_is_hard_cut_and_loop_terminates(self):
        doc = "x" * 2500 + " tail"
        chunks = chunk_fixed(doc, size=1000, overlap=150)
        self.assert_valid_chunks(doc, chunks, 1000, "fixed")
        self.assertEqual(chunks[0].text, "x" * 1000)
        self.assertTrue(chunks[-1].text.endswith("tail"))

    def test_invalid_parameters(self):
        for size, overlap in [(0, 0), (-5, 0), (100, -1), (100, 50), (100, 80), (1, 0)]:
            with self.subTest(size=size, overlap=overlap):
                with self.assertRaises(ValueError):
                    chunk_fixed("abc", size=size, overlap=overlap)

    def test_to_dict(self):
        c = chunk_fixed("hello world", size=100, overlap=0)[0]
        self.assertEqual(c.to_dict(), {"index": 0, "text": "hello world", "start_char": 0,
                                       "end_char": 11, "method": "fixed", "metadata": {}})


def make_sentences(seed: int, count: int, min_words: int = 4, max_words: int = 15) -> list[str]:
    rng = random.Random(seed)
    words = ["hệ", "thống", "truy", "hồi", "tài", "liệu", "trả", "lời", "câu", "hỏi", "người", "dùng"]
    ends = [".", "?", "!"]
    return [" ".join(rng.choice(words) for _ in range(rng.randint(min_words, max_words))).capitalize()
            + rng.choice(ends) for _ in range(count)]


class ChunkRecursiveTest(ChunkAssertions):
    def test_empty_or_whitespace_gives_no_chunk(self):
        self.assertEqual(chunk_recursive(""), [])
        self.assertEqual(chunk_recursive(" \n\n\t "), [])

    def test_short_text_is_one_chunk(self):
        chunks = chunk_recursive("Câu một.\n\nCâu hai.", size=100, overlap=10)
        self.assertEqual([(c.text, c.start_char, c.method) for c in chunks],
                         [("Câu một.\n\nCâu hai.", 0, "recursive")])

    def test_long_document_is_valid(self):
        doc = make_document()
        for size, overlap in [(1000, 150), (300, 50), (120, 0), (60, 20)]:
            with self.subTest(size=size, overlap=overlap):
                chunks = chunk_recursive(doc, size=size, overlap=overlap)
                self.assertGreater(len(chunks), 2)
                self.assert_valid_chunks(doc, chunks, size, "recursive")

    def test_paragraphs_that_fit_are_never_split(self):
        paras = [" ".join(make_sentences(i, 3)) for i in range(6)]
        self.assertTrue(all(len(p) <= 250 for p in paras))
        chunks = chunk_recursive("\n\n".join(paras), size=250, overlap=0)
        norm_paras = [normalize(p) for p in paras]
        for c in chunks:
            # Mỗi đoạn là một hoặc nhiều đoạn văn trọn vẹn.
            for part in c.text.split("\n\n"):
                self.assertIn(part, norm_paras)

    def test_does_not_cut_inside_short_sentences(self):
        sentences = make_sentences(7, 60)
        self.assertTrue(all(len(s) <= 200 for s in sentences))
        doc = " ".join(sentences)  # một đoạn văn dài, không xuống dòng
        chunks = chunk_recursive(doc, size=200, overlap=0)
        self.assertGreater(len(chunks), 5)
        self.assert_valid_chunks(doc, chunks, 200, "recursive")
        for c in chunks:
            self.assertIn(c.text[-1], ".?!", f"chunk ends mid-sentence: ...{c.text[-30:]!r}")
            self.assertTrue(c.start_char == 0 or doc[c.start_char - 2] in ".?!",
                            f"chunk starts mid-sentence: {c.text[:30]!r}")

    def test_paragraph_that_fits_is_not_mixed_with_next_long_paragraph(self):
        # Ví dụ chuẩn của thuật toán LangChain: đoạn văn 1 (~600 ký tự) vừa size nên đứng riêng;
        # đoạn văn 2 (~1.500 ký tự) quá dài nên chỉ NÓ bị tách theo câu. Không đoạn nào trộn hai đoạn văn.
        para1 = " ".join(make_sentences(11, 12, min_words=8, max_words=12))
        para2 = " ".join(make_sentences(12, 30, min_words=8, max_words=12))
        self.assertTrue(500 < len(para1) <= 1000 < len(para2), (len(para1), len(para2)))
        doc = para1 + "\n\n" + para2
        chunks = chunk_recursive(doc, size=1000, overlap=0)
        self.assert_valid_chunks(doc, chunks, 1000, "recursive")
        self.assertEqual(chunks[0].text, para1)
        self.assertTrue(all("\n\n" not in c.text for c in chunks))

    def test_chunks_crossing_paragraphs_contain_only_whole_paragraphs(self):
        # Tính chất của thuật toán chuẩn: đoạn nào vượt qua ranh giới "\n\n" thì chỉ gồm các đoạn văn
        # TRỌN VẸN (đoạn văn bị cắt nhỏ không bao giờ bị ghép với đoạn văn bên cạnh).
        doc = make_document(seed=5, paragraphs=20)
        norm = normalize(doc)
        starts = {0} | {m + 2 for m in range(len(norm)) if norm.startswith("\n\n", m)}
        ends = {len(norm)} | {m for m in range(len(norm)) if norm.startswith("\n\n", m)}
        for size, overlap in [(1000, 0), (400, 0), (250, 0), (400, 100)]:
            with self.subTest(size=size, overlap=overlap):
                chunks = chunk_recursive(doc, size=size, overlap=overlap)
                self.assert_valid_chunks(doc, chunks, size, "recursive")
                for c in chunks:
                    if "\n\n" in c.text:
                        self.assertIn(c.start_char, starts, c.text[:40])
                        self.assertIn(c.end_char, ends, c.text[-40:])

    def test_fixed_cuts_mid_sentence_where_recursive_does_not(self):
        doc = " ".join(make_sentences(7, 60))
        def mid_sentence(chunks):
            return sum(1 for c in chunks if c.text[-1] not in ".?!")
        self.assertEqual(mid_sentence(chunk_recursive(doc, size=200, overlap=0)), 0)
        self.assertGreater(mid_sentence(chunk_fixed(doc, size=200, overlap=0)), 0)

    def test_sentence_longer_than_size_falls_back_to_words(self):
        doc = " ".join(["từ"] * 200) + "."  # một câu ~600 ký tự, không có dấu chấm ở giữa
        chunks = chunk_recursive(doc, size=100, overlap=0)
        self.assert_valid_chunks(doc, chunks, 100, "recursive")
        for c in chunks:
            self.assertTrue(c.text.startswith("từ"), "word was split")

    def test_word_longer_than_chunk_is_hard_cut_and_loop_terminates(self):
        doc = "Mở đầu. " + "x" * 2500 + " kết thúc."
        chunks = chunk_recursive(doc, size=1000, overlap=150)
        self.assert_valid_chunks(doc, chunks, 1000, "recursive")
        self.assertIn("x" * 1000, [c.text for c in chunks])

    def test_overlap_is_whole_sentences_and_at_most_overlap_chars(self):
        doc = " ".join(make_sentences(3, 80, min_words=2, max_words=6))
        chunks = chunk_recursive(doc, size=200, overlap=60)
        overlapped = 0
        for a, b in zip(chunks, chunks[1:]):
            self.assertLess(a.start_char, b.start_char)
            shared = a.end_char - b.start_char
            self.assertLessEqual(shared, 60)
            if shared > 0:
                overlapped += 1
                self.assertIn(doc[b.start_char - 2], ".?!", "overlap must start at a sentence")
        self.assertGreater(overlapped, 0, "short sentences should produce some overlap")

    def test_no_overlap_when_overlap_is_zero(self):
        chunks = chunk_recursive(make_document(), size=200, overlap=0)
        for a, b in zip(chunks, chunks[1:]):
            self.assertLessEqual(a.end_char, b.start_char)

    def test_question_and_exclamation_are_sentence_ends(self):
        doc = "Bạn khỏe không? Tôi khỏe! Cảm ơn bạn."
        chunks = chunk_recursive(doc, size=16, overlap=0)
        self.assertEqual([c.text for c in chunks], ["Bạn khỏe không?", "Tôi khỏe!", "Cảm ơn bạn."])

    def test_custom_separators(self):
        doc = "a;b;c;d"
        # Dấu tách dính vào mảnh bên trái: các mảnh là "a;", "b;", "c;", "d".
        chunks = chunk_recursive(doc, size=4, overlap=0, separators=(";",))
        self.assertEqual([c.text for c in chunks], ["a;b;", "c;d"])

    def test_invalid_parameters(self):
        for size, overlap in [(0, 0), (100, -1), (100, 50)]:
            with self.subTest(size=size, overlap=overlap):
                with self.assertRaises(ValueError):
                    chunk_recursive("abc", size=size, overlap=overlap)
        with self.assertRaises(ValueError):
            chunk_recursive("abc", separators=())


TOPICS = {
    "mèo": ["Con mèo ngủ trên ghế.", "Con mèo thích ăn cá.", "Con mèo kêu meo meo.", "Con mèo trèo lên cây."],
    "xe": ["Chiếc xe chạy trên đường.", "Chiếc xe cần thay dầu.", "Chiếc xe màu đỏ rất đẹp.", "Chiếc xe đỗ trước nhà."],
    "bánh": ["Cái bánh vừa ra lò.", "Cái bánh có vị ngọt.", "Cái bánh được cắt làm tư.", "Cái bánh rất thơm."],
}


class FakeEmbed:
    """Embedding giả: vector = số lần xuất hiện của từ khóa mỗi chủ đề. Đếm số lần được gọi."""

    def __init__(self):
        self.calls = []

    def __call__(self, texts):
        self.calls.append(list(texts))
        return [[t.count(k) + 0.0 for k in TOPICS] for t in texts]


def random_embed(texts):
    """Embedding giả ngẫu nhiên nhưng cố định theo nội dung (để test tính hợp lệ trên văn bản bất kỳ)."""
    out = []
    for t in texts:
        rng = random.Random(t)
        out.append([rng.uniform(-1, 1) for _ in range(8)])
    return out


def topic_text(*parts):
    """parts = (chủ đề, số câu), ...; các câu nối bằng dấu cách, không xuống dòng."""
    sentences = []
    for topic, n in parts:
        sentences += [TOPICS[topic][i % 4] for i in range(n)]
    return " ".join(sentences)


class ChunkSemanticTest(ChunkAssertions):
    def test_empty_gives_no_chunk_and_no_embedding_call(self):
        fake = FakeEmbed()
        self.assertEqual(chunk_semantic("  \n ", fake), [])
        self.assertEqual(fake.calls, [])

    def test_single_sentence_needs_no_embedding(self):
        fake = FakeEmbed()
        chunks = chunk_semantic("Một câu duy nhất.", fake)
        self.assertEqual([c.text for c in chunks], ["Một câu duy nhất."])
        self.assertEqual(fake.calls, [])

    def test_cuts_where_topic_changes(self):
        doc = topic_text(("mèo", 10), ("xe", 10))
        fake = FakeEmbed()
        chunks = chunk_semantic(doc, fake, min_size=0, max_size=1000)
        self.assert_valid_chunks(doc, chunks, 1000, "semantic")
        self.assertEqual(len(chunks), 2)
        self.assertNotIn("xe", chunks[0].text)
        self.assertNotIn("mèo", chunks[1].text)
        self.assertEqual([c.metadata["sentences"] for c in chunks], [10, 10])

    def test_embedding_is_called_once_with_one_window_per_sentence(self):
        doc = topic_text(("mèo", 6), ("xe", 6))
        fake = FakeEmbed()
        chunk_semantic(doc, fake, min_size=0)
        self.assertEqual(len(fake.calls), 1)
        windows = fake.calls[0]
        self.assertEqual(len(windows), 12)
        # buffer=1: cửa sổ đầu = câu 0 + câu 1, cửa sổ giữa = 3 câu.
        self.assertEqual(windows[0], "Con mèo ngủ trên ghế. Con mèo thích ăn cá.")
        self.assertEqual(windows[1].count("."), 3)

    def test_three_topics_with_lower_percentile_and_no_buffer(self):
        doc = topic_text(("mèo", 8), ("xe", 8), ("bánh", 8))
        chunks = chunk_semantic(doc, FakeEmbed(), breakpoint_percentile=90, buffer=0, min_size=0)
        self.assertEqual(len(chunks), 3)
        for c, topic in zip(chunks, ["mèo", "xe", "bánh"]):
            self.assertTrue(all(topic in s for s in c.text.split(". ")), c.text)

    def test_same_topic_everywhere_gives_no_semantic_cut(self):
        doc = topic_text(("mèo", 12))
        chunks = chunk_semantic(doc, FakeEmbed(), min_size=0, max_size=1000)
        self.assertEqual(len(chunks), 1)

    def test_group_longer_than_max_size_is_split_at_sentences(self):
        doc = topic_text(("mèo", 40))
        chunks = chunk_semantic(doc, FakeEmbed(), min_size=0, max_size=200)
        self.assertGreater(len(chunks), 3)
        self.assert_valid_chunks(doc, chunks, 200, "semantic")
        for c in chunks:
            self.assertEqual(c.text[-1], ".")

    def test_small_groups_are_merged_up_to_max_size(self):
        # buffer=0: khoảng cách = 0 trong cùng chủ đề, = 1 khi đổi chủ đề -> 5 nhóm nhỏ (1–2 câu).
        doc = topic_text(("mèo", 2), ("xe", 1), ("bánh", 2), ("mèo", 1), ("xe", 2))
        no_min = chunk_semantic(doc, FakeEmbed(), breakpoint_percentile=0, buffer=0, min_size=0)
        self.assertEqual(len(no_min), 5)
        with_min = chunk_semantic(doc, FakeEmbed(), breakpoint_percentile=0, buffer=0,
                                  min_size=60, max_size=1000)
        self.assertGreater(len(no_min), len(with_min))
        self.assert_valid_chunks(doc, with_min, 1000, "semantic")
        for c in with_min[:-1]:
            self.assertGreaterEqual(len(c.text), 60)

    def test_sentence_longer_than_max_size_is_split_by_words(self):
        doc = "Mở đầu ngắn. " + " ".join(["từ"] * 300) + ". Kết thúc."
        chunks = chunk_semantic(doc, random_embed, min_size=0, max_size=100)
        self.assert_valid_chunks(doc, chunks, 100, "semantic")

    def test_long_sentence_becomes_few_fragments_not_single_words(self):
        # Câu ~900 ký tự, max_size 100: phải thành ~9–10 mảnh gần 100 ký tự, KHÔNG phải 300 "câu" một từ
        # (mỗi từ lẻ thành một cửa sổ embedding thì khoảng cách cosine vô nghĩa và tốn phí gấp nhiều lần).
        doc = "Mở đầu ngắn. " + " ".join(["từ"] * 300) + ". Kết thúc."
        fake = FakeEmbed()
        chunk_semantic(doc, fake, min_size=0, max_size=100)
        self.assertLessEqual(len(fake.calls[0]), 14)

    def test_long_document_is_valid(self):
        doc = make_document()
        for min_size, max_size in [(200, 1000), (0, 300), (50, 120)]:
            with self.subTest(min_size=min_size, max_size=max_size):
                chunks = chunk_semantic(doc, random_embed, min_size=min_size, max_size=max_size)
                self.assert_valid_chunks(doc, chunks, max_size, "semantic")

    def test_newline_is_a_sentence_boundary(self):
        fake = FakeEmbed()
        chunk_semantic("Tiêu đề không có dấu chấm\nNội dung thứ nhất. Nội dung thứ hai.", fake)
        self.assertEqual(len(fake.calls[0]), 3)

    def test_wrong_number_of_vectors_is_rejected(self):
        with self.assertRaises(ValueError):
            chunk_semantic(topic_text(("mèo", 5)), lambda texts: [[1.0, 0.0]])

    def test_invalid_parameters(self):
        doc = topic_text(("mèo", 3))
        for kwargs in [dict(max_size=0), dict(min_size=-1), dict(min_size=500, max_size=100),
                       dict(breakpoint_percentile=101), dict(buffer=-1)]:
            with self.subTest(**kwargs):
                with self.assertRaises(ValueError):
                    chunk_semantic(doc, FakeEmbed(), **kwargs)


MARKDOWN_DOC = (
    "Lời mở đầu ngắn của tài liệu.\n\n"
    "# 1. Giới thiệu\n" + "RAG giúp mô hình trả lời dựa trên tài liệu. " * 6 + "\n\n"
    "## 1.1. Bối cảnh\n" + "Mô hình ngôn ngữ không biết dữ liệu riêng của doanh nghiệp. " * 5 + "\n\n"
    "# 2. Chi phí\n" + "Embedding có giá 0,02 USD cho 1 triệu token. " * 6 + "\n"
)

LEGAL_DOC = (
    "QUY CHẾ ĐÀO TẠO\n"
    "Chương I. QUY ĐỊNH CHUNG\n"
    "Điều 1. Phạm vi điều chỉnh\n" + "Quy chế này áp dụng cho sinh viên hệ chính quy. " * 5 + "\n"
    "Điều 2. Đối tượng áp dụng\n" + "Sinh viên phải tuân thủ quy định tại\nĐiều 5 của quy chế này. "
    + "Giảng viên có trách nhiệm hướng dẫn sinh viên. " * 4 + "\n"
    "Chương II. TỔ CHỨC ĐÀO TẠO\n"
    "Điều 3. Thời gian học tập\n" + "Thời gian học tối đa gấp đôi thời gian thiết kế. " * 5 + "\n"
)

PAPER_DOC = (
    "Abstract\nWe study retrieval for long documents.\n"
    "1 Introduction\nLong documents are hard to search.\n"
    "2 Method\nWe split documents into chunks.\n"
    "2.1 Data\nWe use three sources.\n1. Thu thập dữ liệu từ nhiều nguồn.\n2. Làm sạch dữ liệu.\n"
    "References\n[1] Some paper."
)


class ChunkStructureTest(ChunkAssertions):
    def headings(self, chunks):
        return [c.metadata["heading"] for c in chunks]

    def test_empty_gives_no_chunk(self):
        self.assertEqual(chunk_structure(""), [])
        self.assertEqual(chunk_structure(" \n\n "), [])

    def test_markdown_sections_become_chunks(self):
        chunks = chunk_structure(MARKDOWN_DOC, size=1000, overlap=150, min_size=200)
        self.assert_valid_chunks(MARKDOWN_DOC, chunks, 1000, "structure")
        self.assertEqual(self.headings(chunks), ["1. Giới thiệu", "1.1. Bối cảnh", "2. Chi phí"])
        self.assertEqual([c.metadata["heading_path"] for c in chunks],
                         [["1. Giới thiệu"], ["1. Giới thiệu", "1.1. Bối cảnh"], ["2. Chi phí"]])
        # Phần mở đầu ngắn được gộp vào mục đầu; dòng tiêu đề vẫn nằm trong text (chữ gốc).
        self.assertTrue(chunks[0].text.startswith("Lời mở đầu"))
        self.assertTrue(chunks[1].text.startswith("## 1.1. Bối cảnh"))
        # Không đoạn nào chứa hai mục.
        self.assertNotIn("Chi phí", chunks[1].text)

    def test_min_size_zero_keeps_short_preamble_separate(self):
        chunks = chunk_structure(MARKDOWN_DOC, min_size=0)
        self.assertEqual(self.headings(chunks), [None, "1. Giới thiệu", "1.1. Bối cảnh", "2. Chi phí"])

    def test_legal_document_one_article_per_chunk(self):
        chunks = chunk_structure(LEGAL_DOC, size=1000, overlap=150, min_size=200)
        self.assert_valid_chunks(LEGAL_DOC, chunks, 1000, "structure")
        self.assertEqual([c.metadata["heading_path"] for c in chunks], [
            ["Chương I. QUY ĐỊNH CHUNG", "Điều 1. Phạm vi điều chỉnh"],
            ["Chương I. QUY ĐỊNH CHUNG", "Điều 2. Đối tượng áp dụng"],
            ["Chương II. TỔ CHỨC ĐÀO TẠO", "Điều 3. Thời gian học tập"],
        ])
        # Tiêu đề chương đứng trơ được gộp vào điều đầu tiên của chương.
        self.assertTrue(chunks[2].text.startswith("Chương II. TỔ CHỨC ĐÀO TẠO\nĐiều 3."))

    def test_line_wrapped_article_reference_is_not_a_heading(self):
        chunks = chunk_structure(LEGAL_DOC, min_size=0)
        holder = [c for c in chunks if "Điều 5 của quy chế này" in c.text]
        self.assertEqual(len(holder), 1)
        self.assertEqual(holder[0].metadata["heading"], "Điều 2. Đối tượng áp dụng")

    def test_paper_sections_numbered_and_named(self):
        chunks = chunk_structure(PAPER_DOC, size=1000, overlap=0, min_size=0)
        self.assert_valid_chunks(PAPER_DOC, chunks, 1000, "structure")
        self.assertEqual([c.metadata["heading_path"] for c in chunks], [
            ["Abstract"], ["1 Introduction"], ["2 Method"], ["2 Method", "2.1 Data"], ["References"],
        ])
        # Mục liệt kê "1. Thu thập ..." (kết thúc bằng dấu chấm) không phải tiêu đề.
        self.assertIn("1. Thu thập dữ liệu", chunks[3].text)

    def test_long_section_is_split_inside_the_section_only(self):
        doc = "# A\n" + "Câu dài trong mục A về truy hồi tài liệu. " * 60 + "\n\n# B\n" + "Câu ngắn mục B. " * 5
        b_start = normalize(doc).index("# B")
        chunks = chunk_structure(doc, size=500, overlap=100, min_size=0)
        self.assert_valid_chunks(doc, chunks, 500, "structure")
        self.assertGreater(len(chunks), 4)
        for c in chunks:
            self.assertFalse(c.start_char < b_start < c.end_char, "chunk crosses section boundary")
            self.assertEqual(c.metadata["heading"], "B" if c.start_char >= b_start else "A")

    def test_short_sections_are_merged_only_when_they_fit(self):
        doc = "# A\nx.\n# B\ny.\n# C\nz."
        self.assertEqual(len(chunk_structure(doc, size=1000, overlap=0, min_size=200)), 1)
        self.assertEqual([c.text for c in chunk_structure(doc, size=10, overlap=0, min_size=8)],
                         ["# A\nx.", "# B\ny.", "# C\nz."])

    def test_no_heading_falls_back_to_recursive(self):
        doc = make_document()
        structure = chunk_structure(doc, size=300, overlap=50)
        recursive = chunk_recursive(doc, size=300, overlap=50)
        self.assertEqual([(c.start_char, c.end_char) for c in structure],
                         [(c.start_char, c.end_char) for c in recursive])
        self.assertTrue(all(c.metadata == {"heading": None, "heading_path": []} for c in structure))

    def test_hash_inside_code_block_is_not_a_heading(self):
        doc = "# Hướng dẫn\nĐoạn mở.\n```\n# đây là comment\nprint(1)\n```\nKết thúc."
        chunks = chunk_structure(doc, min_size=0)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].metadata["heading_path"], ["Hướng dẫn"])

    def test_invalid_parameters(self):
        for kwargs in [dict(size=0), dict(overlap=600), dict(min_size=-1), dict(size=100, overlap=0, min_size=101)]:
            with self.subTest(**kwargs):
                with self.assertRaises(ValueError):
                    chunk_structure("abc", **kwargs)


if __name__ == "__main__":
    unittest.main()
