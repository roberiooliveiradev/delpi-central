import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  listPurchaseRequestRequesters,
  type RequesterFacetQuery,
} from "../api/purchaseRequestsApi";
import { ApiClientError } from "../api/httpClient";
import type { PurchaseRequestRequesterOption } from "../types/purchaseRequests";

export function usePurchaseRequestRequesters(query: RequesterFacetQuery, enabled: boolean) {
  const [items, setItems] = useState<PurchaseRequestRequesterOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryRef = useRef(query);
  queryRef.current = query;

  const queryKey = useMemo(() => JSON.stringify(query), [query]);

  const reload = useCallback(async () => {
    const currentQuery = queryRef.current;
    if (!enabled || !currentQuery.branch) return;
    setLoading(true);
    setError(null);
    try {
      const result = await listPurchaseRequestRequesters(currentQuery);
      setItems(result);
    } catch (err) {
      setItems([]);
      if (err instanceof ApiClientError && err.status === 403) {
        setError("Você não possui acesso aos dados solicitados.");
      } else {
        setError(err instanceof Error ? err.message : "Erro ao carregar solicitantes.");
      }
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void reload();
  }, [reload, queryKey]);

  return { items, loading, error, reload };
}
