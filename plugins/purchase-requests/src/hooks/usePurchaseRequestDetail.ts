import { useCallback, useEffect, useState } from "react";

import { getPurchaseRequest } from "../api/purchaseRequestsApi";
import { ApiClientError } from "../api/httpClient";
import type { PurchaseRequestDetail, PurchaseRequestsQuery } from "../types/purchaseRequests";

type DetailTarget = {
  branch: string;
  requestNumber: string;
} | null;

export function usePurchaseRequestDetail(
  target: DetailTarget,
  filters: Pick<PurchaseRequestsQuery, "date_from" | "date_to" | "cost_center">,
) {
  const [data, setData] = useState<PurchaseRequestDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const reload = useCallback(async () => {
    if (!target) {
      setData(null);
      setError(null);
      setNotFound(false);
      return;
    }
    setLoading(true);
    setError(null);
    setNotFound(false);
    try {
      const result = await getPurchaseRequest(target.branch, target.requestNumber, filters);
      setData(result);
    } catch (err) {
      setData(null);
      if (err instanceof ApiClientError && err.status === 404) {
        setNotFound(true);
        setError("Solicitação não encontrada ou indisponível.");
      } else if (err instanceof ApiClientError && err.status === 403) {
        setError("Você não possui acesso aos dados solicitados.");
      } else {
        setError(err instanceof Error ? err.message : "Erro ao carregar detalhe.");
      }
    } finally {
      setLoading(false);
    }
  }, [filters.cost_center, filters.date_from, filters.date_to, target]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    data,
    loading,
    error,
    notFound,
    reload,
  };
}
