"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/context/auth-context";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import type { ApiKey, LlmProvider } from "@/lib/api/types";

const PROVIDERS: LlmProvider[] = ["openai", "anthropic", "google"];

export default function AdminApiKeysPage() {
  const { accessToken } = useAuth();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [provider, setProvider] = useState<LlmProvider>("openai");
  const [rawKey, setRawKey] = useState("");
  const [priority, setPriority] = useState("0");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<ApiKey[]>("/admin/api-keys", { token: accessToken });
      setKeys(data);
    } catch {
      toast.error("Failed to load API keys.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiFetch<ApiKey>("/admin/api-keys", {
        method: "POST",
        token: accessToken,
        body: { provider, raw_key: rawKey, priority: Number(priority) || 0 },
      });
      toast.success("API key added.");
      setRawKey("");
      setPriority("0");
      load();
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to add API key.");
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleStatus(key: ApiKey) {
    const nextStatus = key.status === "active" ? "disabled" : "active";
    try {
      await apiFetch<ApiKey>(`/admin/api-keys/${key.id}`, {
        method: "PATCH",
        token: accessToken,
        body: { status: nextStatus, priority: key.priority },
      });
      toast.success(`Key ${nextStatus}.`);
      load();
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to update key.");
    }
  }

  async function handleDelete(key: ApiKey) {
    try {
      await apiFetch(`/admin/api-keys/${key.id}`, { method: "DELETE", token: accessToken });
      toast.success("API key deleted.");
      load();
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to delete key.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://admin/api-keys
          </div>
          <h1 className="page-title">API keys</h1>
        </div>
      </div>

      <form onSubmit={handleCreate} className="card stack-sm" style={{ marginBottom: 24, maxWidth: 480 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div>
            <div className="label">Provider</div>
            <select
              className="input"
              value={provider}
              onChange={(e) => setProvider(e.target.value as LlmProvider)}
            >
              {PROVIDERS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="label">Priority</div>
            <input
              className="input"
              type="number"
              min={0}
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
            />
          </div>
        </div>
        <div>
          <div className="label">Raw key</div>
          <input
            className="input"
            value={rawKey}
            onChange={(e) => setRawKey(e.target.value)}
            placeholder="sk-..."
            required
          />
          <div className="faint mono" style={{ fontSize: "var(--t-1)", marginTop: 6 }}>
            Encrypted (AES-GCM) before being stored — never shown again after this.
          </div>
        </div>
        <button type="submit" className="btn btn-primary" disabled={submitting} style={{ alignSelf: "flex-start" }}>
          {submitting ? "Adding..." : "Add key"}
        </button>
      </form>

      {loading ? (
        <p className="faint">Loading...</p>
      ) : keys.length === 0 ? (
        <p className="faint">No API keys yet.</p>
      ) : (
        <div className="card card-flush">
          <table className="table">
            <thead>
              <tr>
                <th>Provider</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Last used</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((key) => (
                <tr key={key.id}>
                  <td>{key.provider}</td>
                  <td>
                    <span className={key.status === "active" ? "badge badge-accent" : "badge badge-danger"}>
                      {key.status}
                    </span>
                  </td>
                  <td className="num">{key.priority}</td>
                  <td className="faint">
                    {key.last_used_at ? new Date(key.last_used_at).toLocaleString("vi-VN") : "Never"}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div className="row" style={{ justifyContent: "flex-end" }}>
                      <button className="btn btn-ghost btn-sm" onClick={() => toggleStatus(key)}>
                        {key.status === "active" ? "Disable" : "Enable"}
                      </button>
                      <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(key)}>
                        Delete
                      </button>
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
