-- Init schema, dung tu docs/erd.dbml (ban goc do nguoi dung cung cap, khong tu suy dien).
-- Pham vi: toan bo bang Must-have + Should-have (RAG - knowledge_bases/kb_chunks).

CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;   -- pgvector, cho kb_chunks.embedding

CREATE TYPE user_role AS ENUM ('admin', 'creator', 'user');
CREATE TYPE user_status AS ENUM ('active', 'banned');
CREATE TYPE agent_type AS ENUM ('text');
CREATE TYPE agent_status AS ENUM ('draft', 'pending', 'approved', 'rejected', 'published', 'unpublished');
CREATE TYPE kb_status AS ENUM ('processing', 'ready', 'failed');
CREATE TYPE message_role AS ENUM ('user', 'assistant');
CREATE TYPE payment_method AS ENUM ('vnpay', 'mock');
CREATE TYPE payment_status AS ENUM ('pending', 'paid', 'failed', 'refunded');
CREATE TYPE webhook_result AS ENUM ('accepted', 'duplicate', 'invalid_signature');
CREATE TYPE credit_tx_type AS ENUM ('purchase_grant', 'usage_deduct', 'topup', 'refund_deduct');
CREATE TYPE api_key_status AS ENUM ('active', 'rate_limited', 'disabled');
CREATE TYPE llm_provider AS ENUM ('openai', 'anthropic', 'google');
CREATE TYPE usage_status AS ENUM ('success', 'fallback', 'error');
CREATE TYPE unit_type AS ENUM ('token_input', 'token_output', 'image_generation');
CREATE TYPE routing_proxy AS ENUM ('litellm', 'bifrost', 'portkey');

-- ============================================
-- 1. USERS & AUTH
-- ============================================

CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email varchar NOT NULL UNIQUE,
    password_hash varchar,
    full_name varchar,
    avatar_url varchar,
    role user_role NOT NULL DEFAULT 'user',
    status user_status NOT NULL DEFAULT 'active',
    email_verified boolean DEFAULT false,
    oauth_provider varchar,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================
-- 2. AGENT & KHO TRI THUC (RAG - knowledge_bases/kb_chunks la Should-have)
-- ============================================

CREATE TABLE agents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id uuid NOT NULL REFERENCES users(id),
    title varchar NOT NULL,
    introduction text,
    agent_type agent_type NOT NULL DEFAULT 'text',
    price_vnd int NOT NULL DEFAULT 0,
    default_credit_granted int NOT NULL DEFAULT 0,
    status agent_status NOT NULL DEFAULT 'draft',
    reject_reason varchar,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_agents_creator_id ON agents(creator_id);
CREATE INDEX idx_agents_status ON agents(status);

CREATE TABLE knowledge_bases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id uuid NOT NULL REFERENCES agents(id),
    file_name varchar NOT NULL,
    file_url varchar NOT NULL,
    status kb_status NOT NULL DEFAULT 'processing',
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_knowledge_bases_agent_id ON knowledge_bases(agent_id);

CREATE TABLE kb_chunks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id uuid NOT NULL REFERENCES knowledge_bases(id),
    agent_id uuid NOT NULL REFERENCES agents(id), -- denormalized, loc theo agent (RAG metadata filtering + tenant isolation)
    chunk_text text NOT NULL,
    chunk_index int,
    embedding vector(1536) NOT NULL, -- text-embedding-3-small
    source_file varchar,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_kb_chunks_knowledge_base_id ON kb_chunks(knowledge_base_id);
CREATE INDEX idx_kb_chunks_agent_id ON kb_chunks(agent_id);
-- TODO (Should-have): tao vector index (vd ivfflat) khi da co du lieu that de tune lists/probes.

-- ============================================
-- 3. VI CREDIT & GIAO DICH
-- ============================================

CREATE TABLE credit_wallets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL UNIQUE REFERENCES users(id),
    balance bigint NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================
-- 5. CHAT / CONVERSATION (tao truoc credit_transactions vi credit_transactions FK toi messages)
-- ============================================

CREATE TABLE conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id),
    agent_id uuid NOT NULL REFERENCES agents(id),
    title varchar,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);

CREATE TABLE messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL REFERENCES conversations(id),
    role message_role NOT NULL,
    content text,
    credit_charged int, -- null neu luot goi loi/retry khong tinh phi (CLAUDE.md muc 5)
    model_used varchar,
    latency_ms int,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

-- ============================================
-- 4. MUA AGENT & THANH TOAN (VNPay / Mock)
-- ============================================

CREATE TABLE agent_purchases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id),
    agent_id uuid NOT NULL REFERENCES agents(id),
    amount_vnd int NOT NULL,
    default_credit_granted int NOT NULL,
    payment_method payment_method NOT NULL DEFAULT 'vnpay',
    payment_status payment_status NOT NULL DEFAULT 'pending',
    transaction_ref varchar NOT NULL UNIQUE, -- idempotency
    paid_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_agent_purchases_user_id ON agent_purchases(user_id);
CREATE INDEX idx_agent_purchases_agent_id ON agent_purchases(agent_id);

CREATE TABLE payment_webhook_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_ref varchar NOT NULL,
    result webhook_result NOT NULL,
    raw_payload text,
    received_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_payment_webhook_logs_transaction_ref ON payment_webhook_logs(transaction_ref);

-- credit_transactions sau cung trong nhom 3 vi FK toi messages/agent_purchases
CREATE TABLE credit_transactions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id uuid NOT NULL REFERENCES credit_wallets(id),
    type credit_tx_type NOT NULL,
    amount bigint NOT NULL, -- duong = cong, am = tru
    related_message_id uuid REFERENCES messages(id),
    related_purchase_id uuid REFERENCES agent_purchases(id),
    description varchar,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_credit_transactions_wallet_id ON credit_transactions(wallet_id);

-- ============================================
-- 6. API KEY & PROVIDER (Admin quan ly)
-- ============================================

CREATE TABLE api_keys (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    provider llm_provider NOT NULL,
    key_encrypted text NOT NULL, -- AES-GCM, encryption key ngoai DB (env)
    status api_key_status NOT NULL DEFAULT 'active',
    priority int DEFAULT 0,
    last_used_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================
-- 7. LOGGING & MONITORING
-- ============================================

CREATE TABLE usage_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id uuid NOT NULL REFERENCES messages(id),
    api_key_id uuid REFERENCES api_keys(id),
    provider llm_provider,
    model varchar,
    token_input int,
    token_output int,
    cost_upstream numeric,
    revenue_credit numeric,
    latency_ms int,
    status usage_status NOT NULL DEFAULT 'success',
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_usage_logs_message_id ON usage_logs(message_id);

-- ============================================
-- 8. DINH GIA & DANH GIA ROUTING PROXY (dong gop chinh cua khoa luan)
-- ============================================

CREATE TABLE model_pricing (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    provider llm_provider NOT NULL,
    model varchar NOT NULL,
    unit_type unit_type NOT NULL,
    price_usd_per_unit numeric NOT NULL,
    credit_markup_multiplier numeric NOT NULL DEFAULT 1.5,
    effective_from timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_model_pricing_provider_model ON model_pricing(provider, model);

CREATE TABLE routing_decisions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id uuid NOT NULL REFERENCES messages(id),
    proxy_name routing_proxy NOT NULL,
    selected_model varchar NOT NULL,
    predicted_cost numeric NOT NULL,
    token_input int,
    token_output int,
    response_quality_score numeric,
    latency_ms int,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_routing_decisions_message_id ON routing_decisions(message_id);
CREATE INDEX idx_routing_decisions_proxy_name ON routing_decisions(proxy_name);
