"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/context/auth-context";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import type { User, UserListResponse, UserStatus } from "@/lib/api/types";

const FILTERS: Array<{ value: string; label: string; status?: UserStatus }> = [
  { value: "all", label: "All" },
  { value: "active", label: "Active", status: "active" },
  { value: "banned", label: "Banned", status: "banned" },
];

export default function AdminUsersPage() {
  const { accessToken } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  const loadUsers = useCallback(
    async (status?: UserStatus) => {
      setLoading(true);
      try {
        const data = await apiFetch<UserListResponse>("/admin/users", {
          token: accessToken,
          searchParams: { status },
        });
        setUsers(data.items);
      } catch {
        toast.error("Failed to load users.");
      } finally {
        setLoading(false);
      }
    },
    [accessToken],
  );

  useEffect(() => {
    // Fetch-on-filter-change: synchronizing local state with the server.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadUsers(FILTERS.find((f) => f.value === filter)?.status);
  }, [filter, loadUsers]);

  async function toggleStatus(user: User) {
    const nextStatus: UserStatus = user.status === "active" ? "banned" : "active";
    try {
      await apiFetch<User>(`/admin/users/${user.id}/status`, {
        method: "PATCH",
        token: accessToken,
        body: { status: nextStatus },
      });
      toast.success(`User ${nextStatus === "banned" ? "banned" : "unbanned"}.`);
      loadUsers(FILTERS.find((f) => f.value === filter)?.status);
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to update user.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://admin/users
          </div>
          <h1 className="page-title">Users</h1>
        </div>
        <div className="seg">
          {FILTERS.map((f) => (
            <button key={f.value} className={filter === f.value ? "is-active" : ""} onClick={() => setFilter(f.value)}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="faint">Loading...</p>
      ) : (
        <div className="card card-flush">
          <table className="table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Full name</th>
                <th>Role</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.email}</td>
                  <td>{user.full_name ?? "-"}</td>
                  <td>
                    <span className="badge">{user.role}</span>
                  </td>
                  <td>
                    <span className={user.status === "banned" ? "badge badge-danger" : "badge badge-accent"}>
                      {user.status}
                    </span>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-sm" onClick={() => toggleStatus(user)}>
                      {user.status === "active" ? "Ban" : "Unban"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
