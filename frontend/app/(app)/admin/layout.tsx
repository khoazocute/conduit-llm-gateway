"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/context/auth-context";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { status, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    } else if (status === "authenticated" && user?.role !== "admin") {
      router.replace("/");
    }
  }, [status, user, router]);

  if (status !== "authenticated" || user?.role !== "admin") {
    return (
      <div className="page">
        <p className="faint">Loading...</p>
      </div>
    );
  }

  return <>{children}</>;
}
