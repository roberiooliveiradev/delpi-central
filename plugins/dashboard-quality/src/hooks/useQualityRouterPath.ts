import { useEffect, useState } from "react";
import { dispatchFilterRouteSync } from "../utils/filterUrl";

function readPathname(fallback?: string): string {
  if (typeof window === "undefined") return fallback ?? "";
  return window.location.pathname;
}

export function useQualityRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(pathnameFromHost ?? readPathname());

  useEffect(() => {
    if (pathnameFromHost) {
      setPathname(pathnameFromHost);
    }
  }, [pathnameFromHost]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const sync = () => setPathname(readPathname(pathnameFromHost));
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, [pathnameFromHost]);

  useEffect(() => {
    dispatchFilterRouteSync();
  }, [pathname]);

  return pathname;
}
