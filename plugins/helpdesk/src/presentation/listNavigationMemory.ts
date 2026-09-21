/** Remembers the solicitante list URL (path + search) so Voltar restores the same recorte. */

const LAST_LIST_KEY = "helpdesk:last-list-path:v1";

function normalizeListPath(pathWithSearch: string): string | null {
  const qIndex = pathWithSearch.indexOf("?");
  const pathname = qIndex >= 0 ? pathWithSearch.slice(0, qIndex) : pathWithSearch;
  const search = qIndex >= 0 ? pathWithSearch.slice(qIndex) : "";
  if (pathname !== "/apps/helpdesk" && pathname !== "/apps/helpdesk/") return null;
  return `/apps/helpdesk${search}`;
}

/** Persists the current or given list URL (with query) for later Voltar. */
export function rememberHelpdeskListPath(pathWithSearch?: string): void {
  const path =
    pathWithSearch ??
    (typeof window !== "undefined" ? `${window.location.pathname}${window.location.search}` : "");
  const normalized = path ? normalizeListPath(path) : null;
  if (!normalized) return;
  try {
    sessionStorage.setItem(LAST_LIST_KEY, normalized);
  } catch {
    /* quota / private mode — ignore */
  }
}

/** Last remembered list URL, or the bare list root. */
export function lastHelpdeskListPath(): string {
  try {
    const raw = sessionStorage.getItem(LAST_LIST_KEY);
    if (raw) {
      const normalized = normalizeListPath(raw);
      if (normalized) return normalized;
    }
  } catch {
    /* ignore */
  }
  return "/apps/helpdesk";
}
