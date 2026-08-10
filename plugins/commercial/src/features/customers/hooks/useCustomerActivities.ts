import { useCallback, useEffect, useRef, useState } from "react";

import {
  listCustomerActivities,
  type CommercialActivityDto,
} from "../../../api/worklistApi";

export type UseCustomerActivitiesResult = {
  items: CommercialActivityDto[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  hasData: boolean;
  reload: () => void;
};

export function useCustomerActivities(
  codigo: string,
  loja: string,
  enabled: boolean,
): UseCustomerActivitiesResult {
  const [items, setItems] = useState<CommercialActivityDto[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasData, setHasData] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const hasDataRef = useRef(false);

  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    const isRefresh = hasDataRef.current;

    async function run() {
      try {
        if (isRefresh) setRefreshing(true);
        else setLoading(true);
        setError(null);
        const rows = await listCustomerActivities(codigo, loja, controller.signal);
        if (controller.signal.aborted) return;
        setItems(rows);
        hasDataRef.current = true;
        setHasData(true);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar atividades.");
        if (!hasDataRef.current) setItems([]);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [codigo, loja, enabled, reloadKey]);

  return {
    items,
    loading: enabled && loading,
    refreshing: enabled && refreshing,
    error,
    hasData,
    reload,
  };
}
