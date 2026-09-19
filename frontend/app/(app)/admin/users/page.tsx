"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Pager } from "@/components/pager";
import { useAuth } from "@/context/auth-context";
import { ApiClientError, apiFetch } from "@/lib/api/client";
import type { User, UserListResponse, UserStatus } from "@/lib/api/types";

const PAGE_SIZE = 10;

const FILTERS: Array<{ value: string; label: string; status?: UserStatus }> = [
  { value: "all", label: "All" },
  { value: "active", label: "Active", status: "active" },
  { value: "banned", label: "Banned", status: "banned" },
];

export default function AdminUsersPage() {
  const { accessToken, user: me } = useAuth();
  const [data, setData] = useState<UserListResponse | null>(null);
  const [filter, setFilter] = useState("all");
  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);

  const status = FILTERS.find((f) => f.value === filter)?.status;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch<UserListResponse>("/admin/users", {
        token: accessToken,
        searchParams: { status, q: query, page, size: PAGE_SIZE },
      });
      setData(res);
    } catch {
      toast.error("Failed to load users.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, status, query, page]);

  useEffect(() => {
    // Fetch-on-filter/search/page change: synchronizing local state with the server.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load, reloadKey]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(0);
    setQuery(searchInput.trim());
  }

  function clearSearch() {
    setSearchInput("");
    setQuery("");
    setPage(0);
  }

  function changeFilter(value: string) {
    setFilter(value);
    setPage(0);
  }

  async function toggleStatus(user: User) {
    const nextStatus: UserStatus = user.status === "active" ? "banned" : "active";
    try {
      await apiFetch<User>(`/admin/users/${user.id}/status`, {
        method: "PATCH",
        token: accessToken,
        body: { status: nextStatus },
      });
      toast.success(`User ${nextStatus === "banned" ? "banned" : "unbanned"}.`);
      setReloadKey((k) => k + 1);
    } catch (err) {
      toast.error(err instanceof ApiClientError ? err.apiError.message : "Failed to update user.");
    }
  }

  const users = data?.items ?? [];

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
            <button key={f.value} className={filter === f.value ? "is-active" : ""} onClick={() => changeFilter(f.value)}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSearch} className="row" style={{ maxWidth: 460, marginBottom: 16 }}>
        <input
          className="input"
          placeholder="Search by email or name..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <button type="submit" className="btn">
          Search
        </button>
        {query && (
          <button type="button" className="btn btn-ghost" onClick={clearSearch}>
            Clear
          </button>
        )}
      </form>

      {loading && !data ? (
        <p className="faint">Loading...</p>
      ) : users.length === 0 ? (
        <p className="faint">{query ? `No users match "${query}".` : "No users found."}</p>
      ) : (
        <div className="card card-flush" style={{ opacity: loading ? 0.6 : 1 }}>
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
              {users.map((user) => {
                const isMe = user.id === me?.id;
                return (
                  <tr key={user.id}>
                    <td>
                      {user.email}
                      {isMe && (
                        <span className="badge badge-info" style={{ marginLeft: 8 }}>
                          you
                        </span>
                      )}
                    </td>
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
                      <button
                        className="btn btn-sm"
                        disabled={isMe}
                        title={isMe ? "You cannot ban your own account" : undefined}
                        onClick={() => toggleStatus(user)}
                      >
                        {user.status === "active" ? "Ban" : "Unban"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {data && (
        <Pager
          page={data.page.page}
          totalPages={data.page.total_pages}
          totalElements={data.page.total_elements}
          noun="users"
          onChange={setPage}
        />
      )}
    </div>
  );
}
