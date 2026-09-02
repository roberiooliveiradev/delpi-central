import { useEffect, useState } from "react";

function readPathname(): string {
  if (typeof window === "undefined") return "/";
  return window.location.pathname;
}

function readSearch(): string {
  if (typeof window === "undefined") return "";
  return window.location.search;
}

export function useProductionPulseRouterPath(pathnameFromHost?: string): {
  pathname: string;
  search: string;
} {
  const [pathname, setPathname] = useState(() => pathnameFromHost ?? readPathname());
  const [search, setSearch] = useState(() => readSearch());

  useEffect(() => {
    if (!pathnameFromHost) return;
    setPathname(pathnameFromHost);
  }, [pathnameFromHost]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const syncFromBrowser = () => {
      setSearch(readSearch());
      setPathname(pathnameFromHost ?? readPathname());
    };

    window.addEventListener("popstate", syncFromBrowser);
    return () => window.removeEventListener("popstate", syncFromBrowser);
  }, [pathnameFromHost]);

  return { pathname, search };
}
