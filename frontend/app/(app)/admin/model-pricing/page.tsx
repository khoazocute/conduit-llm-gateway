"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/context/auth-context";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import type { LlmProvider, ModelPricing, UnitType } from "@/lib/api/types";

const PROVIDERS: LlmProvider[] = ["openai", "anthropic", "google"];
const UNIT_TYPES: UnitType[] = ["token_input", "token_output", "image_generation"];

export default function AdminModelPricingPage() {
  const { accessToken } = useAuth();
  const [rows, setRows] = useState<ModelPricing[]>([]);
  const [loading, setLoading] = useState(true);
  const [provider, setProvider] = useState<LlmProvider>("openai");
  const [model, setModel] = useState("");
  const [unitType, setUnitType] = useState<UnitType>("token_input");
  const [priceUsd, setPriceUsd] = useState("0.000001");
  const [markup, setMarkup] = useState("1.5");
  const [effectiveFrom, setEffectiveFrom] = useState(() => new Date().toISOString().slice(0, 16));
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<ModelPricing[]>("/admin/model-pricing", { token: accessToken });
      setRows(data);
    } catch {
      toast.error("Failed to load model pricing.");
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
      await apiFetch<ModelPricing>("/admin/model-pricing", {
        method: "POST",
        token: accessToken,
        body: {
          provider,
          model,
          unit_type: unitType,
          price_usd_per_unit: Number(priceUsd),
          credit_markup_multiplier: Number(markup) || 1.5,
          effective_from: new Date(effectiveFrom).toISOString(),
        },
      });
      toast.success("Pricing row created.");
      setModel("");
      load();
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to create pricing.");
    } finally {
      setSubmitting(false);
    }
  }

  const isFuture = (iso: string) => new Date(iso).getTime() > Date.now();

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://admin/model-pricing
          </div>
          <h1 className="page-title">Model pricing</h1>
        </div>
      </div>

      <form onSubmit={handleCreate} className="card stack-sm" style={{ marginBottom: 24, maxWidth: 560 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div>
            <div className="label">Provider</div>
            <select className="input" value={provider} onChange={(e) => setProvider(e.target.value as LlmProvider)}>
              {PROVIDERS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="label">Model</div>
            <input className="input" value={model} onChange={(e) => setModel(e.target.value)} placeholder="gpt-4o-mini" required />
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
          <div>
            <div className="label">Unit type</div>
            <select className="input" value={unitType} onChange={(e) => setUnitType(e.target.value as UnitType)}>
              {UNIT_TYPES.map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="label">Price (USD/unit)</div>
            <input
              className="input"
              type="number"
              step="0.0000001"
              min={0}
              value={priceUsd}
              onChange={(e) => setPriceUsd(e.target.value)}
              required
            />
          </div>
          <div>
            <div className="label">Markup</div>
            <input
              className="input"
              type="number"
              step="0.01"
              min={1}
              value={markup}
              onChange={(e) => setMarkup(e.target.value)}
            />
          </div>
        </div>
        <div>
          <div className="label">Effective from</div>
          <input
            className="input"
            type="datetime-local"
            value={effectiveFrom}
            onChange={(e) => setEffectiveFrom(e.target.value)}
            required
          />
          <div className="faint mono" style={{ fontSize: "var(--t-1)", marginTop: 6 }}>
            credit = ceil(token_upstream × markup). Editing a row later only works while
            its effective_from is still in the future — otherwise a new row is created.
          </div>
        </div>
        <button type="submit" className="btn btn-primary" disabled={submitting} style={{ alignSelf: "flex-start" }}>
          {submitting ? "Saving..." : "Add pricing"}
        </button>
      </form>

      {loading ? (
        <p className="faint">Loading...</p>
      ) : rows.length === 0 ? (
        <p className="faint">No pricing configured yet.</p>
      ) : (
        <div className="card card-flush">
          <table className="table">
            <thead>
              <tr>
                <th>Provider</th>
                <th>Model</th>
                <th>Unit</th>
                <th style={{ textAlign: "right" }}>Price (USD)</th>
                <th style={{ textAlign: "right" }}>Markup</th>
                <th style={{ textAlign: "right" }}>Effective from</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{row.provider}</td>
                  <td>{row.model}</td>
                  <td className="faint">{row.unit_type}</td>
                  <td className="num" style={{ textAlign: "right" }}>
                    {row.price_usd_per_unit}
                  </td>
                  <td className="num" style={{ textAlign: "right" }}>
                    {row.credit_markup_multiplier}×
                  </td>
                  <td className="faint" style={{ textAlign: "right" }}>
                    {new Date(row.effective_from).toLocaleString("vi-VN")}
                    {isFuture(row.effective_from) && (
                      <span className="badge" style={{ marginLeft: 6 }}>
                        upcoming
                      </span>
                    )}
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
