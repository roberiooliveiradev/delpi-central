import { useEffect, useState } from "react";

export function useTvDashboardPath(pathnameFromHost?: string) {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost ?? (typeof window !== "undefined" ? window.location.pathname : "/apps/tv-dashboard"),
  );

  useEffect(() => {
    if (pathnameFromHost) setPathname(pathnameFromHost);
  }, [pathnameFromHost]);

  useEffect(() => {
    const onPop = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  return pathname;
}
