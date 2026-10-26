import { useCallback, useEffect, useRef, useState } from "react";

import { getDowntimes } from "../api/mesApi";
import type { DowntimesQuery, DowntimesResponse } from "../types/mes";

/** Lista gerencial de paradas — atualização manual (sem polling), com
 * cancelamento de requisições obsoletas e preservação do último snapshot
 * quando uma atualização falha. */
export function useDowntimesData(query: DowntimesQuery) {
  const [data, setData] = useState<DowntimesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const hasData = useRef(false);
  const queryKey = JSON.stringify(query);

  const refresh = useCallback(async () => {
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    setRefreshing(hasData.current);
    try {
      const response = await getDowntimes(JSON.parse(queryKey), next.signal);
      setData(response);
      hasData.current = true;
      setError(null);
    } catch (reason) {
      if (!next.signal.aborted) {
        setError(reason instanceof Error ? reason.message : "Falha ao consultar as paradas.");
      }
    } finally {
      if (!next.signal.aborted) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, [queryKey]);

  useEffect(() => {
    queueMicrotask(() => {
      setData(null);
      setError(null);
      setLoading(true);
      hasData.current = false;
    });
    void refresh();
    return () => controller.current?.abort();
  }, [refresh]);

  return { data, error, loading, refreshing, refresh };
}
