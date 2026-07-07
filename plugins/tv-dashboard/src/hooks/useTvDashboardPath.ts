import { useEffect, useState } from "react";

const PREFIX = "/apps/tv-dashboard";

function readPathname(): string {
  if (typeof window === "undefined") return PREFIX;
  return window.location.pathname;
}

/** Prefere a rota mais específica quando host e browser divergem (host stale após pushState). */
function resolvePathname(pathnameFromHost?: string): string {
  const browser = readPathname();
  if (!pathnameFromHost) return browser;

  const normHost = pathnameFromHost.replace(/\/+$/, "") || PREFIX;
  const normBrowser = browser.replace(/\/+$/, "") || PREFIX;
  if (normHost === normBrowser) return browser;

  if (normBrowser.startsWith(`${normHost}/`) || normBrowser.startsWith(`${normHost}?`)) {
    return browser;
  }
  if (normHost.startsWith(`${normBrowser}/`)) {
    return pathnameFromHost;
  }

  return browser;
}

export function useTvDashboardPath(pathnameFromHost?: string) {
  const [pathname, setPathname] = useState(() => resolvePathname(pathnameFromHost));

  useEffect(() => {
    if (!pathnameFromHost) return;

    if (pathnameFromHost === readPathname()) {
      setPathname(pathnameFromHost);
    }
  }, [pathnameFromHost]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const syncFromBrowser = () => {
      setPathname(readPathname());
    };

    window.addEventListener("popstate", syncFromBrowser);
    return () => window.removeEventListener("popstate", syncFromBrowser);
  }, []);

  return pathname;
}
