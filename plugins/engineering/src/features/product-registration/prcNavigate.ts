/** Navegação interna da feature via pushState + popstate — mesmo
 * mecanismo governado usado por navigateEngineeringView.
 * Estado de URL: fila `?status=&type=&search=&page=` e detalhe `?tab=`. */

import { useEffect, useState } from "react";

export const PRC_BASE = "product-registration";

export const PRC_PATHS = {
  queue: PRC_BASE,
  create: `${PRC_BASE}/new`,
  detail: (requestId: string) => `${PRC_BASE}/${requestId}`,
} as const;

export function resolvePrcPath(relativePath: string): {
  page: "queue" | "detail" | "create";
  requestId?: string;
} {
  const parts = relativePath
    .replace(/^product-registration\/?/, "")
    .split("/")
    .filter(Boolean);
  if (parts[0] === "new") {
    return { page: "create" };
  }
  if (parts.length >= 1 && /^[0-9a-fA-F-]{36}$/.test(parts[0])) {
    return { page: "detail", requestId: parts[0] };
  }
  return { page: "queue" };
}

export function navigatePrc(path: string, basePath: string): void {
  if (typeof window === "undefined") return;
  window.history.pushState(
    window.history.state,
    "",
    `${basePath}/${path}`,
  );
  window.dispatchEvent(
    new PopStateEvent("popstate", { state: window.history.state }),
  );
}

export function navigatePrcHref(
  href: string,
  options?: { replace?: boolean },
): void {
  if (typeof window === "undefined") return;
  if (options?.replace) {
    window.history.replaceState(window.history.state, "", href);
  } else {
    window.history.pushState(window.history.state, "", href);
  }
  window.dispatchEvent(
    new PopStateEvent("popstate", { state: window.history.state }),
  );
}

function readLocationSearch(): string {
  if (typeof window === "undefined") return "";
  return window.location.search;
}

/** `window.location.search` reativo a popstate — mesmo padrão de
 * `useLocationSearch` da feature products. */
export function useLocationSearch(): string {
  const [search, setSearch] = useState(readLocationSearch);
  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const sync = () => setSearch(readLocationSearch());
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);
  return search;
}

// --- Fila: estado orientado por URL --------------------------------------

export type PrcQueueUrlState = {
  status: string;
  type: string;
  search: string;
  page: number;
};

export const EMPTY_PRC_QUEUE_URL: PrcQueueUrlState = {
  status: "",
  type: "",
  search: "",
  page: 1,
};

export function parsePrcQueueUrl(search: string): PrcQueueUrlState {
  const p = new URLSearchParams(search);
  const page = Math.max(1, Number.parseInt(p.get("page") ?? "1", 10) || 1);
  const type = p.get("type") ?? "";
  return {
    status: p.get("status") ?? "",
    type: type === "create" || type === "update" ? type : "",
    search: p.get("search") ?? "",
    page: Number.isFinite(page) ? page : 1,
  };
}

export function buildPrcQueueUrl(
  basePath: string,
  state: PrcQueueUrlState,
): string {
  const p = new URLSearchParams();
  if (state.status) p.set("status", state.status);
  if (state.type) p.set("type", state.type);
  if (state.search) p.set("search", state.search);
  if (state.page > 1) p.set("page", String(state.page));
  const q = p.toString();
  return `${basePath}/${PRC_PATHS.queue}${q ? `?${q}` : ""}`;
}

// --- Detalhe: abas orientadas por URL ------------------------------------

export type PrcTabKey =
  | "overview"
  | "draft"
  | "verification"
  | "history"
  | "revisions";

export const PRC_TAB_KEYS: readonly PrcTabKey[] = [
  "overview",
  "draft",
  "verification",
  "history",
  "revisions",
];

export function parsePrcTab(search: string): PrcTabKey {
  const raw = new URLSearchParams(search).get("tab");
  return (PRC_TAB_KEYS as readonly string[]).includes(raw || "")
    ? (raw as PrcTabKey)
    : "overview";
}

export function prcDetailTabHref(
  basePath: string,
  requestId: string,
  tab: PrcTabKey,
): string {
  const base = `${basePath}/${PRC_PATHS.detail(requestId)}`;
  return tab === "overview" ? base : `${base}?tab=${tab}`;
}
