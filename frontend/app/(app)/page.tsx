import { AgentCard } from "@/components/agent-card";
import { AgentSearchBox } from "@/components/agent-search-box";
import { apiFetch } from "@/lib/api/client";
import type { AgentListResponse } from "@/lib/api/types";

interface HomePageProps {
  searchParams: Promise<{ q?: string; page?: string }>;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const { q, page } = await searchParams;
  const pageNumber = page ? Number(page) : 0;

  let data: AgentListResponse | null = null;
  let loadError = false;
  try {
    data = await apiFetch<AgentListResponse>("/agents", {
      searchParams: { q, page: pageNumber },
    });
  } catch {
    loadError = true;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://discover
          </div>
          <h1 className="page-title">Agent marketplace</h1>
          <p className="page-subtitle">Browse published agents built by the community.</p>
        </div>
        <AgentSearchBox />
      </div>

      {loadError && (
        <p style={{ color: "var(--danger)" }} className="mono">
          Could not load agents. Is the backend running?
        </p>
      )}

      {data && data.items.length === 0 && <p className="faint">No published agents yet.</p>}

      {data && data.items.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: 14,
          }}
        >
          {data.items.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}

      {data && data.page.total_pages > 1 && (
        <div className="row" style={{ marginTop: 20, fontSize: "var(--t-3)" }}>
          {Array.from({ length: data.page.total_pages }, (_, i) => (
            <a
              key={i}
              href={`/?${new URLSearchParams({ ...(q ? { q } : {}), page: String(i) })}`}
              className={i === pageNumber ? "link" : "faint"}
              style={{ textDecoration: i === pageNumber ? "underline" : "none" }}
            >
              {i + 1}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
