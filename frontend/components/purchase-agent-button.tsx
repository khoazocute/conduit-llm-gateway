"use client";

import { useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/context/auth-context";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import { signMockWebhookBody } from "@/lib/mock-webhook-signature";
import type { AgentPurchase, CreatePurchaseResponse } from "@/lib/api/types";

export function PurchaseAgentButton({ agentId, priceVnd }: { agentId: string; priceVnd: number }) {
  const { status, accessToken } = useAuth();
  const [purchase, setPurchase] = useState<AgentPurchase | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleBuy() {
    setLoading(true);
    try {
      const res = await apiFetch<CreatePurchaseResponse>(`/agents/${agentId}/purchases`, {
        method: "POST",
        token: accessToken,
        body: { payment_method: "mock" },
      });
      setPurchase(res.purchase);
      if (res.purchase.payment_status === "paid") {
        toast.success("Purchased! Credit granted instantly (free agent).");
      } else {
        toast.success("Purchase created — pending payment. Click \"Simulate payment\" below.");
      }
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to create purchase.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSimulatePayment() {
    if (!purchase) return;
    setLoading(true);
    try {
      const body = { transaction_ref: purchase.transaction_ref, result: "success" };
      const rawBody = JSON.stringify(body);
      const signature = await signMockWebhookBody(rawBody);
      await apiFetch("/payments/webhook/mock", {
        method: "POST",
        body,
        extraHeaders: { "X-Webhook-Signature": signature },
      });
      // Re-fetch instead of guessing paid_at locally - the webhook call above
      // doesn't return the updated purchase, only {result: "accepted"}.
      const refreshed = await apiFetch<AgentPurchase>(`/purchases/${purchase.transaction_ref}`, {
        token: accessToken,
      });
      setPurchase(refreshed);
      toast.success("Mock payment confirmed! Credit granted — check your wallet.");
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Webhook call failed.");
    } finally {
      setLoading(false);
    }
  }

  if (status !== "authenticated") {
    return <p className="faint">Log in to purchase this agent.</p>;
  }

  if (purchase?.payment_status === "paid") {
    return <p className="faint">You own this agent (purchased {new Date(purchase.paid_at!).toLocaleString("vi-VN")}).</p>;
  }

  return (
    <div className="row" style={{ gap: 10 }}>
      {!purchase ? (
        <button className="btn btn-primary" disabled={loading} onClick={handleBuy}>
          {priceVnd === 0 ? "Get for free" : "Buy"}
        </button>
      ) : (
        <button className="btn btn-primary" disabled={loading} onClick={handleSimulatePayment}>
          Simulate payment (mock)
        </button>
      )}
    </div>
  );
}
