import type { ApiResponse } from "@/types";
const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response = await fetch(`${BASE}${path}`, { ...init, headers });
  if (
    response.status === 401 &&
    typeof window !== "undefined" &&
    localStorage.getItem("refresh_token")
  ) {
    const refreshed = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        refresh_token: localStorage.getItem("refresh_token"),
      }),
    });
    if (refreshed.ok) {
      const body = await refreshed.json();
      localStorage.setItem("access_token", body.data.access_token);
      localStorage.setItem("refresh_token", body.data.refresh_token);
      document.cookie = `access_token=${body.data.access_token}; path=/; max-age=1800; SameSite=Lax`;
      headers.set("Authorization", `Bearer ${body.data.access_token}`);
      response = await fetch(`${BASE}${path}`, { ...init, headers });
    }
  }
  const body: ApiResponse<T> = await response.json();
  if (!response.ok || body.code !== 0)
    throw new Error(body.message || "请求失败");
  return body.data;
}
export const api = {
  get: <T>(p: string) => request<T>(p),
  post: <T>(p: string, b?: unknown) =>
    request<T>(p, {
      method: "POST",
      body: b instanceof FormData ? b : JSON.stringify(b ?? {}),
    }),
  put: <T>(p: string, b: unknown) =>
    request<T>(p, { method: "PUT", body: JSON.stringify(b) }),
  patch: <T>(p: string, b: unknown) =>
    request<T>(p, { method: "PATCH", body: JSON.stringify(b) }),
  delete: <T>(p: string) => request<T>(p, { method: "DELETE" }),
};
export async function sse(
  path: string,
  body: unknown,
  onEvent: (e: any) => void,
) {
  const token = localStorage.getItem("access_token");
  const response = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error((await response.json()).message);
  const reader = response.body!.getReader(),
    decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      const line = part.split("\n").find((x) => x.startsWith("data: "));
      if (line) onEvent(JSON.parse(line.slice(6)));
    }
  }
}
