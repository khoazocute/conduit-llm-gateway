"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

export function AgentSearchBox() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [q, setQ] = useState(searchParams.get("q") ?? "");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    router.push(`/?${params.toString()}`);
  }

  return (
    <form onSubmit={handleSubmit} className="row" style={{ maxWidth: 360 }}>
      <input
        className="input"
        placeholder="Search agents..."
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <button type="submit" className="btn">
        Search
      </button>
    </form>
  );
}
