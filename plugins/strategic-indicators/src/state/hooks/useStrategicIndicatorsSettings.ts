import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchStrategicIndicatorsSettings,
  updateStrategicIndicatorsSettings,
} from "../../data/api/strategicIndicatorsSettingsApi";
import type {
  StrategicIndicatorsSettingsResponse,
  StrategicIndicatorsSettingsUpdateRequest,
} from "../../data/types/settings";

type UseStrategicIndicatorsSettingsParams = {
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsSettings({
  getAccessToken,
}: UseStrategicIndicatorsSettingsParams) {
  const [data, setData] = useState<StrategicIndicatorsSettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetchStrategicIndicatorsSettings(getAccessToken);
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado ao carregar.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = useCallback(
    async (payload: StrategicIndicatorsSettingsUpdateRequest) => {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      try {
        const response = await updateStrategicIndicatorsSettings(
          payload,
          getAccessToken,
        );
        setSuccessMessage(response.message);
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro inesperado ao salvar.");
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [getAccessToken, load],
  );

  return useMemo(
    () => ({
      data,
      loading,
      saving,
      error,
      successMessage,
      reload: load,
      save,
      clearSuccessMessage: () => setSuccessMessage(null),
    }),
    [data, loading, saving, error, successMessage, load, save],
  );
}