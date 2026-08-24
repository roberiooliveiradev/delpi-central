// src/ui/admin/stats/useAdminEngagementStats.ts

import { useCallback, useEffect, useRef, useState } from "react";

import type { AdminEngagementStatistics } from "../../../data/adminApi";
import { useAdminApi } from "../../../hooks/useAdminApi";
import { STATS_AUTO_REFRESH_MS } from "./statsTheme";

export type EngagementPeriodDays = 7 | 30 | 90;

type LoadOptions = {
  silent?: boolean;
};

export function useAdminEngagementStats(initialPeriod: EngagementPeriodDays = 30) {
  const [periodDays, setPeriodDays] = useState<EngagementPeriodDays>(initialPeriod);
  const [engagement, setEngagement] = useState<AdminEngagementStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hasDataRef = useRef(false);

  const api = useAdminApi();

  const load = useCallback(
    async (options?: LoadOptions) => {
      const silent = Boolean(options?.silent && hasDataRef.current);

      if (!silent) {
        setLoading(true);
      }
      setError(null);

      try {
        const data = await api.getAdminEngagementStatistics(periodDays);
        setEngagement(data);
        hasDataRef.current = true;
      } catch (err) {
        if (!silent) {
          setEngagement(null);
          hasDataRef.current = false;
        }
        setError(
          err instanceof Error
            ? err.message
            : "Falha ao carregar estatísticas de engajamento",
        );
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [api, periodDays],
  );

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const tick = () => {
      if (document.visibilityState !== "visible") return;
      void load({ silent: true });
    };

    const intervalId = window.setInterval(tick, STATS_AUTO_REFRESH_MS);
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void load({ silent: true });
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [load]);

  const changePeriod = useCallback((next: EngagementPeriodDays) => {
    setPeriodDays(next);
    hasDataRef.current = false;
  }, []);

  return {
    engagement,
    loading,
    error,
    load,
    periodDays,
    changePeriod,
    autoRefreshSeconds: STATS_AUTO_REFRESH_MS / 1000,
  };
}
