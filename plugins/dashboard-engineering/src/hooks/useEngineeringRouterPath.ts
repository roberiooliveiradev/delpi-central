import { useEffect, useState } from "react";
import { ENGINEERING_ROUTES } from "../constants/routes";
import { dispatchFilterRouteSync } from "../utils/filterUrl";

function readBrowserPathname(): string {
  if (typeof window === "undefined") return ENGINEERING_ROUTES.home;
  return window.location.pathname;
}

export function useEngineeringRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost ?? readBrowserPathname()
  );

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

  useEffect(() => {
    dispatchFilterRouteSync();
  }, [pathname]);

  return pathname;
}
