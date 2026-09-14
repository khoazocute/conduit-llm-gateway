"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/context/auth-context";
import { ApiClientError } from "@/lib/api/client";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    setSubmitting(true);
    try {
      await register(email, password, fullName);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.apiError.message);
        if (err.apiError.details) {
          setFieldErrors(err.apiError.details as Record<string, string>);
        }
      } else {
        setError("Something went wrong.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "48px 24px" }}>
      <div className="card" style={{ width: 360 }}>
        <div className="page-eyebrow">
          <span className="accent">●</span> conduit://register
        </div>
        <h1 style={{ fontSize: "var(--t-7)", fontWeight: 500, marginBottom: 18 }}>Create an account</h1>
        <form onSubmit={handleSubmit} className="stack-sm">
          {error && <p style={{ color: "var(--danger)", fontSize: "var(--t-3)" }}>{error}</p>}
          <div>
            <div className="label">Full name</div>
            <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            {fieldErrors.full_name && (
              <p style={{ color: "var(--danger)", fontSize: "var(--t-1)", marginTop: 4 }}>{fieldErrors.full_name}</p>
            )}
          </div>
          <div>
            <div className="label">Email</div>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            {fieldErrors.email && (
              <p style={{ color: "var(--danger)", fontSize: "var(--t-1)", marginTop: 4 }}>{fieldErrors.email}</p>
            )}
          </div>
          <div>
            <div className="label">Password</div>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
            {fieldErrors.password && (
              <p style={{ color: "var(--danger)", fontSize: "var(--t-1)", marginTop: 4 }}>{fieldErrors.password}</p>
            )}
          </div>
          <button type="submit" className="btn btn-primary" disabled={submitting} style={{ marginTop: 6, justifyContent: "center" }}>
            {submitting ? "Creating account..." : "Sign up"}
          </button>
        </form>
        <p className="faint" style={{ fontSize: "var(--t-3)", marginTop: 16 }}>
          Already have an account? <Link href="/login" className="link">Log in</Link>
        </p>
      </div>
    </div>
  );
}
