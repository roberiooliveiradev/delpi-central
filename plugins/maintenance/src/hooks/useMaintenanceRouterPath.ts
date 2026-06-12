import { useEffect, useState } from "react";

import { MAINTENANCE_ROUTES } from "../constants/routes";

function readBrowserPathname(): string {
  if (typeof window === "undefined") return MAINTENANCE_ROUTES.home;
  return window.location.pathname;
}

export function useMaintenanceRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(() => pathnameFromHost ?? readBrowserPathname());

  useEffect(() => {
    if (pathnameFromHost) {
      setPathname(pathnameFromHost);
    }
  }, [pathnameFromHost]);

  useEffect(() => {
    const syncFromBrowser = () => {
      setPathname(readBrowserPathname());
    };

    window.addEventListener("popstate", syncFromBrowser);
    return () => window.removeEventListener("popstate", syncFromBrowser);
  }, []);

  return pathname;
}
