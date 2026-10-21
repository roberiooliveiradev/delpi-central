export const APP_BASE = "/apps/metalography";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export type MetalographyRoute =
  | { kind: "list" }
  | { kind: "create" }
  | { kind: "editor"; reportId: string; readOnly: boolean };

function currentPathname(pathname?: string): string {
  const raw = pathname?.trim()
    ? pathname
    : typeof window !== "undefined"
      ? window.location.pathname
      : APP_BASE;
  return raw.replace(/\/+$/, "") || "/";
}

export function listPath(): string {
  return APP_BASE;
}

export function createPath(): string {
  return `${APP_BASE}/new`;
}

export function editorPath(reportId: string, readOnly = false): string {
  return readOnly ? `${APP_BASE}/${reportId}/view` : `${APP_BASE}/${reportId}`;
}

export function parseMetalographyPath(pathname?: string): MetalographyRoute {
  const path = currentPathname(pathname);
  if (path === APP_BASE || !path.startsWith(`${APP_BASE}/`)) return { kind: "list" };
  const rest = path.slice(APP_BASE.length + 1);
  if (rest === "new") return { kind: "create" };
  const [reportId, mode] = rest.split("/");
  if (!reportId || !UUID_PATTERN.test(reportId)) return { kind: "list" };
  return { kind: "editor", reportId, readOnly: mode === "view" };
}

export function navigateMetalography(path: string): void {
  if (typeof window === "undefined") return;
  if (window.location.pathname === path) return;
  window.history.pushState(null, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
