import Link from "next/link";
import { notFound } from "next/navigation";
import { AgentAvatar } from "@/components/agent-avatar";
import { AgentStatusBadge } from "@/components/agent-status-badge";
import { PurchaseAgentButton } from "@/components/purchase-agent-button";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import type { Agent } from "@/lib/api/types";

interface AgentDetailPageProps {
  params: Promise<{ id: string }>;
}

function formatVnd(amount: number) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount);
}

export default async function AgentDetailPage({ params }: AgentDetailPageProps) {
  const { id } = await params;

  let agent: Agent;
  try {
    agent = await apiFetch<Agent>(`/agents/${id}`);
  } catch (err) {
    if (err instanceof ApiClientError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  return (
    <div className="page" style={{ maxWidth: 720 }}>
      <div className="page-header">
        <div className="row" style={{ alignItems: "flex-start", gap: 16 }}>
          <AgentAvatar id={agent.id} title={agent.title} size={52} />
          <div>
            <div className="page-eyebrow">
              <span className="accent">●</span> conduit://agents/{agent.id.slice(0, 8)}
            </div>
            <div className="row" style={{ gap: 10 }}>
              <h1 className="page-title">{agent.title}</h1>
              <AgentStatusBadge status={agent.status} />
            </div>
          </div>
        </div>
      </div>

      <div className="card stack-md">
        <p style={{ whiteSpace: "pre-wrap", color: "var(--text-dim)" }}>
          {agent.introduction ?? "No description provided."}
        </p>
        <div className="divider" />
        <div className="row">
          <span className="mono" style={{ fontSize: "var(--t-6)", color: agent.price_vnd === 0 ? "var(--accent)" : "var(--text)" }}>
            {agent.price_vnd === 0 ? "Free" : formatVnd(agent.price_vnd)}
          </span>
          <span className="spacer" />
          <span className="faint mono" style={{ fontSize: "var(--t-2)" }}>
            Grants {agent.default_credit_granted} credit on purchase
          </span>
        </div>
        <div className="divider" />
        <div className="row" style={{ gap: 10 }}>
          <PurchaseAgentButton agentId={agent.id} priceVnd={agent.price_vnd} />
          <Link href={`/agents/${agent.id}/chat`} className="btn btn-ghost">
            Chat
          </Link>
        </div>
      </div>
    </div>
  );
}
