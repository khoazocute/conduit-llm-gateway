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
