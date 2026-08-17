import { useEffect, useState } from "react";

import { COMMERCIAL_BASE_PATH, normalizePathname } from "./pluginRoutes";

export function usePluginRouterPath(
  pathnameFromHost?: string,
  basePath: string = COMMERCIAL_BASE_PATH,
): string {
  const fallback = normalizePathname(basePath);
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
    return window.location.pathname;
  }

  return pathnameFromHost ?? fallback;
}
