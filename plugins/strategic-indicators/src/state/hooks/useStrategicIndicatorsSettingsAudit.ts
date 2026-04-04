import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchStrategicIndicatorsSettingsAudit } from "../../data/api/strategicIndicatorsSettingsAuditApi";
import type { StrategicIndicatorsSettingsAuditItem } from "../../data/types/settingsAudit";

type UseStrategicIndicatorsSettingsAuditParams = {
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsSettingsAudit({
  getAccessToken,
}: UseStrategicIndicatorsSettingsAuditParams) {
  const [items, setItems] = useState<StrategicIndicatorsSettingsAuditItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetchStrategicIndicatorsSettingsAudit(getAccessToken);
      setItems(response.items);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro inesperado ao carregar auditoria.",
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
      items,
      loading,
      error,
      reload: load,
    }),
    [items, loading, error, load],
  );
}