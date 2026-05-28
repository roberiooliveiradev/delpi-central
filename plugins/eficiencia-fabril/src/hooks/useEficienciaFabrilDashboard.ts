import { useCallback, useEffect, useState } from "react";

import { getEficienciaFabrilDashboard } from "../api/eficienciaFabrilApi";
import type {
  EficienciaFabrilDashboardData,
  EficienciaFabrilFilterParams,
} from "../types/eficienciaFabril";

export function useEficienciaFabrilDashboard(params: EficienciaFabrilFilterParams) {
  const [data, setData] = useState<EficienciaFabrilDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);

    try {
      const result = await getEficienciaFabrilDashboard(params, signal);
      setData(result);
    } catch (err) {
      if (signal?.aborted) return;
      const message =
        err instanceof Error ? err.message : "Erro ao carregar dashboard";
      setError(message);
      setData(null);
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, [params]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  return {
    data,
    loading,
    error,
    reload: () => load(),
  };
}
