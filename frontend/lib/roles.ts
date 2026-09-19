import type { UserRole } from "@/lib/api/types";

/** Where a user lands after logging in / signing up: creators and admins manage agents, buyers use their library. */
export function homePathForRole(role: UserRole): string {
  return role === "creator" || role === "admin" ? "/dashboard" : "/library";
}

export function canManageAgents(role: UserRole | undefined): boolean {
  return role === "creator" || role === "admin";
}
