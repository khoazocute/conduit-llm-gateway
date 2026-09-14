"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { AgentAvatar } from "@/components/agent-avatar";
import { useAuth } from "@/context/auth-context";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import type { Agent, AgentListResponse } from "@/lib/api/types";

function PendingAgentCard({
  agent,
  onApprove,
  onReject,
}: {
  agent: Agent;
  onApprove: () => Promise<void>;
  onReject: (reason: string) => Promise<void>;
}) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleApprove() {
    setBusy(true);
    try {
      await onApprove();
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    if (!reason.trim()) return;
    setBusy(true);
    try {
      await onReject(reason);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <div className="row" style={{ alignItems: "flex-start", marginBottom: 12 }}>
        <AgentAvatar id={agent.id} title={agent.title} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "var(--t-5)", fontWeight: 500 }}>{agent.title}</div>
          <div className="dim mono" style={{ fontSize: "var(--t-1)" }}>
            {agent.price_vnd === 0 ? "Free" : `${agent.price_vnd.toLocaleString("vi-VN")} VND`} · +
            {agent.default_credit_granted} credit
          </div>
        </div>
      </div>
      <p style={{ fontSize: "var(--t-3)", margin: "0 0 14px" }}>
        {agent.introduction ?? "No description provided."}
      </p>
      <textarea
        className="textarea"
        placeholder="Reason (required if rejecting)..."
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        style={{ minHeight: 50, marginBottom: 12 }}
      />
      <div className="row">
        <button className="btn btn-danger" disabled={busy || !reason.trim()} onClick={handleReject}>
          Reject
        </button>
        <span className="spacer" />
        <button className="btn btn-primary" disabled={busy} onClick={handleApprove}>
          Approve
        </button>
      </div>
    </div>
  );
}

export default function AdminAgentsPage() {
  const { accessToken } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAgents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<AgentListResponse>("/admin/agents/pending", { token: accessToken });
      setAgents(data.items);
    } catch {
      toast.error("Failed to load pending agents.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    // Fetch-on-mount: synchronizing local state with the server.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadAgents();
  }, [loadAgents]);

  async function handleApprove(agent: Agent) {
    try {
      await apiFetch<Agent>(`/admin/agents/${agent.id}/approve`, {
        method: "POST",
        token: accessToken,
      });
      toast.success("Agent approved.");
      loadAgents();
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to approve.");
    }
  }

  async function handleReject(agent: Agent, reason: string) {
    try {
      await apiFetch<Agent>(`/admin/agents/${agent.id}/reject`, {
        method: "POST",
        token: accessToken,
        body: { reject_reason: reason },
      });
      toast.success("Agent rejected.");
      loadAgents();
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to reject.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://admin/approve
          </div>
          <h1 className="page-title">Pending agents</h1>
          <p className="page-subtitle">{agents.length} agents awaiting review.</p>
        </div>
      </div>

      {loading ? (
        <p className="faint">Loading...</p>
      ) : agents.length === 0 ? (
        <p className="faint">No agents pending — queue is clear.</p>
      ) : (
        <div className="stack-md">
          {agents.map((agent) => (
            <PendingAgentCard
              key={agent.id}
              agent={agent}
              onApprove={() => handleApprove(agent)}
              onReject={(reason) => handleReject(agent, reason)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
