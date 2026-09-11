# Conduit — LLM Gateway Portal & AI Agent Marketplace

Khóa luận tốt nghiệp UIT (Nguyễn Văn Lê Hùng, Võ Đăng Khoa). Conduit là một LLM
Gateway Portal kiêm sàn AI Agent Marketplace, dùng làm testbed cho đóng góp
khoa học chính: **đánh giá thực nghiệm và lựa chọn 1 trong 3 routing proxy mã
nguồn mở (LiteLLM, Bifrost, Portkey AI Gateway)**. Chi tiết đầy đủ về đề tài,
thiết kế thí nghiệm, tech stack, data model, quy ước code: xem [CLAUDE.md](CLAUDE.md).

## Cấu trúc monorepo

```
backend-gateway/   Spring Boot 3 (Java 21, Maven) — Gateway chính
ai-service/        FastAPI (Python) — RAG, Should-have
frontend/          Next.js + TypeScript + Tailwind — Portal
proxy-configs/     Config cho 3 proxy đánh giá (litellm/bifrost/portkey)
experiments/       Thực nghiệm đánh giá proxy (prompts, scripts, results, analysis)
docs/              ERD, tài liệu proposal
scripts/           Tiện ích chung (migration, seed data...)
```

## Chạy hạ tầng (Postgres + pgvector, Redis, 3 proxy)

```bash
cp .env.example .env   # điền OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY / LITELLM_MASTER_KEY
docker compose up -d
```

- Postgres (pgvector): `localhost:5432`, db `conduit`, user/pass `conduit`
- Redis: `localhost:16379` (không phải 6379 mặc định — Windows/Hyper-V hay loại
  trừ động dải cổng quanh 6379, xem chú thích trong `docker-compose.yml`)
- LiteLLM: `localhost:4000`
- Bifrost: `localhost:8080`
- Portkey: `localhost:8787`

## Chạy từng service

**Backend Gateway** (cần Postgres/Redis đang chạy):

```bash
cd backend-gateway
./mvnw spring-boot:run
```

**AI Service**:

```bash
cd ai-service
python -m venv .venv
.venv/Scripts/activate   # Windows; source .venv/bin/activate trên macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**:

```bash
cd frontend
npm run dev
```

## Thực nghiệm đánh giá proxy

Xem `experiments/README` (nếu có) hoặc CLAUDE.md mục 2 cho quy trình đầy đủ:
30 prompt × 3 proxy × 3 lần lặp, áp dụng quy tắc quyết định 4 bước.

```bash
cd experiments/scripts
pip install -r requirements.txt
python run_experiment.py
python ../analysis/decision_rule.py ../results/<file>.json
```
