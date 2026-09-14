"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { AgentAvatar } from "@/components/agent-avatar";
import { AgentStatusBadge } from "@/components/agent-status-badge";
import { useAuth } from "@/context/auth-context";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import type { Agent, AgentListResponse, AgentStatus } from "@/lib/api/types";

const TABS: Array<{ value: string; label: string; status?: AgentStatus }> = [
  { value: "all", label: "All" },
  { value: "draft", label: "Draft", status: "draft" },
  { value: "pending", label: "Pending", status: "pending" },
  { value: "published", label: "Published", status: "published" },
  { value: "rejected", label: "Rejected", status: "rejected" },
  { value: "unpublished", label: "Unpublished", status: "unpublished" },
];

export default function DashboardPage() {
  const { accessToken, user } = useAuth();
  const [tab, setTab] = useState("all");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAgents = useCallback(
    async (status?: AgentStatus) => {
      setLoading(true);
      try {
        const data = await apiFetch<AgentListResponse>("/agents/mine", {
          token: accessToken,
          searchParams: { status },
        });
        setAgents(data.items);
      } catch {
        toast.error("Failed to load your agents.");
      } finally {
        setLoading(false);
      }
    },
    [accessToken],
  );

  useEffect(() => {
    const activeTab = TABS.find((t) => t.value === tab);
    // Fetch-on-tab-change: synchronizing local state with the server, the
    // sanctioned use of an effect (not a derived-state anti-pattern).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadAgents(activeTab?.status);
  }, [tab, loadAgents]);

  async function handleSubmit(agent: Agent) {
    try {
      await apiFetch<Agent>(`/agents/${agent.id}/submit`, { method: "POST", token: accessToken });
      toast.success("Agent submitted for review.");
      loadAgents(TABS.find((t) => t.value === tab)?.status);
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to submit agent.");
    }
  }

  async function handleUnpublish(agent: Agent) {
    try {
      await apiFetch<Agent>(`/agents/${agent.id}/unpublish`, { method: "POST", token: accessToken });
      toast.success("Agent unpublished.");
      loadAgents(TABS.find((t) => t.value === tab)?.status);
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to unpublish agent.");
    }
  }

  function handleNewAgentClick(e: React.MouseEvent) {
    if (user?.role !== "creator" && user?.role !== "admin") {
      e.preventDefault();
      toast.error("Your account needs the creator role to publish agents. Ask an admin to upgrade it.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://creator/agents
          </div>
          <h1 className="page-title">My agents</h1>
        </div>
        <Link href="/dashboard/agents/new" className="btn btn-primary" onClick={handleNewAgentClick}>
          + New agent
        </Link>
      </div>

      <div className="seg" style={{ marginBottom: 20 }}>
        {TABS.map((t) => (
          <button
            key={t.value}
            className={tab === t.value ? "is-active" : ""}
            onClick={() => setTab(t.value)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="faint">Loading...</p>
      ) : agents.length === 0 ? (
        <p className="faint">No agents in this category yet.</p>
      ) : (
        <div className="card card-flush">
          <table className="table">
            <thead>
              <tr>
                <th>Agent</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Price</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.id}>
                  <td>
                    <div className="row">
                      <AgentAvatar id={agent.id} title={agent.title} size={32} />
                      <span>{agent.title}</span>
                    </div>
                  </td>
                  <td>
                    <AgentStatusBadge status={agent.status} />
                  </td>
                  <td className="num" style={{ textAlign: "right" }}>
                    {agent.price_vnd.toLocaleString("vi-VN")} VND
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div className="row" style={{ justifyContent: "flex-end" }}>
                      {(agent.status === "draft" || agent.status === "rejected") && (
                        <Link href={`/dashboard/agents/${agent.id}/edit`} className="btn btn-ghost btn-sm">
                          Edit
                        </Link>
                      )}
                      {(agent.status === "draft" ||
                        agent.status === "rejected" ||
                        agent.status === "unpublished") && (
                        <button className="btn btn-sm" onClick={() => handleSubmit(agent)}>
                          {agent.status === "unpublished" ? "Resubmit" : "Submit"}
                        </button>
                      )}
                      {agent.status === "published" && (
                        <button className="btn btn-ghost btn-sm" onClick={() => handleUnpublish(agent)}>
                          Unpublish
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
