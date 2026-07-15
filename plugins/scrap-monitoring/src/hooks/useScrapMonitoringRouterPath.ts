import { useMemo } from "react";

import { SCRAP_MONITORING_BASE_PATH } from "../constants/branches";

export function useScrapMonitoringRouterPath(pathnameFromHost?: string): string {
  return useMemo(() => {
    if (pathnameFromHost && pathnameFromHost.trim()) {
      return pathnameFromHost;
    }
    if (typeof window !== "undefined" && window.location?.pathname) {
      return window.location.pathname;
    }
    return `${SCRAP_MONITORING_BASE_PATH}/sc`;
  }, [pathnameFromHost]);
}
