"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api/client";
import type { AuthResponse, User } from "@/lib/api/types";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  user: User | null;
  accessToken: string | null;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, password: string, fullName: string) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const applyAuthResponse = useCallback((data: AuthResponse) => {
    setUser(data.user);
    setAccessToken(data.access_token);
    setStatus("authenticated");
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiFetch<AuthResponse>("/auth/refresh", { method: "POST", withCredentials: true })
      .then((data) => {
        if (!cancelled) applyAuthResponse(data);
      })
      .catch(() => {
        if (!cancelled) setStatus("unauthenticated");
      });
    return () => {
      cancelled = true;
    };
  }, [applyAuthResponse]);

  const login = useCallback(
    async (email: string, password: string) => {
      const data = await apiFetch<AuthResponse>("/auth/login", {
        method: "POST",
        withCredentials: true,
        body: { email, password },
      });
      applyAuthResponse(data);
      return data.user;
    },
    [applyAuthResponse],
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      const data = await apiFetch<AuthResponse>("/auth/register", {
        method: "POST",
        withCredentials: true,
        body: { email, password, full_name: fullName },
      });
      applyAuthResponse(data);
      return data.user;
    },
    [applyAuthResponse],
  );

  const logout = useCallback(async () => {
    try {
      await apiFetch("/auth/logout", {
        method: "POST",
        token: accessToken,
        withCredentials: true,
      });
    } catch {
      // Never surface a logout failure: the local session must be dropped regardless (the server
      // revokes the refresh token and clears its cookie when reachable).
    } finally {
      setUser(null);
      setAccessToken(null);
      setStatus("unauthenticated");
    }
  }, [accessToken]);

  const value = useMemo(
    () => ({ status, user, accessToken, login, register, logout }),
    [status, user, accessToken, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
