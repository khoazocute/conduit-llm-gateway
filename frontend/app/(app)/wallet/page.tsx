"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/context/auth-context";
import { apiFetch } from "@/lib/api/client";
import type { CreditTransactionListResponse, CreditWallet } from "@/lib/api/types";

const TX_TYPE_LABEL: Record<string, string> = {
  purchase_grant: "Purchase grant",
  usage_deduct: "Usage",
  topup: "Top up",
  refund_deduct: "Refund",
};

export default function WalletPage() {
  const { accessToken } = useAuth();
  const [wallet, setWallet] = useState<CreditWallet | null>(null);
  const [txs, setTxs] = useState<CreditTransactionListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    Promise.all([
      apiFetch<CreditWallet>("/wallet", { token: accessToken }),
      apiFetch<CreditTransactionListResponse>("/wallet/transactions", { token: accessToken }),
    ])
      .then(([w, t]) => {
        setWallet(w);
        setTxs(t);
      })
      .catch(() => toast.error("Failed to load wallet."))
      .finally(() => setLoading(false));
  }, [accessToken]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://wallet
          </div>
          <h1 className="page-title">My wallet</h1>
        </div>
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 24, maxWidth: 320 }}>
        <div className="faint">Balance</div>
        <div className="num" style={{ fontSize: 32, fontWeight: 600 }}>
          {loading ? "..." : (wallet?.balance ?? 0).toLocaleString("vi-VN")} credit
        </div>
      </div>

      <h2 style={{ fontSize: 16, marginBottom: 12 }}>Transactions</h2>

      {loading ? (
        <p className="faint">Loading...</p>
      ) : !txs || txs.items.length === 0 ? (
        <p className="faint">No transactions yet.</p>
      ) : (
        <div className="card card-flush">
          <table className="table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Description</th>
                <th style={{ textAlign: "right" }}>Amount</th>
                <th style={{ textAlign: "right" }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {txs.items.map((tx) => (
                <tr key={tx.id}>
                  <td>{TX_TYPE_LABEL[tx.type] ?? tx.type}</td>
                  <td className="faint">{tx.description ?? "—"}</td>
                  <td className="num" style={{ textAlign: "right" }}>
                    {tx.amount > 0 ? "+" : ""}
                    {tx.amount.toLocaleString("vi-VN")}
                  </td>
                  <td className="faint" style={{ textAlign: "right" }}>
                    {new Date(tx.created_at).toLocaleString("vi-VN")}
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
