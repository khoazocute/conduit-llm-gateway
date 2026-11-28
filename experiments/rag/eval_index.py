"""TASK-75/76: đánh giá 3 cách index của pgvector — quét toàn bộ, IVFFlat, HNSW.

Chạy trên database RIÊNG (mặc định `conduit_eval`, cùng container conduit-postgres), không đụng dữ liệu
Conduit. Bảng thử `eval_vectors(id, agent_id, embedding vector(1536))` mô phỏng `kb_chunks`: vector
thuộc về nhiều agent, truy vấn thật của Conduit luôn lọc `WHERE agent_id = ...`.

Nguồn vector:
  --source synthetic  vector tổng hợp có cụm, MIỄN PHÍ. Chỉ để chạy thử script; KHÔNG dùng làm kết quả
                      báo cáo (vector tổng hợp không có cấu trúc như embedding thật).
  --source npy        vector thật (vd BEIR-FiQA embedding bằng text-embedding-3-small), file .npy do
                      script khác tạo (có phí, cần duyệt D1).

Đo cho từng cấu hình:
  - recall@k so với top-k CHÍNH XÁC (tính bằng numpy, độc lập với DB);
  - độ trễ truy vấn phía server (EXPLAIN ANALYZE "Execution Time"): trung bình, p50, p95;
  - tỉ lệ truy vấn trả THIẾU kết quả (vấn đề lọc sau của index khi có WHERE agent_id);
  - tỉ lệ truy vấn planner thực sự dùng index vector;
  - thời gian tạo index, dung lượng index.

Ví dụ chạy thử:
  experiments/rag/.venv/Scripts/python experiments/rag/eval_index.py --source synthetic --n 20000
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import pathlib
import sys
import time

import numpy as np
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from pgvector.psycopg import register_vector

DIM = 1536  # khớp kb_chunks.embedding vector(1536), text-embedding-3-small
TABLE = "eval_vectors"
ANN_INDEX = "eval_vectors_ann"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dsn", default="postgresql://conduit:conduit@localhost:5432/conduit_eval",
                   help="DB dùng để thử (sẽ được tạo nếu chưa có)")
    p.add_argument("--admin-dsn", default="postgresql://conduit:conduit@localhost:5432/conduit",
                   help="DB có sẵn để chạy CREATE DATABASE")
    p.add_argument("--source", choices=["synthetic", "npy"], default="synthetic")
    p.add_argument("--vectors", help="--source npy: file .npy (n x 1536) vector tài liệu")
    p.add_argument("--queries", help="--source npy: file .npy (m x 1536) vector câu hỏi")
    p.add_argument("--n", type=int, default=20000, help="synthetic: số vector tài liệu")
    p.add_argument("--clusters", type=int, default=200, help="synthetic: số cụm chủ đề")
    p.add_argument("--noise", type=float, default=0.6, help="synthetic: độ tản trong cụm (chuẩn vector nhiễu)")
    p.add_argument("--agents", type=int, default=50, help="số agent mô phỏng")
    p.add_argument("--zipf", type=float, default=1.1, help="độ lệch kích thước agent (Zipf): vài agent lớn, nhiều agent nhỏ")
    p.add_argument("--num-queries", type=int, default=200)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ivf-lists", type=int, default=0, help="0 = theo README pgvector: rows/1000 (<= 1M dòng)")
    p.add_argument("--ivf-probes", default="1,2,4,8,16")
    p.add_argument("--hnsw-m", type=int, default=16)
    p.add_argument("--hnsw-ef-construction", type=int, default=64)
    p.add_argument("--hnsw-ef-search", default="10,20,40,80,160")
    p.add_argument("--maintenance-work-mem", default="1GB")
    p.add_argument("--parallel-workers", type=int, default=0,
                   help="max_parallel_maintenance_workers khi tạo index. 0 = tuần tự: tạo song song cần "
                        "shared memory lớn, Docker mặc định /dev/shm chỉ 64MB nên dễ lỗi")
    p.add_argument("--out", help="thư mục kết quả (mặc định experiments/rag/results/index-<source>-<thời gian>)")
    p.add_argument("--keep-table", action="store_true", help="giữ bảng thử sau khi chạy")
    return p.parse_args()


# ---------------------------------------------------------------------------------------------
# Dữ liệu
# ---------------------------------------------------------------------------------------------


def unit(x: np.ndarray) -> np.ndarray:
    return (x / np.linalg.norm(x, axis=1, keepdims=True)).astype(np.float32)


def synthetic_data(rng, n, num_queries, clusters, noise):
    """Hỗn hợp cụm trên mặt cầu: tâm cụm ngẫu nhiên + nhiễu. Câu hỏi lấy từ CÙNG phân phối."""
    centers = unit(rng.standard_normal((clusters, DIM)))

    def sample(count):
        which = rng.integers(0, clusters, count)
        jitter = rng.standard_normal((count, DIM)).astype(np.float32) * (noise / math.sqrt(DIM))
        return unit(centers[which] + jitter)

    return sample(n), sample(num_queries)


def load_npy(vectors_path, queries_path, rng, num_queries):
    x = np.load(vectors_path).astype(np.float32)
    q = np.load(queries_path).astype(np.float32)
    if x.shape[1] != DIM or q.shape[1] != DIM:
        sys.exit(f"Expected {DIM}-dim vectors, got {x.shape} and {q.shape}")
    if len(q) > num_queries:
        q = q[rng.choice(len(q), num_queries, replace=False)]
    return unit(x), unit(q)


def zipf_agents(rng, count, agents, s):
    weights = 1.0 / np.arange(1, agents + 1) ** s
    return rng.choice(agents, count, p=weights / weights.sum()).astype(np.int32)


def exact_topk(x, q, k, data_agents, query_agent=None):
    """Top-k chính xác theo cosine (vector đã chuẩn hóa: cosine = tích vô hướng)."""
    candidates = np.arange(len(x)) if query_agent is None else np.flatnonzero(data_agents == query_agent)
    sims = x[candidates] @ q
    top = np.argsort(-sims)[:k]
    return candidates[top].tolist()


# ---------------------------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------------------------


def ensure_database(admin_dsn: str, dsn: str) -> None:
    dbname = conninfo_to_dict(dsn)["dbname"]
    if dbname == conninfo_to_dict(admin_dsn).get("dbname"):
        sys.exit("--dsn must point to a separate evaluation database, not the application database")
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)).fetchone():
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))


def load_table(conn, x, data_agents) -> None:
    conn.execute(f"DROP TABLE IF EXISTS {TABLE}")
    conn.execute(f"CREATE TABLE {TABLE} (id integer PRIMARY KEY, agent_id integer NOT NULL,"
                 f" embedding vector({DIM}) NOT NULL)")
    with conn.cursor().copy(f"COPY {TABLE} (id, agent_id, embedding) FROM STDIN WITH (FORMAT BINARY)") as copy:
        copy.set_types(["int4", "int4", "vector"])
        for i in range(len(x)):
            copy.write_row((i, int(data_agents[i]), x[i]))
    # Giống kb_chunks: có btree trên agent_id (idx_kb_chunks_agent_id).
    conn.execute(f"CREATE INDEX {TABLE}_agent_idx ON {TABLE} (agent_id)")
    conn.execute(f"ANALYZE {TABLE}")


def vector_literal(v: np.ndarray) -> str:
    # 9 chữ số có nghĩa đủ để float32 đi-về không sai lệch. Chỉ chứa số nên an toàn khi ghép vào SQL.
    return "[" + ",".join(f"{float(a):.9g}" for a in v) + "]"


def query_sql(literal: str, k: int, agent: int | None) -> str:
    where = "" if agent is None else f" WHERE agent_id = {int(agent)}"
    return f"SELECT id FROM {TABLE}{where} ORDER BY embedding <=> '{literal}'::vector LIMIT {int(k)}"


def run_one(conn, literal, k, agent):
    q = query_sql(literal, k, agent)
    ids = [row[0] for row in conn.execute(q)]
    plan = conn.execute("EXPLAIN (ANALYZE, FORMAT JSON) " + q).fetchone()[0][0]
    uses_ann = ANN_INDEX in json.dumps(plan)
    return ids, float(plan["Execution Time"]), uses_ann


# ---------------------------------------------------------------------------------------------
# Đo
# ---------------------------------------------------------------------------------------------


def measure(conn, label, params, settings, queries, literals, truth, k, query_agents, scope, per_query):
    for s in settings:
        conn.execute(s)
    # Làm nóng cache: 20 truy vấn đầu, không tính.
    for i in range(min(20, len(queries))):
        conn.execute(query_sql(literals[i], k, None if scope == "global" else query_agents[i])).fetchall()

    recalls, latencies, short, ann = [], [], 0, 0
    for i in range(len(queries)):
        agent = None if scope == "global" else int(query_agents[i])
        ids, ms, uses_ann = run_one(conn, literals[i], k, agent)
        expected = truth[scope][i]
        recall = len(set(ids) & set(expected)) / len(expected) if expected else 1.0
        recalls.append(recall)
        latencies.append(ms)
        short += len(ids) < len(expected)
        ann += uses_ann
        per_query.append({"index": label, **params, "scope": scope, "query": i, "agent": agent,
                          "expected": len(expected), "returned": len(ids), "recall": round(recall, 4),
                          "latency_ms": round(ms, 3), "uses_ann_index": uses_ann})
    lat = np.array(latencies)
    row = {
        "index": label, **params, "scope": scope,
        "recall_at_k": round(float(np.mean(recalls)), 4),
        "latency_mean_ms": round(float(lat.mean()), 3),
        "latency_p50_ms": round(float(np.percentile(lat, 50)), 3),
        "latency_p95_ms": round(float(np.percentile(lat, 95)), 3),
        "short_result_rate": round(short / len(queries), 4),
        "ann_plan_rate": round(ann / len(queries), 4),
    }
    print(f"  {label:8} {json.dumps(params):55} {scope:8} recall@{k}={row['recall_at_k']:.3f}"
          f"  mean={row['latency_mean_ms']:.2f}ms p95={row['latency_p95_ms']:.2f}ms"
          f"  short={row['short_result_rate']:.2f} ann_plan={row['ann_plan_rate']:.2f}")
    return row


def build_index(conn, label, ddl):
    conn.execute(f"DROP INDEX IF EXISTS {ANN_INDEX}")
    start = time.perf_counter()
    conn.execute(ddl)
    seconds = time.perf_counter() - start
    conn.execute(f"ANALYZE {TABLE}")
    size = conn.execute(f"SELECT pg_relation_size('{ANN_INDEX}')").fetchone()[0]
    print(f"[build] {label}: {seconds:.1f}s, {size / 2**20:.1f} MB")
    return {"index": label, "ddl": ddl, "build_seconds": round(seconds, 2), "size_mb": round(size / 2**20, 2)}


def write_csv(path: pathlib.Path, rows: list[dict]) -> None:
    fields: list[str] = []
    for r in rows:
        fields += [f for f in r if f not in fields]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = pathlib.Path(args.out or f"experiments/rag/results/index-{args.source}-{stamp}")
    out.mkdir(parents=True, exist_ok=True)

    if args.source == "synthetic":
        x, q = synthetic_data(rng, args.n, args.num_queries, args.clusters, args.noise)
    else:
        if not (args.vectors and args.queries):
            sys.exit("--source npy requires --vectors and --queries")
        x, q = load_npy(args.vectors, args.queries, rng, args.num_queries)
    data_agents = zipf_agents(rng, len(x), args.agents, args.zipf)
    query_agents = zipf_agents(rng, len(q), args.agents, args.zipf)
    k = args.k
    print(f"data={len(x)} queries={len(q)} agents={args.agents} k={k} source={args.source}")

    truth = {
        "global": [exact_topk(x, qi, k, data_agents) for qi in q],
        "agent": [exact_topk(x, qi, k, data_agents, int(a)) for qi, a in zip(q, query_agents)],
    }
    literals = [vector_literal(qi) for qi in q]

    ensure_database(args.admin_dsn, args.dsn)
    conn = psycopg.connect(args.dsn, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    versions = {
        "pgvector": conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()[0],
        "postgres": conn.execute("SHOW server_version").fetchone()[0],
    }
    print(f"pgvector {versions['pgvector']}, PostgreSQL {versions['postgres']}; loading table...")
    t0 = time.perf_counter()
    load_table(conn, x, data_agents)
    print(f"loaded in {time.perf_counter() - t0:.1f}s")
    conn.execute(f"SET maintenance_work_mem = '{args.maintenance_work_mem}'")
    conn.execute(f"SET max_parallel_maintenance_workers = {int(args.parallel_workers)}")

    summary, per_query, builds = [], [], []

    # 1. Không index vector: quét toàn bộ (với lọc agent thì planner dùng btree agent_id + sắp xếp).
    conn.execute(f"DROP INDEX IF EXISTS {ANN_INDEX}")
    builds.append({"index": "none", "ddl": "", "build_seconds": 0, "size_mb": 0})
    for scope in ("global", "agent"):
        summary.append(measure(conn, "none", {}, [], q, literals, truth, k, query_agents, scope, per_query))

    # 2. IVFFlat: lists theo README pgvector (rows/1000 khi <= 1M dòng, sqrt(rows) khi lớn hơn).
    if args.ivf_lists:
        lists = args.ivf_lists
    elif len(x) <= 1_000_000:
        lists = max(1, round(len(x) / 1000))
    else:
        lists = round(math.sqrt(len(x)))
    builds.append(build_index(conn, "ivfflat", f"CREATE INDEX {ANN_INDEX} ON {TABLE} USING ivfflat"
                              f" (embedding vector_cosine_ops) WITH (lists = {lists})"))
    for probes in [int(p) for p in args.ivf_probes.split(",") if int(p) <= lists]:
        base = [f"SET ivfflat.probes = {probes}"]
        params = {"lists": lists, "probes": probes}
        summary.append(measure(conn, "ivfflat", {**params, "iterative_scan": "off"},
                               base + ["SET ivfflat.iterative_scan = off"], q, literals, truth, k,
                               query_agents, "global", per_query))
        for mode in ("off", "relaxed_order"):
            summary.append(measure(conn, "ivfflat", {**params, "iterative_scan": mode},
                                   base + [f"SET ivfflat.iterative_scan = {mode}"], q, literals, truth, k,
                                   query_agents, "agent", per_query))

    # 3. HNSW: đồ thị nhiều tầng; ef_search = độ rộng tìm kiếm lúc truy vấn.
    builds.append(build_index(conn, "hnsw", f"CREATE INDEX {ANN_INDEX} ON {TABLE} USING hnsw"
                              f" (embedding vector_cosine_ops) WITH (m = {args.hnsw_m},"
                              f" ef_construction = {args.hnsw_ef_construction})"))
    for ef in [int(e) for e in args.hnsw_ef_search.split(",")]:
        base = [f"SET hnsw.ef_search = {ef}"]
        params = {"m": args.hnsw_m, "ef_construction": args.hnsw_ef_construction, "ef_search": ef}
        summary.append(measure(conn, "hnsw", {**params, "iterative_scan": "off"},
                               base + ["SET hnsw.iterative_scan = off"], q, literals, truth, k,
                               query_agents, "global", per_query))
        for mode in ("off", "relaxed_order"):
            summary.append(measure(conn, "hnsw", {**params, "iterative_scan": mode},
                                   base + [f"SET hnsw.iterative_scan = {mode}"], q, literals, truth, k,
                                   query_agents, "agent", per_query))

    agent_sizes = np.bincount(data_agents, minlength=args.agents)
    run_info = {
        "timestamp": stamp, "args": vars(args), "versions": versions, "dim": DIM,
        "num_vectors": len(x), "num_queries": len(q), "ivf_lists": lists,
        "agent_size_min": int(agent_sizes.min()), "agent_size_median": int(np.median(agent_sizes)),
        "agent_size_max": int(agent_sizes.max()),
        "note": "synthetic = chỉ chạy thử script, không phải kết quả báo cáo" if args.source == "synthetic" else "",
    }
    (out / "run_info.json").write_text(json.dumps(run_info, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(out / "summary.csv", summary)
    write_csv(out / "build.csv", builds)
    write_csv(out / "per_query.csv", per_query)

    if not args.keep_table:
        conn.execute(f"DROP TABLE IF EXISTS {TABLE}")
    conn.close()
    print(f"results -> {out}")


if __name__ == "__main__":
    main()
