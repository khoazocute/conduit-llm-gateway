"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AgentForm, agentToFormValues, type AgentFormValues } from "@/components/agent-form";
import { useAuth } from "@/context/auth-context";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import type { Agent } from "@/lib/api/types";

export default function EditAgentPage() {
  const { accessToken } = useAuth();
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Agent>(`/agents/${params.id}`)
      .then(setAgent)
      .catch(() => setLoadError("Agent not found."));
  }, [params.id]);

  async function handleSubmit(values: AgentFormValues) {
    setSubmitError(null);
    try {
      const updated = await apiFetch<Agent>(`/agents/${params.id}`, {
        method: "PATCH",
        token: accessToken,
        body: values,
      });
      setAgent(updated);
      router.push("/dashboard");
    } catch (err) {
      setSubmitError(
        err instanceof ApiClientError ? err.apiError.message : "Failed to update agent.",
      );
    }
  }

  if (loadError) {
    return (
      <div className="page">
        <p style={{ color: "var(--danger)" }}>{loadError}</p>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="page">
        <p className="faint">Loading...</p>
      </div>
    );
  }

  const editable = agent.status === "draft" || agent.status === "rejected";

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://creator/build
          </div>
          <h1 className="page-title">Edit agent</h1>
        </div>
      </div>
      {!editable && (
        <p style={{ color: "var(--danger)", marginBottom: 16 }}>
          This agent is currently &quot;{agent.status}&quot; and can only be edited while draft or
          rejected.
        </p>
      )}
      <AgentForm
        agentId={agent.id}
        initialValues={agentToFormValues(agent)}
        submitLabel="Save changes"
        onSubmit={handleSubmit}
        errorMessage={submitError}
      />
    </div>
  );
}
