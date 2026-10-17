# Vendor — code của bên thứ ba, giữ nguyên văn

## `instruction_following_eval/` — verifier chính thức của IFEval

- **Nguồn:** https://github.com/google-research/google-research/tree/master/instruction_following_eval
- **Paper:** Zhou et al. 2023, *Instruction-Following Evaluation for Large Language Models* (arXiv:2311.07911)
- **Giấy phép:** Apache-2.0 — header gốc giữ nguyên trong từng file
- **Tải về:** 2026-10-14
- **File:** `instructions.py`, `instructions_registry.py`, `instructions_util.py`

**Vendor nguyên văn, KHÔNG sửa logic.** Lý do: yêu cầu của thầy là tiêu chí đánh giá phải chuẩn
theo paper — nếu tự viết lại verifier thì metric không còn là metric của paper nữa. Bộ đề của nhóm
dùng **12 loại ràng buộc**, registry này có 25 loại nên phủ đủ (có test kiểm:
`experiments/tests/test_graders.py::IfEvalGrader::test_moi_verifier_cua_bo_de_that_deu_build_va_chay_duoc`).

Wrapper của nhóm nằm ở `experiments/analysis/graders.py::grade_ifeval` — chỉ gọi vào registry,
không can thiệp vào cách kiểm.

**Cần `nltk` corpus `punkt`/`punkt_tab`** mới chạy được 2 verifier tách câu — xem
`experiments/requirements.txt`.
