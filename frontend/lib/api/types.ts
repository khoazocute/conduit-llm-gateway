export type UserRole = "admin" | "creator" | "user";
export type UserStatus = "active" | "banned";
export type AgentType = "text";
export type AgentStatus =
  | "draft"
  | "pending"
  | "approved"
  | "rejected"
  | "published"
  | "unpublished";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: UserRole;
  status: UserStatus;
  email_verified: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  expires_in: number;
  user: User;
}

export interface Agent {
  id: string;
  creator_id: string;
  title: string;
  introduction: string | null;
  agent_type: AgentType;
  price_vnd: number;
  default_credit_granted: number;
  status: AgentStatus;
  reject_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface PageMeta {
  page: number;
  size: number;
  total_elements: number;
  total_pages: number;
}

export interface AgentListResponse {
  items: Agent[];
  page: PageMeta;
}

export interface UserListResponse {
  items: User[];
  page: PageMeta;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface CreditWallet {
  id: string;
  user_id: string;
  balance: number;
  updated_at: string;
}

export type CreditTxType = "purchase_grant" | "usage_deduct" | "topup" | "refund_deduct";

export interface CreditTransaction {
  id: string;
  wallet_id: string;
  type: CreditTxType;
  amount: number;
  related_message_id: string | null;
  related_purchase_id: string | null;
  description: string | null;
  created_at: string;
}

export interface CreditTransactionListResponse {
  items: CreditTransaction[];
  page: PageMeta;
}

export type PaymentMethod = "vnpay" | "mock";
export type PaymentStatus = "pending" | "paid" | "failed" | "refunded";

export interface AgentPurchase {
  id: string;
  user_id: string;
  agent_id: string;
  amount_vnd: number;
  default_credit_granted: number;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  transaction_ref: string;
  paid_at: string | null;
  created_at: string;
}

export interface CreatePurchaseResponse {
  purchase: AgentPurchase;
  redirect_url: string | null;
}

export type LlmProvider = "openai" | "anthropic" | "google";
export type ApiKeyStatus = "active" | "rate_limited" | "disabled";

export interface ApiKey {
  id: string;
  provider: LlmProvider;
  status: ApiKeyStatus;
  priority: number;
  last_used_at: string | null;
  created_at: string;
}

export type UnitType = "token_input" | "token_output" | "image_generation";

export interface Conversation {
  id: string;
  user_id: string;
  agent_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  items: Conversation[];
  page: PageMeta;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string | null;
  credit_charged: number | null;
  model_used: string | null;
  latency_ms: number | null;
  created_at: string;
}

export interface MessageListResponse {
  items: ChatMessage[];
  page: PageMeta;
}

export interface ModelPricing {
  id: string;
  provider: LlmProvider;
  model: string;
  unit_type: UnitType;
  price_usd_per_unit: number;
  credit_markup_multiplier: number;
  effective_from: string;
  created_at: string;
}
