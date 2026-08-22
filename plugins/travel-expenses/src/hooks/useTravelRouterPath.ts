import { useEffect, useState } from "react";

export type TravelRoute =
  | { kind: "hub" }
  | { kind: "list"; scope: "mine" | "unit" }
  | { kind: "new" }
  | { kind: "detail"; reportId: string }
  | { kind: "package"; reportId: string }
  | { kind: "unknown" };

export function useTravelRouterPath(pathnameFromHost?: string) {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost || window.location.pathname,
  );
  const [search, setSearch] = useState(() => window.location.search);

  useEffect(() => {
    if (pathnameFromHost) {
      setPathname(pathnameFromHost);
      setSearch(window.location.search);
      return;
    }
    const onPop = () => {
      setPathname(window.location.pathname);
      setSearch(window.location.search);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [pathnameFromHost]);

  return { pathname, search };
}

export function parseTravelRoute(pathname: string, search = ""): TravelRoute {
  const path = pathname.replace(/\/+$/, "") || "/";
  const query = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  if (path === "/apps/travel-expenses") return { kind: "hub" };
  if (path === "/apps/travel-expenses/reports/new") return { kind: "new" };
  const pack = path.match(/^\/apps\/travel-expenses\/reports\/([^/]+)\/(?:package|report)$/);
  if (pack) return { kind: "package", reportId: pack[1] };
  const detail = path.match(/^\/apps\/travel-expenses\/reports\/([^/]+)$/);
  if (detail) return { kind: "detail", reportId: detail[1] };
  if (path === "/apps/travel-expenses/reports") {
    return { kind: "list", scope: query.get("scope") === "unit" ? "unit" : "mine" };
  }
  return { kind: "unknown" };
}

export function readListSearch(search: string) {
  const query = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  return {
    scope: (query.get("scope") === "unit" ? "unit" : "mine") as "mine" | "unit",
    unit: query.get("unit") || "",
    q: query.get("q") || "",
    periodFrom: query.get("from") || "",
    periodTo: query.get("to") || "",
  };
}

export function navigateTravel(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function replaceTravel(path: string) {
  window.history.replaceState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
