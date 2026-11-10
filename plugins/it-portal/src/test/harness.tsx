import { render } from "@testing-library/react";
import { vi } from "vitest";

import App from "../App";

/** Rotas simuladas da BFF: `"/path"` para GET, `"METHOD /path"` para escrita. */
export type Routes = Record<string, { status?: number; data?: unknown; body?: unknown }>;

export function ok(data: unknown) {
  return { success: true, message: "ok", data };
}

export function mockApi(routes: Routes) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://localhost");
    const key = url.pathname.replace("/apps/it-portal-api", "");
    const method = init?.method ?? "GET";
    const route = method === "GET" ? routes[key] : routes[`${method} ${key}`];
    if (!route) return new Response(JSON.stringify({ detail: "Not Found" }), { status: 404 });
    const status = route.status ?? 200;
    const body = route.body ?? (status < 400 ? ok(route.data) : { success: false, message: "Erro", data: null });
    return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export function renderAt(path: string) {
  window.history.pushState(null, "", path);
  return render(<App getAccessToken={() => "token"} pathname={path} basePath="/apps/it-portal" />);
}

export function requestedPaths(fetchMock: ReturnType<typeof mockApi>, method = "GET"): string[] {
  return fetchMock.mock.calls
    .filter(([, init]) => (init?.method ?? "GET") === method)
    .map(([input]) => new URL(String(input), "http://localhost").pathname.replace("/apps/it-portal-api", ""));
}

export function requestBodies(fetchMock: ReturnType<typeof mockApi>, method: string): unknown[] {
  return fetchMock.mock.calls
    .filter(([, init]) => init?.method === method)
    .map(([, init]) => JSON.parse(String(init?.body ?? "null")));
}
