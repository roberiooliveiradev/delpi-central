import { useEffect, useState } from "react";

import { PRODUCTION_PULSE_BASE_PATH } from "../constants/routes";

function readPathname(): string {
  if (typeof window === "undefined") return PRODUCTION_PULSE_BASE_PATH;
  return window.location.pathname;
}

function readSearch(): string {
  if (typeof window === "undefined") return "";
  return window.location.search;
}

/**
 * Path efetivo no portal federado: prioriza `window.location` após pushState interno.
 * `pathnameFromHost` só entra como fallback fora do browser (SSR/standalone).
 */
export function useProductionPulseRouterPath(pathnameFromHost?: string): {
  pathname: string;
  search: string;
} {
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

  if (typeof window !== "undefined") {
    return {
      pathname: readPathname(),
      search: readSearch(),
    };
  }

  return {
    pathname: pathnameFromHost ?? PRODUCTION_PULSE_BASE_PATH,
    search: "",
  };
}
