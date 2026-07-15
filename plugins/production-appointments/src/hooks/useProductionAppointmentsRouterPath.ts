import { useEffect, useState } from "react";

export function useProductionAppointmentsRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost ?? (typeof window !== "undefined" ? window.location.pathname : ""),
  );

  useEffect(() => {
    if (!pathnameFromHost) return;
    setPathname(pathnameFromHost);
  }, [pathnameFromHost]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const sync = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  return pathname;
}
