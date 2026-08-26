import { useEffect, useState } from "react";

export function usePurchaseRequestsRouterPath(
  pathnameFromHost?: string,
  searchFromHost?: string,
) {
  const [pathname, setPathname] = useState(() =>
    pathnameFromHost || (typeof window !== "undefined" ? window.location.pathname : ""),
  );
  const [search, setSearch] = useState(
    () => searchFromHost ?? (typeof window !== "undefined" ? window.location.search : ""),
  );

  useEffect(() => {
    if (pathnameFromHost) {
      setPathname(pathnameFromHost);
    }
    if (searchFromHost !== undefined) {
      setSearch(searchFromHost);
    } else if (pathnameFromHost && typeof window !== "undefined") {
      setSearch(window.location.search);
    }
  }, [pathnameFromHost, searchFromHost]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const sync = () => {
      setPathname(window.location.pathname);
      setSearch(window.location.search);
    };

    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  return { pathname, search };
}
