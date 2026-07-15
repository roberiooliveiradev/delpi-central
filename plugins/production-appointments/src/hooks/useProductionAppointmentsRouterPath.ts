import { useMemo } from "react";

import { branchRouteFromPathname } from "../constants/branches";

/**
 * Prefer pathname do host (portal); fallback para window.location.
 */
export function useProductionAppointmentsRouterPath(pathnameFromHost?: string): string {
  return useMemo(() => {
    if (pathnameFromHost) return pathnameFromHost;
    if (typeof window !== "undefined") return window.location.pathname;
    return "";
  }, [pathnameFromHost]);
}

export function useBranchFromPath(pathname?: string) {
  return branchRouteFromPathname(pathname);
}
