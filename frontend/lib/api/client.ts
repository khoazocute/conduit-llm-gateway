import type { ApiError } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8081/api";

export class ApiClientError extends Error {
  status: number;
  apiError: ApiError;

  constructor(status: number, apiError: ApiError) {
    super(apiError.message);
    this.status = status;
    this.apiError = apiError;
  }
}

interface ApiFetchOptions {
  method?: string;
  token?: string | null;
  body?: unknown;
  /** Only auth endpoints (login/register/refresh/logout) need the refresh_token cookie. */
  withCredentials?: boolean;
  searchParams?: Record<string, string | number | undefined>;
}

function buildUrl(path: string, searchParams?: ApiFetchOptions["searchParams"]) {
  const url = new URL(API_BASE_URL + path);
  if (searchParams) {
    for (const [key, value] of Object.entries(searchParams)) {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { method = "GET", token, body, withCredentials, searchParams } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(buildUrl(path, searchParams), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: withCredentials ? "include" : "same-origin",
  });

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  const data = text ? JSON.parse(text) : undefined;

  if (!res.ok) {
    throw new ApiClientError(res.status, data as ApiError);
  }

  return data as T;
}
