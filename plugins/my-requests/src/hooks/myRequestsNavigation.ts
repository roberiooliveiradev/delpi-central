const BASE = "/apps/my-requests";

/** Soft navigation inside the MFE — no full document reload (commercial pattern). */
export function navigateMyRequestsPath(
  target: string,
  options?: { replace?: boolean },
): void {
  if (typeof window === "undefined") return;

  const normalizedTarget = target.startsWith("/") ? target : `${BASE}/${target}`;
  const current = `${window.location.pathname}${window.location.search || ""}`;
  if (current === normalizedTarget) return;

  if (options?.replace) {
    window.history.replaceState(null, "", normalizedTarget);
  } else {
    window.history.pushState(null, "", normalizedTarget);
  }

  const popState =
    typeof PopStateEvent === "function"
      ? new PopStateEvent("popstate")
      : new Event("popstate");
  window.dispatchEvent(popState);
}

export function myRequestsPath(
  route: "mine" | "work-queue" | "new" | "admin" | { requestId: string },
): string {
  if (typeof route === "object") {
    return `${BASE}/requests/${route.requestId}`;
  }
  if (route === "mine") return `${BASE}/mine`;
  return `${BASE}/${route}`;
}

/** `/new` or `/new?type=<code>` (canonical deep link for type forms). */
export function myRequestsNewPath(typeCode?: string): string {
  const code = String(typeCode || "").trim();
  if (!code) return myRequestsPath("new");
  const qs = new URLSearchParams({ type: code });
  return `${myRequestsPath("new")}?${qs.toString()}`;
}
