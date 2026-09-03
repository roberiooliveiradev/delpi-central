import { useMemo } from "react";

const BASE = "/apps/my-requests";

export function useMyRequestsRouterPath(
  pathnameFromHost?: string,
  searchFromHost?: string,
): { pathname: string; search: string } {
  return useMemo(() => {
    if (typeof window === "undefined") {
      return { pathname: pathnameFromHost || BASE, search: searchFromHost || "" };
    }
    return {
      pathname: pathnameFromHost || window.location.pathname || BASE,
      search: searchFromHost ?? window.location.search ?? "",
    };
  }, [pathnameFromHost, searchFromHost]);
}

export function resolveInternalRoute(pathname: string): {
  name: "mine" | "work-queue" | "new" | "detail" | "home";
  requestId?: string;
} {
  const normalized = pathname.replace(/\/+$/, "") || BASE;
  if (normalized === BASE || normalized === `${BASE}/mine`) {
    return { name: "mine" };
  }
  if (normalized === `${BASE}/work-queue`) return { name: "work-queue" };
  if (normalized === `${BASE}/new`) return { name: "new" };
  const detail = normalized.match(new RegExp(`^${BASE}/requests/([^/]+)$`));
  if (detail?.[1]) return { name: "detail", requestId: detail[1] };
  return { name: "home" };
}
