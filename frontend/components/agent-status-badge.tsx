import type { AgentStatus } from "@/lib/api/types";

const STATUS_LABEL: Record<AgentStatus, string> = {
  draft: "draft",
  pending: "pending review",
  approved: "approved",
  rejected: "rejected",
  published: "published",
  unpublished: "unpublished",
};

const STATUS_CLASS: Record<AgentStatus, string> = {
  draft: "badge",
  pending: "badge badge-warn",
  approved: "badge badge-accent",
  rejected: "badge badge-danger",
  published: "badge badge-accent",
  unpublished: "badge",
};

export function AgentStatusBadge({ status }: { status: AgentStatus }) {
  return (
    <span className={STATUS_CLASS[status]}>
      <span className="badge-dot" />
      {STATUS_LABEL[status]}
    </span>
  );
}
