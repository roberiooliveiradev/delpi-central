import { useCallback, useEffect, useMemo, useState } from "react";
import { adaptDepartmentDetailsToView } from "../../data/adapters/departmentDetailsAdapter";
import { fetchStrategicIndicatorsDepartmentDetails } from "../../data/api/strategicIndicatorsDepartmentDetailsApi";
import type { DepartmentDetailsViewData } from "../../data/types/departmentDetails";

type UseStrategicIndicatorsDepartmentDetailsParams = {
  departmentId: string;
  getAccessToken?: () => string | undefined;
};

export function useStrategicIndicatorsDepartmentDetails({
  departmentId,
  getAccessToken,
}: UseStrategicIndicatorsDepartmentDetailsParams) {
  const [data, setData] = useState<DepartmentDetailsViewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!departmentId) {
      setData(null);
      setLoading(false);
      setError("Departamento inválido.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetchStrategicIndicatorsDepartmentDetails(
        departmentId,
        getAccessToken,
      );
      setData(adaptDepartmentDetailsToView(response));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro inesperado ao carregar detalhe do departamento.",
      );
    } finally {
      setLoading(false);
    }
  }, [departmentId, getAccessToken]);

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