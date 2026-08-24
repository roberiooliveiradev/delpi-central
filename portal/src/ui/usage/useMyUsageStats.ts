// portal/src/ui/usage/useMyUsageStats.ts

import { useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { ApiClient } from "../../data/apiClient";
import { CoreApi } from "../../data/coreApi";
import type { UserUsagePeriodDays, UserUsageStatistics } from "../../data/userUsageTypes";
import { AuthContext } from "../../state/AuthContext";

type LoadOptions = {
  silent?: boolean;
};

export function useMyUsageStats(initialPeriod: UserUsagePeriodDays = 30) {
  const { getAccessToken, refreshToken } = useContext(AuthContext);
  const [periodDays, setPeriodDays] = useState<UserUsagePeriodDays>(initialPeriod);
  const [data, setData] = useState<UserUsageStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const hasDataRef = useRef(false);

  const api = useMemo(
    () =>
      new CoreApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  const load = useCallback(
    async (options?: LoadOptions) => {
      const silent = Boolean(options?.silent && hasDataRef.current);

      if (!silent) {
        setLoading(true);
      }
      setError(null);

      try {
        const result = await api.getMyUsageStatistics(periodDays);
        setData(result);
        hasDataRef.current = true;
      } catch (err) {
        if (!silent) {
          setData(null);
          hasDataRef.current = false;
        }
        setError(
          err instanceof Error ? err.message : "Falha ao carregar seu uso na plataforma",
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
