import { useEffect, useState } from "react";

export function useProductionPulseRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost || (typeof window !== "undefined" ? window.location.pathname : "/"),
  );

  useEffect(() => {
    if (pathnameFromHost) {
      setPathname(pathnameFromHost);
    }
  }, [pathnameFromHost]);

  return pathname;
}
