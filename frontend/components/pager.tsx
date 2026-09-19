"use client";

interface PagerProps {
  page: number;
  totalPages: number;
  totalElements: number;
  noun: string;
  onChange: (page: number) => void;
}

export function Pager({ page, totalPages, totalElements, noun, onChange }: PagerProps) {
  if (totalElements === 0) return null;
  return (
    <div className="row" style={{ marginTop: 16, justifyContent: "space-between" }}>
      <span className="faint mono" style={{ fontSize: "var(--t-2)" }}>
        {totalElements} {noun} · page {page + 1} of {Math.max(totalPages, 1)}
      </span>
      <div className="row">
        <button className="btn btn-sm" disabled={page <= 0} onClick={() => onChange(page - 1)}>
          ← Prev
        </button>
        <button className="btn btn-sm" disabled={page + 1 >= totalPages} onClick={() => onChange(page + 1)}>
          Next →
        </button>
      </div>
    </div>
  );
}
