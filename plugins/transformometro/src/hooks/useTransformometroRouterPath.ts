import { useEffect, useState } from "react";

import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import { canonicalizeTransformometroPath } from "../utils/routeParser";

function readBrowserPathname(): string {
  if (typeof window === "undefined") return TRANSFORMOMETRO_ROUTES.home;
  return canonicalizeTransformometroPath(window.location.pathname);
}

function redirectLegacyPathIfNeeded() {
  if (typeof window === "undefined") return;
  const current = window.location.pathname;
  const canonical = canonicalizeTransformometroPath(current);
  if (canonical !== current) {
    window.history.replaceState(null, "", `${canonical}${window.location.hash}`);
  }
}

export function useTransformometroRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(() =>
    pathnameFromHost
      ? canonicalizeTransformometroPath(pathnameFromHost)
      : readBrowserPathname(),
  );

  useEffect(() => {
    if (pathnameFromHost) {
      setPathname(canonicalizeTransformometroPath(pathnameFromHost));
      return;
    }
    redirectLegacyPathIfNeeded();
    setPathname(readBrowserPathname());
  }, [pathnameFromHost]);

  useEffect(() => {
    const syncFromBrowser = () => {
      redirectLegacyPathIfNeeded();
      setPathname(readBrowserPathname());
    };

    window.addEventListener("popstate", syncFromBrowser);
    return () => window.removeEventListener("popstate", syncFromBrowser);
  }, []);

  return pathname;
}
