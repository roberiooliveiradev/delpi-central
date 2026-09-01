import { useEffect, useState } from "react";

export function useProductionPulseRouterPath(pathnameFromHost?: string) {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost || (typeof window !== "undefined" ? window.location.pathname : "/"),
  );
  const [search, setSearch] = useState(
    () => (typeof window !== "undefined" ? window.location.search : ""),
  );

  useEffect(() => {
    if (pathnameFromHost) {
      setPathname(pathnameFromHost);
      setSearch(typeof window !== "undefined" ? window.location.search : "");
      return;
    }
    const onPop = () => {
      setPathname(window.location.pathname);
      setSearch(window.location.search);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [pathnameFromHost]);

  return { pathname, search };
}
