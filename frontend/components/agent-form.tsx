"use client";

import { useState } from "react";
import { AgentAvatar } from "@/components/agent-avatar";
import type { Agent } from "@/lib/api/types";

export interface AgentFormValues {
  title: string;
  introduction: string;
  price_vnd: number;
  default_credit_granted: number;
}

interface AgentFormProps {
  agentId?: string;
  initialValues?: Partial<AgentFormValues>;
  submitLabel: string;
  onSubmit: (values: AgentFormValues) => Promise<void>;
  errorMessage?: string | null;
}

function formatVnd(amount: number) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount);
}

export function AgentForm({ agentId, initialValues, submitLabel, onSubmit, errorMessage }: AgentFormProps) {
  const [title, setTitle] = useState(initialValues?.title ?? "");
  const [introduction, setIntroduction] = useState(initialValues?.introduction ?? "");
  const [priceVnd, setPriceVnd] = useState(String(initialValues?.price_vnd ?? 0));
  const [defaultCredit, setDefaultCredit] = useState(String(initialValues?.default_credit_granted ?? 0));
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({
        title,
        introduction,
        price_vnd: Number(priceVnd),
        default_credit_granted: Number(defaultCredit),
      });
    } finally {
      setSubmitting(false);
    }
  }

  const previewId = agentId ?? "preview";
  const priceNumber = Number(priceVnd) || 0;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 24, alignItems: "flex-start" }}>
      <form onSubmit={handleSubmit} className="stack-lg">
        {errorMessage && <p style={{ color: "var(--danger)" }}>{errorMessage}</p>}

        <section className="card">
          <div className="row" style={{ marginBottom: 14 }}>
            <span className="mono faint">01</span>
            <span style={{ fontWeight: 500 }}>Identity</span>
          </div>
          <div className="stack-sm">
            <div>
              <div className="label">Title</div>
              <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
            </div>
            <div>
              <div className="label">Introduction</div>
              <textarea
                className="textarea"
                value={introduction}
                onChange={(e) => setIntroduction(e.target.value)}
                rows={5}
                placeholder="Describe what this agent does..."
              />
            </div>
          </div>
        </section>

        <section className="card">
          <div className="row" style={{ marginBottom: 14 }}>
            <span className="mono faint">02</span>
            <span style={{ fontWeight: 500 }}>Price &amp; credit</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <div>
              <div className="label">Price (VND)</div>
              <input
                className="input"
                type="number"
                min={0}
                value={priceVnd}
                onChange={(e) => setPriceVnd(e.target.value)}
                required
              />
            </div>
            <div>
              <div className="label">Default credit granted</div>
              <input
                className="input"
                type="number"
                min={0}
                value={defaultCredit}
                onChange={(e) => setDefaultCredit(e.target.value)}
                required
              />
              <div className="faint mono" style={{ fontSize: "var(--t-1)", marginTop: 6 }}>
                Credit the buyer receives when purchasing this agent.
              </div>
            </div>
          </div>
        </section>

        <button type="submit" className="btn btn-primary" disabled={submitting} style={{ alignSelf: "flex-start" }}>
          {submitting ? "Saving..." : submitLabel}
        </button>
      </form>

      <div style={{ position: "sticky", top: 20 }}>
        <div className="label" style={{ marginBottom: 10 }}>
          Preview
        </div>
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="row" style={{ alignItems: "flex-start" }}>
            <AgentAvatar id={previewId} title={title || "?"} />
            <div style={{ fontSize: "var(--t-4)", fontWeight: 500 }}>{title || "Untitled agent"}</div>
          </div>
          <p className="dim" style={{ fontSize: "var(--t-3)", minHeight: 36 }}>
            {introduction || "No description provided."}
          </p>
          <div className="row" style={{ borderTop: "1px solid var(--border-soft)", paddingTop: 12 }}>
            <span className="mono" style={{ color: priceNumber === 0 ? "var(--accent)" : "var(--text)" }}>
              {priceNumber === 0 ? "Free" : formatVnd(priceNumber)}
            </span>
            <span className="spacer" />
            <span className="faint mono" style={{ fontSize: "var(--t-1)" }}>
              +{Number(defaultCredit) || 0} credit
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function agentToFormValues(agent: Agent): AgentFormValues {
  return {
    title: agent.title,
    introduction: agent.introduction ?? "",
    price_vnd: agent.price_vnd,
    default_credit_granted: agent.default_credit_granted,
  };
}
