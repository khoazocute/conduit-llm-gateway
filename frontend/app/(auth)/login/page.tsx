"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/context/auth-context";
import { ApiClientError } from "@/lib/api/client";
import { homePathForRole } from "@/lib/roles";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await login(email, password);
      router.push(homePathForRole(user.role));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.apiError.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "48px 24px" }}>
      <div className="card" style={{ width: 360 }}>
        <div className="page-eyebrow">
          <span className="accent">●</span> conduit://login
        </div>
        <h1 style={{ fontSize: "var(--t-7)", fontWeight: 500, marginBottom: 18 }}>Log in</h1>
        <form onSubmit={handleSubmit} className="stack-sm">
          {error && <p style={{ color: "var(--danger)", fontSize: "var(--t-3)" }}>{error}</p>}
          <div>
            <div className="label">Email</div>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <div className="label">Password</div>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={submitting} style={{ marginTop: 6, justifyContent: "center" }}>
            {submitting ? "Logging in..." : "Log in"}
          </button>
        </form>
        <p className="faint" style={{ fontSize: "var(--t-3)", marginTop: 16 }}>
          No account? <Link href="/register" className="link">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
