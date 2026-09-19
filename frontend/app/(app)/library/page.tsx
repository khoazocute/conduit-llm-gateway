"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { AgentAvatar } from "@/components/agent-avatar";
import { Pager } from "@/components/pager";
import { useAuth } from "@/context/auth-context";
import { apiFetch } from "@/lib/api/client";
import type { PurchasedAgentListResponse } from "@/lib/api/types";

const PAGE_SIZE = 12;

// The buyer's view: only agents they have actually paid for (drafts/pending belong to the creator dashboard).
export default function LibraryPage() {
  const { status, accessToken } = useAuth();
  const router = useRouter();
  const [page, setPage] = useState(0);
  const [data, setData] = useState<PurchasedAgentListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/login");
  }, [status, router]);

  useEffect(() => {
    if (status !== "authenticated" || !accessToken) return;
    let cancelled = false;
    // Fetch-on-page-change: synchronizing local state with the server.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    apiFetch<PurchasedAgentListResponse>("/purchases", {
      token: accessToken,
      searchParams: { page, size: PAGE_SIZE },
    })
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch(() => toast.error("Failed to load your library."))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [status, accessToken, page]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://library
          </div>
          <h1 className="page-title">My library</h1>
          <p className="page-subtitle">Agents you have purchased. Open one to keep chatting.</p>
        </div>
      </div>

      {loading || !data ? (
        <p className="faint">Loading...</p>
      ) : data.items.length === 0 ? (
        <div className="card stack-sm" style={{ maxWidth: 420 }}>
          <p>You haven&apos;t purchased any agent yet.</p>
          <Link href="/" className="btn btn-primary" style={{ alignSelf: "flex-start" }}>
            Browse the marketplace
          </Link>
        </div>
      ) : (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: 14,
            }}
          >
            {data.items.map(({ agent, purchase }) => (
              <div key={purchase.id} className="card" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                <div className="row" style={{ alignItems: "flex-start" }}>
                  <AgentAvatar id={agent.id} title={agent.title} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: "var(--t-4)", fontWeight: 500 }}>{agent.title}</div>
                    <div className="faint mono" style={{ fontSize: "var(--t-1)" }}>
                      bought {new Date(purchase.paid_at ?? purchase.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <p className="dim" style={{ fontSize: "var(--t-3)", minHeight: 36 }}>
                  {agent.introduction ?? "No description provided."}
                </p>
                <div className="row" style={{ borderTop: "1px solid var(--border-soft)", paddingTop: 12 }}>
                  <Link href={`/agents/${agent.id}/chat`} className="btn btn-primary btn-sm">
                    Chat
                  </Link>
                  <Link href={`/agents/${agent.id}`} className="btn btn-ghost btn-sm">
                    Details
                  </Link>
                </div>
              </div>
            ))}
          </div>
          <Pager
            page={data.page.page}
            totalPages={data.page.total_pages}
            totalElements={data.page.total_elements}
            noun="agents"
            onChange={setPage}
          />
        </>
      )}
    </div>
  );
}
