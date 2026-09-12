# Conduit — LLM Gateway Portal & AI Agent Marketplace

Khóa luận tốt nghiệp UIT (Nguyễn Văn Lê Hùng, Võ Đăng Khoa). Conduit là một LLM
Gateway Portal kiêm sàn AI Agent Marketplace, dùng làm testbed cho đóng góp
khoa học chính: **đánh giá thực nghiệm và lựa chọn 1 trong 3 routing proxy mã
nguồn mở (LiteLLM, Bifrost, Portkey AI Gateway)**. Chi tiết đầy đủ về đề tài,
thiết kế thí nghiệm, tech stack, data model, quy ước code: xem [CLAUDE.md](CLAUDE.md).

## Setup lần đầu (Khoa đọc phần này trước khi code)

Yêu cầu máy: Java 21, Node 18+, Python 3.11+, Docker Desktop đang chạy (mở app
lên, đợi icon hết xoay). Không cần cài Maven/Gradle riêng — dùng wrapper
(`./mvnw`) có sẵn trong repo.

```bash
git clone <repo-url>
cd conduit-llm-gateway
cp .env.example .env   # điền OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY / LITELLM_MASTER_KEY nếu có, không thì để placeholder cũng chạy được hạ tầng
docker compose up -d
```

Lệnh trên bật 7 container: Postgres (pgvector), pgAdmin, Redis, 3 proxy
(litellm/bifrost/portkey). **Chạy `docker compose` phải đứng đúng trong thư mục
`conduit-llm-gateway`** (nơi có file `docker-compose.yml`) — lỗi "no
configuration file provided" nghĩa là đang đứng sai thư mục.

Postgres lúc này còn **rỗng, chưa có bảng**. Chạy backend 1 lần để Flyway tự
tạo schema:

```bash
cd backend-gateway
./mvnw spring-boot:run
```

Đợi thấy dòng `Started BackendGatewayApplication` là 15 bảng đã được tạo xong
(migration nằm ở `backend-gateway/src/main/resources/db/migration/`, tự chạy
mỗi lần backend khởi động, không cần thao tác gì thêm). Có thể Ctrl+C dừng lại
sau đó — chỉ cần chạy 1 lần để tạo bảng, các lần sau chạy lại backend bình
thường để code.

**Xem bảng vừa tạo:** mở `http://localhost:5050` (pgAdmin) → đăng nhập
`admin@conduit.dev` / `admin` → mở server "Conduit (docker-compose)" (server
đã pre-fill sẵn host/port/db/user, chỉ cần nhập password Postgres là `conduit`
lúc kết nối lần đầu) → `Databases > conduit > Schemas > public > Tables`.

Entity + repository JPA cho toàn bộ 12 bảng đã có sẵn ở
`backend-gateway/src/main/java/com/conduit/backendgateway/{domain,repository}/`
— **không viết lại**, chỉ thêm service/controller theo `docs/openapi.json`
(xem phần "API contract" bên dưới để biết vertical nào phụ trách bảng nào).

Xong việc, `docker compose down` là đủ — data trong volume Postgres vẫn giữ
nguyên (không cần chạy lại migration ở lần `up` kế tiếp, trừ khi có migration
mới `V3...`). Chỉ dùng `docker compose down -v` nếu cố ý muốn xoá sạch data.

## Cấu trúc monorepo

```
backend-gateway/   Spring Boot 3 (Java 21, Maven) — Gateway chính
ai-service/        FastAPI (Python) — RAG, Should-have
frontend/          Next.js + TypeScript + Tailwind — Portal
proxy-configs/     Config cho 3 proxy đánh giá (litellm/bifrost/portkey)
experiments/       Thực nghiệm đánh giá proxy (prompts, scripts, results, analysis)
docs/              ERD (erd.dbml), API contract (openapi.json), tài liệu proposal
scripts/           Tiện ích chung (migration, seed data...)
```

## Port tra cứu nhanh (đã bật bằng `docker compose up -d` ở phần Setup)

- Postgres (pgvector): `localhost:5432`, db `conduit`, user/pass `conduit`
- Redis: `localhost:16379` (không phải 6379 mặc định — Windows/Hyper-V hay loại
  trừ động dải cổng quanh 6379, xem chú thích trong `docker-compose.yml`)
- LiteLLM: `localhost:4000`
- Bifrost: `localhost:8080`
- Portkey: `localhost:8787`
- pgAdmin (UI xem Postgres qua trình duyệt, kiểu MySQL Workbench): `localhost:5050`
  — xem hướng dẫn đăng nhập ở phần Setup phía trên.

## API contract

`docs/openapi.json` (OpenAPI 3.0.3) — thống nhất trước endpoint/request/response
giữa 2 người trước khi code backend + frontend, dựng từ `docs/erd.dbml`. Paste vào
[editor.swagger.io](https://editor.swagger.io) để xem dạng UI dễ đọc hơn. Chia việc
theo vertical (mỗi người làm cả backend lẫn frontend cho phần của mình, không chia
theo mảng thuần):

- **Hùng — Auth + Agent**: entity `users`/`agents`, JWT, CRUD agent + luồng duyệt,
  admin quản lý user/agent. Trang login/register, sàn agent, trang creator, trang
  admin duyệt agent. Tag: `Auth`, `Users`, `Agents`, `Admin - Agents`, `Admin - Users`.
- **Khoa — Credit + Chat + Payment**: entity `credit_wallets`/`credit_transactions`/
  `agent_purchases`/`payment_webhook_logs`/`conversations`/`messages`/`api_keys`/
  `model_pricing`, Provider Adapter (OpenAI/Anthropic), webhook mock idempotent, chat
  streaming SSE. Ví credit, luồng mua agent, màn chat, admin API key/bảng giá. Tag:
  `Wallet`, `Purchases & Payment`, `Conversations & Chat`, `Admin - API Keys`,
  `Admin - Model Pricing`.

Việc chung làm sau khi 2 vertical ổn định: `call_proxy()` thật trong
`experiments/scripts/run_experiment.py` + 30 prompt/rubric chấm mù trong
`experiments/prompts/`.

Cho phép sai số ±3 endpoint khi code thực tế — nếu đổi field đã thống nhất thì báo
lại cho người còn lại.

## Chạy từng service

**Backend Gateway**: xem lệnh `./mvnw spring-boot:run` ở phần Setup phía trên
(cần Postgres đang chạy qua `docker compose up -d`).

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
