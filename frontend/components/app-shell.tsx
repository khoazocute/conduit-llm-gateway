"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

function LogoMark() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="1" y="1" width="18" height="18" rx="5" stroke="currentColor" strokeWidth="1.4" />
      <path
        d="M6 10h2l1.4-4 2.2 8 1.4-4h2"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function NavItem({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const isActive = pathname === href || (href !== "/" && pathname.startsWith(href));
  return (
    <Link href={href} className={"nav-item" + (isActive ? " is-active" : "")}>
      {label}
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { status, user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/");
  }

  const canManageAgents = user?.role === "creator" || user?.role === "admin";
  const isAdmin = user?.role === "admin";

  return (
    <div className="app">
      <header className="topbar">
        <Link href="/" className="topbar-logo">
          <span className="topbar-logo-mark">
            <LogoMark />
          </span>
          <span className="topbar-logo-text">
            CONDUIT<span className="dim"> · gateway</span>
          </span>
        </Link>
        <div className="topbar-spacer" />
        {status === "authenticated" && user ? (
          <div className="topbar-meta">
            <span>{user.email}</span>
            <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
              Log out
            </button>
          </div>
        ) : status === "unauthenticated" ? (
          <div className="topbar-meta">
            <Link href="/login" className="link">
              Log in
            </Link>
            <Link href="/register" className="btn btn-primary btn-sm">
              Sign up
            </Link>
          </div>
        ) : null}
      </header>

      <nav className="sidebar">
        <div className="sidebar-section">Browse</div>
        <NavItem href="/" label="Marketplace" />

        {status === "authenticated" && (
          <>
            <div className="sidebar-section">Account</div>
            <NavItem href="/wallet" label="Wallet" />
          </>
        )}

        {canManageAgents && (
          <>
            <div className="sidebar-section">Creator</div>
            <NavItem href="/dashboard" label="My agents" />
          </>
        )}

        {isAdmin && (
          <>
            <div className="sidebar-section">Admin</div>
            <NavItem href="/admin/agents" label="Approve agents" />
            <NavItem href="/admin/users" label="Users" />
            <NavItem href="/admin/api-keys" label="API keys" />
            <NavItem href="/admin/model-pricing" label="Model pricing" />
          </>
        )}

        {status === "authenticated" && user && (
          <div className="sidebar-footer">
            <div className="sidebar-user">
              <div className="sidebar-user-avatar">{user.email.charAt(0).toUpperCase()}</div>
              <div className="sidebar-user-text">
                <div className="sidebar-user-name">{user.full_name ?? user.email}</div>
                <div className="sidebar-user-email">{user.role}</div>
              </div>
            </div>
          </div>
        )}
      </nav>

      <main className="main">{children}</main>
    </div>
  );
}
