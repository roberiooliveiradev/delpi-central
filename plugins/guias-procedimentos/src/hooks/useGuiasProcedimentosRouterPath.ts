import { useEffect, useState } from "react";

import { GUIAS_PROCEDIMENTOS_ROUTES } from "../utils/route";

function readBrowserPathname(): string {
  if (typeof window === "undefined") return GUIAS_PROCEDIMENTOS_ROUTES.home;
  return window.location.pathname;
}

/**
 * Prioriza `window.location.pathname` (pushState / popstate / refresh).
 * `pathnameFromHost` é fallback quando o browser path ainda não está disponível.
 * Tick via `popstate` força releitura após navegação interna sem reload.
 */
export function useGuiasProcedimentosRouterPath(
  pathnameFromHost?: string,
): string {
  const [, setRouteTick] = useState(0);

  useEffect(() => {
    const syncFromBrowser = () => {
      setRouteTick((value) => value + 1);
    };

    window.addEventListener("popstate", syncFromBrowser);
    return () => window.removeEventListener("popstate", syncFromBrowser);
  }, []);

  const browserPath = readBrowserPathname();
  if (browserPath) {
    return browserPath;
  }

  return pathnameFromHost ?? GUIAS_PROCEDIMENTOS_ROUTES.home;
}
