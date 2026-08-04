import { useEffect, useState } from "react";

import { normalizePathname, PVA_BASE_PATH } from "./pluginRoutes.ts";

/**
 * Pathname efetivo para o shell.
 * - Em sessão Portal: `window.location` já reflete o path (mount/updateRoute + pushState).
 * - `pathnameFromHost` é fallback (SSR/standalone) e alinhamento inicial.
 * - `popstate` força re-leitura após navegação interna (pushState).
 */
export function usePluginRouterPath(
  pathnameFromHost?: string,
  basePath: string = PVA_BASE_PATH,
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
