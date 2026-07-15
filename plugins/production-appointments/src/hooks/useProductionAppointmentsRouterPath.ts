import { useEffect, useState } from "react";

import { PRODUCTION_APPOINTMENTS_BASE_PATH } from "../constants/branches";
import { APPOINTMENTS_ROUTE_CHANGE_EVENT } from "../utils/navigation";

function readPathname(): string {
  if (typeof window === "undefined") return "";
  return window.location.pathname;
}

function normalize(path: string): string {
  if (path.length > 1 && path.endsWith("/")) return path.slice(0, -1);
  return path;
}

function isAppPath(path: string): boolean {
  return normalize(path).startsWith(PRODUCTION_APPOINTMENTS_BASE_PATH);
}

/**
 * Resolve rota preferindo o browser quando ele já está num detalhe
 * mais profundo que o pathname do host (ex.: `/sc/op/:id` vs `/sc`).
 */
export function resolveAppointmentsPathname(
  pathnameFromHost: string | undefined,
  browserPathname: string,
): string {
  const host = pathnameFromHost ? normalize(pathnameFromHost) : "";
  const browser = normalize(browserPathname);

  if (!host) return browser || PRODUCTION_APPOINTMENTS_BASE_PATH;
  if (!browser) return host;
  if (host === browser) return browser;

  if (isAppPath(browser) && browser.startsWith(`${host}/`)) {
    return browser;
  }

  if (isAppPath(host)) return host;
  if (isAppPath(browser)) return browser;
  return host || browser;
}

export function useProductionAppointmentsRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(() =>
    resolveAppointmentsPathname(pathnameFromHost, readPathname()),
  );

  useEffect(() => {
    setPathname(resolveAppointmentsPathname(pathnameFromHost, readPathname()));
  }, [pathnameFromHost]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const syncFromBrowser = () => {
      setPathname(resolveAppointmentsPathname(pathnameFromHost, readPathname()));
    };

    const syncFromInternalNav = (event: Event) => {
      const detail = (event as CustomEvent<{ pathname?: string }>).detail;
      const next = detail?.pathname ? normalize(detail.pathname) : readPathname();
      setPathname(next);
    };

    window.addEventListener("popstate", syncFromBrowser);
    window.addEventListener(APPOINTMENTS_ROUTE_CHANGE_EVENT, syncFromInternalNav);
    return () => {
      window.removeEventListener("popstate", syncFromBrowser);
      window.removeEventListener(APPOINTMENTS_ROUTE_CHANGE_EVENT, syncFromInternalNav);
    };
  }, [pathnameFromHost]);

  return pathname;
}
