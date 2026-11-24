"""Vẽ lại các sơ đồ của báo cáo cho khớp mã nguồn và văn bản (Hình 3.2, 3.3, 4.5, 4.7, 4.8, 4.10, 4.11, 4.13).

Sơ đồ khối dùng Graphviz (dot), sơ đồ tuần tự vẽ bằng matplotlib. Ảnh không có tiêu đề bên trong
(chú thích nằm dưới ảnh trong báo cáo). Chạy: python experiments/analysis/make_diagrams.py
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FONT = "Arial"


def dot(name: str, body: str, rankdir: str = "TB", dpi: int = 200) -> None:
    src = (
        f'digraph G {{ rankdir={rankdir}; dpi={dpi}; nodesep=0.35; ranksep=0.45;\n'
        f'node [shape=box, style="rounded,filled", fillcolor="#eef2ff", color="#6366f1", fontname="{FONT}", fontsize=12, margin="0.18,0.10"];\n'
        f'edge [fontname="{FONT}", fontsize=11, color="#374151"];\n{body}\n}}'
    )
    (OUT / f"{name}.dot").write_text(src, encoding="utf-8")
    subprocess.run(["dot", "-Tpng", str(OUT / f"{name}.dot"), "-o", str(OUT / f"{name}.png")], check=True)
    (OUT / f"{name}.dot").unlink()


def seq(name: str, actors: list[str], msgs: list[tuple], notes: dict[int, str] | None = None, width: float = 12.5) -> None:
    """msgs: (từ, đến, nhãn, kiểu) với kiểu '-' (gọi) hoặc '--' (trả về); từ==đến là tự gọi."""
    n = len(actors)
    xs = [i * (width / (n - 1)) for i in range(n)]
    h = 1.0 + 0.62 * len(msgs)
    fig, ax = plt.subplots(figsize=(width + 1.2, h))
    ax.set_xlim(-1.0, width + 1.0)
    ax.set_ylim(-h + 0.4, 0.9)
    ax.axis("off")
    for a, x in zip(actors, xs):
        ax.add_patch(FancyBboxPatch((x - 0.95, 0.15), 1.9, 0.55, boxstyle="round,pad=0.02", fc="#eef2ff", ec="#6366f1"))
        ax.text(x, 0.425, a, ha="center", va="center", fontsize=9.5)
        ax.plot([x, x], [0.15, -h + 0.5], color="#a5b4fc", lw=1.2, zorder=0)
    y = -0.2
    for i, (f, t, label, kind) in enumerate(msgs):
        xf, xt = xs[actors.index(f)], xs[actors.index(t)]
        if f == t:
            ax.annotate("", xy=(xf, y - 0.28), xytext=(xf, y), arrowprops=dict(arrowstyle="-|>", color="#374151", connectionstyle="arc3,rad=-1.4"))
            ax.text(xf + 0.35, y - 0.12, label, fontsize=8.8, va="center")
        else:
            ax.annotate("", xy=(xt, y), xytext=(xf, y), arrowprops=dict(arrowstyle="-|>", color="#374151", ls="--" if kind == "--" else "-"))
            ax.text((xf + xt) / 2, y + 0.07, label, fontsize=8.8, ha="center", va="bottom")
        y -= 0.62
    fig.savefig(OUT / f"{name}.png", dpi=190, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    # Hình 3.2
    dot("hinh-3-2-quy-trinh-danh-gia", '''
a [label="Giả thuyết nghiên cứu\\n(H1 đến H3, RQ1, RQ2)\\nghi ngày 14/10/2026, trước khi chạy", fillcolor="#dbeafe"];
b [label="Thực nghiệm có kiểm soát\\n80 câu × 3 proxy × 3 lần\\n= 720 lượt", fillcolor="#dcfce7", color="#16a34a"];
c [label="Quy tắc quyết định bốn bước\\nkhóa trước ngày 11/09/2026", fillcolor="#fef3c7", color="#d97706"];
d [label="Kết luận định lượng\\nchọn proxy tích hợp", fillcolor="#fee2e2", color="#dc2626"];
a -> b -> c -> d;''', rankdir="LR")
    # Hình 3.3
    dot("hinh-3-3-quy-tac-quyet-dinh", '''
s [label="Bắt đầu", shape=ellipse];
q1 [label="Tỷ lệ đạt gộp 4 bộ đề\\n< 80%?", shape=diamond, style=filled];
x [label="Loại proxy", fillcolor="#fee2e2", color="#dc2626"];
c2 [label="So sánh chi phí trung bình\\nmỗi câu hỏi"];
q2 [label="Chênh lệch chi phí\\ngiữa các proxy < 5%?", shape=diamond, style=filled];
r1 [label="Chọn proxy có chi phí thấp nhất", fillcolor="#dcfce7", color="#16a34a"];
q3 [label="Độ trễ p95 khác nhau?", shape=diamond, style=filled];
r2 [label="Chọn proxy có p95 thấp hơn", fillcolor="#dcfce7", color="#16a34a"];
r3 [label="Chọn proxy có routing consistency cao hơn", fillcolor="#dcfce7", color="#16a34a"];
dp [label="Không proxy nào qua bước 1 (luật dự phòng D13):\\nxếp theo chi phí trên mỗi câu đạt,\\nchọn thấp nhất", fillcolor="#fef3c7", color="#d97706"];
e [label="Kết thúc", shape=ellipse];
s -> q1; q1 -> x [label="Đúng"]; q1 -> c2 [label="Sai"]; c2 -> q2;
q2 -> r1 [label="Không"]; q2 -> q3 [label="Có"]; q3 -> r2 [label="Có"]; q3 -> r3 [label="Vẫn hòa"];
x -> e; r1 -> e; r2 -> e; r3 -> e;
x -> dp [style=dashed, label="nếu loại hết"]; dp -> e;''')
    # Hình 4.5
    dot("hinh-4-5-module", '''
g [label="LLM Gateway\\n(trục trung tâm)", fillcolor="#1e3a8a", fontcolor=white, color="#1e3a8a", fontsize=14];
m1 [label="Sàn agent\\n(Marketplace)"]; m2 [label="Tạo agent\\n(no-code)"]; m3 [label="Cơ sở tri thức RAG\\n(cấu hình được)"];
m4 [label="Thanh toán\\nvà ví credit"]; m5 [label="Quản trị\\n(Admin)"];
g -> {m1 m2 m3 m4 m5} [dir=none];
b [label="Bảo mật xuyên suốt: JWT, ABAC, AES-GCM, chữ ký webhook", shape=note, fillcolor="#fef9c3", color="#ca8a04"];
m5 -> b [style=invis];''', rankdir="TB")
    # Hình 4.8
    dot("hinh-4-8-pipeline-gateway", '''
n1 [label="1. Nhận yêu cầu chat kèm JWT"];
n2 [label="2. Xác thực và kiểm quyền sở hữu hội thoại (ABAC)"];
n3 [label="3. Lưu tin nhắn, nạp lịch sử,\\nghép chỉ dẫn riêng của agent làm lượt system"];
n4 [label="4. Gọi proxy qua ProxyChatClient (tối đa 45 giây)\\nproxy định tuyến, thử lại, fallbacks"];
e1 [label="Lỗi: ghi usage_logs và routing_decisions\\ntrạng thái error, không trừ credit,\\ngửi sự kiện SSE error", fillcolor="#fee2e2", color="#dc2626"];
n5 [label="5. Tính credit = ceil(token × hệ số),\\ntrừ ví (khóa lạc quan, thử lại tối đa 8 lần)"];
n6 [label="6. Ghi message, usage_logs, routing_decisions\\ntrong cùng một giao dịch"];
n7 [label="7. Gửi SSE: chunk rồi done", fillcolor="#dcfce7", color="#16a34a"];
n1 -> n2 -> n3 -> n4; n4 -> e1 [label="lỗi", style=dashed]; n4 -> n5 [label="có usage"]; n5 -> n6 -> n7;''')
    # Hình 4.11
    dot("hinh-4-11-pipeline-rag", '''
subgraph cluster_i { label="Luồng ingestion (khi Creator tải tài liệu)"; fontname="Arial"; style="rounded"; color="#16a34a";
 i1 [label="Đọc tài liệu"]; i2 [label="Chunking\\n(cố định có overlap, đệ quy, ngữ nghĩa)"];
 iv [label="Embedding\\ntext-embedding-3-small (1536 chiều)"]; ivs [label="kb_chunks (pgvector)\\nindex: không, IVFFlat, HNSW", shape=cylinder];
 ig [label="Trích thực thể và quan hệ\\n(gpt-4o-mini)"]; igs [label="Neo4j", shape=cylinder];
 i1 -> i2; i2 -> iv [label="vector"]; iv -> ivs; i2 -> ig [label="graph"]; ig -> igs; }
subgraph cluster_r { label="Luồng retrieval (khi User chat)"; fontname="Arial"; style="rounded"; color="#2563eb";
 r0 [label="Câu hỏi"]; r1 [label="Phân tích câu hỏi\\n(bước tùy chọn)", style="rounded,dashed,filled"];
 r2 [label="Truy hồi top_k\\n(cosine hoặc theo quan hệ)"]; r3 [label="Xếp hạng lại\\n(tùy chọn)", style="rounded,dashed,filled"];
 r4 [label="Ghép vào prompt như\\nngữ cảnh tham khảo"]; r5 [label="ProxyChatClient và LLM"]; r6 [label="Câu trả lời", fillcolor="#fed7aa", color="#ea580c"];
 r0 -> r1 -> r2 -> r3 -> r4 -> r5 -> r6; }
ivs -> r2 [style=dashed, label="agent_id"]; igs -> r2 [style=dashed];''')
    # Hình 4.13
    dot("hinh-4-13-so-do-trang", '''
home [label="/ Sàn agent"];
login [label="/login, /register"]; det [label="/agents/[id]\\nChi tiết agent"]; chat [label="/agents/[id]/chat\\nChat"]; lib [label="/library\\nAgent đã mua"]; wal [label="/wallet\\nVí credit"];
dash [label="/dashboard\\nBảng điều khiển Creator"]; new [label="/dashboard/agents/new\\nTạo agent"]; edit [label="/dashboard/agents/[id]/edit\\nSửa agent"];
ad1 [label="/admin/agents\\nDuyệt agent"]; ad2 [label="/admin/users\\nNgười dùng"]; ad3 [label="/admin/api-keys\\nAPI key"]; ad4 [label="/admin/model-pricing\\nBảng giá"];
home -> {login det lib wal dash}; det -> chat; dash -> {new edit};
home -> {ad1 ad2 ad3 ad4} [label="Admin"];''', rankdir="TB")

    seq("hinh-4-7-tuan-tu-chat", ["User", "Frontend", "Backend Gateway", "Routing proxy", "Nhà cung cấp LLM", "PostgreSQL"], [
        ("User", "Frontend", "Gửi tin nhắn", "-"),
        ("Frontend", "Backend Gateway", "POST /conversations/{id}/messages (JWT)", "-"),
        ("Backend Gateway", "Backend Gateway", "Xác thực JWT, kiểm quyền sở hữu hội thoại", "-"),
        ("Backend Gateway", "PostgreSQL", "Lưu tin nhắn, nạp lịch sử, chỉ dẫn agent", "-"),
        ("Backend Gateway", "Routing proxy", "complete(model, lịch sử)", "-"),
        ("Routing proxy", "Nhà cung cấp LLM", "Gọi API (định tuyến, thử lại, fallbacks)", "-"),
        ("Nhà cung cấp LLM", "Routing proxy", "Câu trả lời và usage", "--"),
        ("Routing proxy", "Backend Gateway", "Nội dung, mô hình thật, token", "--"),
        ("Backend Gateway", "PostgreSQL", "Một giao dịch: trừ credit, ghi message, usage_logs, routing_decisions", "-"),
        ("Backend Gateway", "Frontend", "SSE: chunk, done (lỗi hoặc hết credit: SSE error)", "--"),
        ("Frontend", "User", "Hiển thị câu trả lời", "--"),
    ])
    seq("hinh-4-10-tuan-tu-webhook", ["Mock Payment Gateway", "Backend (webhook)", "PostgreSQL"], [
        ("Mock Payment Gateway", "Backend (webhook)", "POST /payments/webhook/mock, X-Webhook-Signature", "-"),
        ("Backend (webhook)", "Backend (webhook)", "Kiểm chữ ký HMAC-SHA256", "-"),
        ("Backend (webhook)", "PostgreSQL", "Sai hoặc thiếu chữ ký: ghi log invalid_signature", "-"),
        ("Backend (webhook)", "Mock Payment Gateway", "HTTP 400, không cộng credit", "--"),
        ("Backend (webhook)", "PostgreSQL", "Chữ ký đúng: tìm đơn theo transaction_ref (UNIQUE)", "-"),
        ("Backend (webhook)", "PostgreSQL", "Đơn không còn pending: ghi log duplicate", "-"),
        ("Backend (webhook)", "Mock Payment Gateway", "HTTP 200 (duplicate), không cộng credit lần hai", "--"),
        ("Backend (webhook)", "PostgreSQL", "Đơn pending: paid hoặc failed, cộng credit khi paid, log accepted", "-"),
        ("Backend (webhook)", "Mock Payment Gateway", "HTTP 200 (accepted)", "--"),
    ], width=11)
    print("saved", OUT)


if __name__ == "__main__":
    main()
