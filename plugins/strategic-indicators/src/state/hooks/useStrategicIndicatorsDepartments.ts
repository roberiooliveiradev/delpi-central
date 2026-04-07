import { useCallback, useEffect, useMemo, useState } from "react";
import { adaptDepartmentsToView } from "../../data/adapters/departmentsAdapter";
import { fetchStrategicIndicatorsDepartments } from "../../data/api/strategicIndicatorsDepartmentsApi";
import type { DepartmentOverviewViewItem } from "../../data/types/departments";

type UseStrategicIndicatorsDepartmentsParams = {
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsDepartments({
  getAccessToken,
}: UseStrategicIndicatorsDepartmentsParams) {
  const [items, setItems] = useState<DepartmentOverviewViewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetchStrategicIndicatorsDepartments(getAccessToken);
      setItems(adaptDepartmentsToView(response));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro inesperado ao carregar departamentos.",
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