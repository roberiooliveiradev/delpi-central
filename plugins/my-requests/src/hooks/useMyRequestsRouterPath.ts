import { useEffect, useState } from "react";

const BASE = "/apps/my-requests";

export function useMyRequestsRouterPath(
  pathnameFromHost?: string,
  searchFromHost?: string,
): { pathname: string; search: string } {
  const [routeEpoch, setRouteEpoch] = useState(0);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const syncFromBrowser = () => {
      setRouteEpoch((value) => value + 1);
    };

    window.addEventListener("popstate", syncFromBrowser);
    return () => window.removeEventListener("popstate", syncFromBrowser);
  }, []);

  void routeEpoch;

  if (typeof window !== "undefined" && window.location?.pathname) {
    return {
      pathname: window.location.pathname || BASE,
      search: window.location.search ?? "",
    };
  }

  return {
    pathname: pathnameFromHost || BASE,
    search: searchFromHost || "",
  };
}

export function resolveInternalRoute(pathname: string): {
  name: "mine" | "work-queue" | "new" | "detail" | "edit" | "admin" | "home";
  requestId?: string;
} {
  const normalized = pathname.replace(/\/+$/, "") || BASE;
  if (normalized === BASE || normalized === `${BASE}/mine`) {
    return { name: "mine" };
  }
  if (normalized === `${BASE}/work-queue`) return { name: "work-queue" };
  if (normalized === `${BASE}/new`) return { name: "new" };
  if (normalized === `${BASE}/admin`) return { name: "admin" };
  const edit = normalized.match(new RegExp(`^${BASE}/requests/([^/]+)/edit$`));
  if (edit?.[1]) return { name: "edit", requestId: edit[1] };
  const detail = normalized.match(new RegExp(`^${BASE}/requests/([^/]+)$`));
  if (detail?.[1]) return { name: "detail", requestId: detail[1] };
  return { name: "home" };
}
