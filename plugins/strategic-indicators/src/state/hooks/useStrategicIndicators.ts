import { useCallback, useEffect, useMemo, useState } from "react";
import { adaptIndicatorsToView } from "../../data/adapters/indicatorsAdapter";
import {
  fetchStrategicIndicators,
  type FetchStrategicIndicatorsParams,
} from "../../data/api/strategicIndicatorsApi";
import type { IndicatorViewItem } from "../../data/types/indicators";

type UseStrategicIndicatorsParams = {
  departmentId?: string;
  startDate?: string;
  endDate?: string;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicators({
  departmentId,
  startDate,
  endDate,
  getAccessToken,
}: UseStrategicIndicatorsParams) {
  const [items, setItems] = useState<IndicatorViewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params: FetchStrategicIndicatorsParams = {
        departmentId,
        startDate,
        endDate,
        getAccessToken,
      };

      const response = await fetchStrategicIndicators(params);
      setItems(adaptIndicatorsToView(response));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro inesperado ao carregar indicadores.",
      );
    } finally {
      setLoading(false);
    }
  }, [departmentId, startDate, endDate, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  return useMemo(
    () => ({
      items,
      loading,
      error,
      reload: load,
    }),
    [items, loading, error, load],
  );
}