"""TASK-67: lượt lỗi phải giữ được thông điệp lỗi backend gửi qua SSE.

Trước đây 0/32 lượt lỗi (experiment-results.md mục 9 + phép thử D15) không ghi được thông điệp nào:
runner gặp `event: error` là dừng đọc, bỏ qua dòng `data:` ngay sau, và record không có trường
`error`. Không gọi API, không cần backend.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_experiment import _read_sse_error_data  # noqa: E402


class ReadSseErrorData(unittest.TestCase):
    def test_lay_message_trong_data_json(self):
        lines = iter(['data:{"message":"Chat provider error: Proxy returned 401"}', ""])
        self.assertEqual(_read_sse_error_data(lines), "Chat provider error: Proxy returned 401")

    def test_data_khong_phai_json_thi_tra_nguyen_van(self):
        lines = iter(["data:upstream timeout", ""])
        self.assertEqual(_read_sse_error_data(lines), "upstream timeout")

    def test_khong_co_data_thi_none(self):
        self.assertIsNone(_read_sse_error_data(iter(["", "event:done"])))
        self.assertIsNone(_read_sse_error_data(iter([])))

    def test_dung_chung_iterator_voi_vong_doc_ngoai(self):
        """Lỗi gặp khi sửa TASK-67: gọi iter_lines() lần hai tạo iterator mới, dòng `data:` đã
        nằm trong bộ đệm của iterator cũ nên mất. Hàm phải đọc tiếp TỪ iterator được truyền vào."""
        lines = iter(["event:error", 'data:{"message":"boom"}', ""])
        self.assertEqual(next(lines), "event:error")  # vòng ngoài đã đọc dòng event
        self.assertEqual(_read_sse_error_data(lines), "boom")


if __name__ == "__main__":
    unittest.main()
