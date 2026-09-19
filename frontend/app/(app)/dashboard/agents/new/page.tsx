"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { AgentForm, type AgentFormValues } from "@/components/agent-form";
import { useAuth } from "@/context/auth-context";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import type { Agent } from "@/lib/api/types";

export default function NewAgentPage() {
  const { accessToken } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(values: AgentFormValues) {
    setError(null);
    try {
      await apiFetch<Agent>("/agents", {
        method: "POST",
        token: accessToken,
        body: values,
      });
      toast.success("Agent created as a draft. Press Submit in the list to send it for review.");
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.apiError.message : "Failed to create agent.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://creator/build
          </div>
          <h1 className="page-title">New agent</h1>
        </div>
      </div>
      <AgentForm submitLabel="Create agent" onSubmit={handleSubmit} errorMessage={error} />
    </div>
  );
}
