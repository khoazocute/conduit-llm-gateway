import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "16px 24px",
        }}
      >
        <Link href="/" className="topbar-logo-text" style={{ color: "var(--text)" }}>
          CONDUIT<span className="dim"> · gateway</span>
        </Link>
      </header>
      {children}
    </div>
  );
}
