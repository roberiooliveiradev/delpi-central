// portal/src/ui/usage/useAdminUserUsageStats.ts

import { useCallback, useEffect, useRef, useState } from "react";

import type { UserUsagePeriodDays, UserUsageStatistics } from "../../data/userUsageTypes";
import { useAdminApi } from "../../hooks/useAdminApi";

type LoadOptions = {
  silent?: boolean;
};

export function useAdminUserUsageStats(
  userId: string,
  initialPeriod: UserUsagePeriodDays = 30,
  enabled = true,
) {
  const [periodDays, setPeriodDays] = useState<UserUsagePeriodDays>(initialPeriod);
  const [data, setData] = useState<UserUsageStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasDataRef = useRef(false);

  const api = useAdminApi();

  const load = useCallback(
    async (options?: LoadOptions) => {
      if (!userId || !enabled) {
        return;
      }

      const silent = Boolean(options?.silent && hasDataRef.current);

      if (!silent) {
        setLoading(true);
      }
      setError(null);

      try {
        const result = await api.getAdminUserUsageStatistics(userId, periodDays);
        setData(result);
        hasDataRef.current = true;
      } catch (err) {
        if (!silent) {
          setData(null);
          hasDataRef.current = false;
        }
        setError(
          err instanceof Error
            ? err.message
            : "Falha ao carregar estatísticas de uso do usuário",
        );
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [api, enabled, periodDays, userId],
  );

  useEffect(() => {
    if (!enabled) {
      return;
    }
    void load();
  }, [enabled, load]);

  const changePeriod = useCallback((next: UserUsagePeriodDays) => {
    hasDataRef.current = false;
    setPeriodDays(next);
  }, []);

  return {
    data,
    loading,
    error,
    load,
    periodDays,
    changePeriod,
  };
}
