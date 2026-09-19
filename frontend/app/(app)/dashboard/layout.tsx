"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/context/auth-context";
import { canManageAgents } from "@/lib/roles";

// Creator area: buyers have no draft/pending agents to manage, they use /library instead.
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { status, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    } else if (status === "authenticated" && !canManageAgents(user?.role)) {
      router.replace("/library");
    }
  }, [status, user, router]);

  if (status !== "authenticated" || !canManageAgents(user?.role)) {
    return (
      <div className="page">
        <p className="faint">Loading...</p>
      </div>
    );
  }

  return <>{children}</>;
}
