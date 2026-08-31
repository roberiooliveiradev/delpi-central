/** Resolve URL to open when a manifesto route has openInNewTab. */

export function isHttpUrl(value: string | null | undefined): boolean {
  if (!value) return false;
  return /^https?:\/\//i.test(value.trim());
}

export type RouteOpenTarget = {
  path: string;
  entry?: string | null;
};

/**
 * Prefer Entry when it is an absolute http(s) URL; otherwise the portal path
 * as an absolute URL (origin + path).
 */
export function resolveRouteOpenUrl(
  route: RouteOpenTarget,
  origin: string = typeof window !== "undefined" ? window.location.origin : "",
): string {
  const entry = String(route.entry ?? "").trim();
  if (isHttpUrl(entry)) {
    return entry;
  }

  const path = route.path.startsWith("/") ? route.path : `/${route.path}`;
  const base = String(origin || "").replace(/\/$/, "");
  if (!base) {
    return path;
  }
  return `${base}${path}`;
}

export function openRouteInNewTab(
  route: RouteOpenTarget,
  origin?: string,
): Window | null {
  const url = resolveRouteOpenUrl(route, origin);
  return window.open(url, "_blank", "noopener,noreferrer");
}
