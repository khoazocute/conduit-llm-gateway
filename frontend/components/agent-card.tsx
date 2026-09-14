import Link from "next/link";
import { AgentAvatar } from "@/components/agent-avatar";
import type { Agent } from "@/lib/api/types";

function formatVnd(amount: number) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount);
}

export function AgentCard({ agent }: { agent: Agent }) {
  return (
    <Link href={`/agents/${agent.id}`} className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div className="row" style={{ alignItems: "flex-start" }}>
        <AgentAvatar id={agent.id} title={agent.title} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: "var(--t-4)", fontWeight: 500 }}>{agent.title}</div>
        </div>
      </div>

      <p
        className="dim"
        style={{
          fontSize: "var(--t-3)",
          minHeight: 36,
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {agent.introduction ?? "No description provided."}
      </p>

      <div className="row" style={{ borderTop: "1px solid var(--border-soft)", paddingTop: 12 }}>
        <span className="mono" style={{ color: agent.price_vnd === 0 ? "var(--accent)" : "var(--text)" }}>
          {agent.price_vnd === 0 ? "Free" : formatVnd(agent.price_vnd)}
        </span>
        <span className="spacer" />
        <span className="faint mono" style={{ fontSize: "var(--t-1)" }}>
          +{agent.default_credit_granted} credit
        </span>
      </div>
    </Link>
  );
}
