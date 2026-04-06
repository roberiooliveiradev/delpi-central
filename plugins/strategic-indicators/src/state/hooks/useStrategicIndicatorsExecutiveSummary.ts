import { useCallback, useEffect, useMemo, useState } from "react";
import { adaptExecutiveSummaryToView } from "../../data/adapters/executiveSummaryAdapter";
import { fetchStrategicIndicatorsExecutiveSummary } from "../../data/api/strategicIndicatorsExecutiveSummaryApi";
import type { ExecutiveDashboardViewData } from "../../data/types/executiveSummary";

type UseStrategicIndicatorsExecutiveSummaryParams = {
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsExecutiveSummary({
  getAccessToken,
}: UseStrategicIndicatorsExecutiveSummaryParams) {
  const [data, setData] = useState<ExecutiveDashboardViewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetchStrategicIndicatorsExecutiveSummary(
        getAccessToken,
      );
      setData(adaptExecutiveSummaryToView(response));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro inesperado ao carregar resumo executivo.",
      );
    } finally {
      setLoading(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  return useMemo(
    () => ({
      data,
      loading,
      error,
      reload: load,
    }),
    [data, loading, error, load],
  );
}