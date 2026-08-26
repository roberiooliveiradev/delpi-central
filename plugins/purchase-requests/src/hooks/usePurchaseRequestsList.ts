import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { listPurchaseRequests } from "../api/purchaseRequestsApi";
import { ApiClientError } from "../api/httpClient";
import type { PurchaseRequestListResponse, PurchaseRequestsQuery } from "../types/purchaseRequests";

export function usePurchaseRequestsList(query: PurchaseRequestsQuery, enabled: boolean) {
  const [data, setData] = useState<PurchaseRequestListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);

  const queryRef = useRef(query);
  queryRef.current = query;

  const queryKey = useMemo(() => JSON.stringify(query), [query]);

  const reload = useCallback(async () => {
    const currentQuery = queryRef.current;
    if (!enabled || !currentQuery.branch) return;
    setLoading(true);
    setError(null);
    try {
      const result = await listPurchaseRequests(currentQuery);
      setData(result);
      setHasLoaded(true);
    } catch (err) {
      setData(null);
      if (err instanceof ApiClientError && err.status === 403) {
        setError("Você não possui acesso aos dados solicitados.");
      } else {
        setError(err instanceof Error ? err.message : "Erro ao carregar solicitações.");
      }
      setHasLoaded(true);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void reload();
  }, [reload, queryKey]);

  return {
    data,
    loading,
    error,
    hasLoaded,
    reload,
  };
}
