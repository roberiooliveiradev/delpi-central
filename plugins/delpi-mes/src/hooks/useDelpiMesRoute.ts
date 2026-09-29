import { useCallback, useEffect, useState } from "react";

import { BASE_PATH, type BranchCode, type DelpiMesArea } from "../constants/routes";

export type DelpiMesRoute = { area: DelpiMesArea; branch: BranchCode; workCenter: string | null };

export function parseDelpiMesRoute(pathname: string, search: string): DelpiMesRoute {
  const suffix = pathname.startsWith(BASE_PATH) ? pathname.slice(BASE_PATH.length) : "";
  const segment = suffix.split("/").filter(Boolean)[0];
  const area: DelpiMesArea =
    segment === "downtimes" || segment === "history" ? segment : "monitoring";
  const params = new URLSearchParams(search);
  const requestedBranch = params.get("branch");
  const workCenter = area === "monitoring" ? params.get("workCenter") : null;
  return { area, branch: requestedBranch === "02" ? "02" : "01", workCenter };
}

export function buildDelpiMesHref(area: DelpiMesArea, branch: BranchCode, workCenter?: string): string {
  const href = `${BASE_PATH}/${area}?branch=${branch}`;
  return workCenter ? `${href}&workCenter=${encodeURIComponent(workCenter)}` : href;
}

export function useDelpiMesRoute(pathnameFromHost?: string) {
  const [browserLocation, setBrowserLocation] = useState(() => ({
    pathname: window.location.pathname,
    search: window.location.search,
  }));

  useEffect(() => {
    const sync = () => setBrowserLocation({
      pathname: window.location.pathname,
      search: window.location.search,
    });
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  const navigate = useCallback((href: string) => {
    window.history.pushState({}, "", href);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, []);

  return {
    route: parseDelpiMesRoute(pathnameFromHost ?? browserLocation.pathname, browserLocation.search),
    navigate,
  };
}
