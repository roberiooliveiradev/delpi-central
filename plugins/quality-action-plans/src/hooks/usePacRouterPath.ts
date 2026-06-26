import { useEffect, useState } from "react";

function readPathname(): string {
  if (typeof window === "undefined") return "";
  return window.location.pathname;
}

export function usePacRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(() => pathnameFromHost ?? readPathname());

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
