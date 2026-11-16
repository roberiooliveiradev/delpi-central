import { useEffect, useState } from "react";
import { ApiRequestError } from "../../api/httpClient";
import {
  getSupplierPerformance,
  type SupplierPerformanceResponse,
} from "../../api/supplierPerformance";

export function useSupplierPerformance(filters: {
  branches: string[];
  from: string;
  to: string;
}) {
  const [data, setData] = useState<SupplierPerformanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const branchKey = filters.branches.join(",");

  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError(null);
    setLoading(true);
    if (!branchKey) {
      setError("Nenhuma unidade disponível para consulta.");
      setLoading(false);
      return () => controller.abort();
    }
    getSupplierPerformance(
      { branches: branchKey.split(","), from: filters.from, to: filters.to },
      controller.signal,
    )
      .then((payload) => {
        if (!controller.signal.aborted) setData(payload);
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          reason instanceof ApiRequestError && reason.detail
            ? reason.detail
            : "Não foi possível carregar o IDF. Tente atualizar a consulta.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branchKey, filters.from, filters.to, reloadKey]);

  return {
    data,
    loading,
    error,
    reload: () => setReloadKey((value) => value + 1),
  };
}
