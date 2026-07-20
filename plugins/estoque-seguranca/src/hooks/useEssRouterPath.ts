import { useEffect, useState } from "react";

import { ESS_ROUTES } from "../constants/routes";

function readBrowserPathname(): string {
  if (typeof window === "undefined") return ESS_ROUTES.home;
  return window.location.pathname;
}

/** Sincroniza a rota do MFE com o pathname do portal e com navegação interna. */
export function useEssRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost ?? readBrowserPathname(),
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

  return pathname;
}

export function navigateEssPath(path: string): void {
  if (typeof window === "undefined") return;
  if (window.location.pathname === path) return;
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
