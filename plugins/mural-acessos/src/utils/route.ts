const APP_BASE = "/apps/mural-acessos";
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export type MuralRoute = { kind: "list" } | { kind: "detail"; hubId: string };

function currentPathname(pathname?: string): string {
  if (pathname && pathname.trim()) {
    return pathname.replace(/\/+$/, "") || "/";
  }
  if (typeof window !== "undefined" && window.location.pathname) {
    return window.location.pathname.replace(/\/+$/, "") || "/";
  }
  return APP_BASE;
}

export function muralListPath(): string {
  return APP_BASE;
}

export function muralDetailPath(hubId: string): string {
  return `${APP_BASE}/${hubId}`;
}

export function parseMuralPath(pathname?: string): MuralRoute {
  const path = currentPathname(pathname);
  if (path === APP_BASE) {
    return { kind: "list" };
  }
  if (!path.startsWith(`${APP_BASE}/`)) {
    return { kind: "list" };
  }
  const hubId = path.slice(APP_BASE.length + 1).split("/")[0] ?? "";
  if (UUID_PATTERN.test(hubId)) {
    return { kind: "detail", hubId };
  }
  return { kind: "list" };
}

export function navigateMural(path: string): void {
  if (typeof window === "undefined") return;
  if (window.location.pathname === path) return;
  window.history.pushState(null, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
