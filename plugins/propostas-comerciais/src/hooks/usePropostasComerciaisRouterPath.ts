import { useEffect, useState } from "react";

import { PROPOSTAS_COMERCIAIS_ROUTES } from "../utils/route";

function readBrowserPathname(): string {
  if (typeof window === "undefined") return PROPOSTAS_COMERCIAIS_ROUTES.home;
  return window.location.pathname;
}

export function usePropostasComerciaisRouterPath(pathnameFromHost?: string): string {
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
