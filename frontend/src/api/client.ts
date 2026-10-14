const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function getTokens() {
  return {
    access: localStorage.getItem("smartchef_access") ?? "",
    refresh: localStorage.getItem("smartchef_refresh") ?? "",
  };
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("smartchef_access", access);
  localStorage.setItem("smartchef_refresh", refresh);
}

export function clearTokens() {
  localStorage.removeItem("smartchef_access");
  localStorage.removeItem("smartchef_refresh");
}

export async function refreshAccessToken(): Promise<string | null> {
  const { refresh } = getTokens();
  if (!refresh) return null;

  const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) {
    clearTokens();
    return null;
  }

  const data = await response.json();
  if (data.access && data.refresh) {
    setTokens(data.access, data.refresh);
    return data.access;
  }
  return null;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const { access } = getTokens();
  const headers = new Headers(options.headers ?? {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (access) {
    headers.set("Authorization", `Bearer ${access}`);
  }

  const request = async (tokenHeaders: Headers) =>
    fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: tokenHeaders,
    });

  let response = await request(headers);
  if (response.status === 401 && access) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${refreshed}`);
      response = await request(headers);
    }
  }

  if (!response.ok) {
    const responseText = await response.text();
    let payload: unknown = responseText;
    try { payload = responseText ? JSON.parse(responseText) : null; } catch { /* keep text payload */ }
    const message = getApiErrorMessage(payload) || response.statusText || "Request failed";
    throw new ApiError(message, response.status, payload);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const apiBaseUrl = API_BASE_URL;

function getApiErrorMessage(payload: unknown): string {
  if (typeof payload === "string" && payload.trim()) return payload;
  if (!payload || typeof payload !== "object") return "";
  const record = payload as Record<string, unknown>;
  if (typeof record.detail === "string") return record.detail;
  return Object.entries(record)
    .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(" ") : String(value)}`)
    .join(" ");
}
