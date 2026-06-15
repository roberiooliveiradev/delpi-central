import { useEffect, useRef } from "react";

export const DASHBOARD_AUTO_REFRESH_MS = 5 * 60_000;

export function useAutoRefresh(
  onRefresh: () => void,
  intervalMs: number = DASHBOARD_AUTO_REFRESH_MS,
  enabled = true
): void {
  const onRefreshRef = useRef(onRefresh);
  onRefreshRef.current = onRefresh;

  useEffect(() => {
    if (!enabled) return;

    const id = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      onRefreshRef.current();
    }, intervalMs);

    return () => window.clearInterval(id);
  }, [enabled, intervalMs]);
}
