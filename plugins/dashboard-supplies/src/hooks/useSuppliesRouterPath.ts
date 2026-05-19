import { useEffect, useState } from "react";
import { SUPPLIES_ROUTES } from "../constants/routes";

function readBrowserPathname(): string {
  if (typeof window === "undefined") return SUPPLIES_ROUTES.home;
  return window.location.pathname;
}

/**
 * Sincroniza a rota exibida com o pathname do portal e com pushState interno (abas).
 * O React Router do host não reage a history.pushState só com popstate — por isso
 * escutamos popstate e lemos window.location.pathname.
 */
export function useSuppliesRouterPath(pathnameFromHost?: string): string {
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

  return pathname;
}
