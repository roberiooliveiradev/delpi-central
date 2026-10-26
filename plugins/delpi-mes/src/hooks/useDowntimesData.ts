import { useCallback, useEffect, useRef, useState } from "react";

import { getDowntimes } from "../api/mesApi";
import type { DowntimesQuery, DowntimesResponse } from "../types/mes";

type DowntimesSnapshot = {
  key: string;
  data: DowntimesResponse | null;
  error: string | null;
  refreshing: boolean;
};

/** Lista gerencial de paradas — atualização manual (sem polling), com
 * cancelamento de requisições obsoletas e estado associado à identidade da
 * consulta: dados de outra filial/consulta nunca são expostos, nem por um
 * único render; o último snapshot da MESMA consulta é preservado quando uma
 * atualização falha. */
export function useDowntimesData(query: DowntimesQuery) {
  const [snapshot, setSnapshot] = useState<DowntimesSnapshot | null>(null);
  const controller = useRef<AbortController | null>(null);
  const queryKey = JSON.stringify(query);

  const refresh = useCallback(async () => {
    const key = queryKey;
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    setSnapshot((prev) => ({
      key,
      data: prev?.key === key ? prev.data : null,
      error: null,
      refreshing: prev?.key === key && prev.data !== null,
    }));
    try {
      const response = await getDowntimes(JSON.parse(key), next.signal);
      if (!next.signal.aborted) {
        setSnapshot({ key, data: response, error: null, refreshing: false });
      }
    } catch (reason) {
      if (!next.signal.aborted) {
        setSnapshot((prev) => ({
          key,
          data: prev?.key === key ? prev.data : null,
          error: reason instanceof Error ? reason.message : "Falha ao consultar as paradas.",
          refreshing: false,
        }));
      }
    }
  }, [queryKey]);

  useEffect(() => {
    void refresh();
    return () => controller.current?.abort();
  }, [refresh]);

  const matches = snapshot !== null && snapshot.key === queryKey;
  return {
    data: matches ? snapshot.data : null,
    error: matches ? snapshot.error : null,
    loading: !matches || (snapshot.data === null && snapshot.error === null),
    refreshing: matches && snapshot.refreshing,
    refresh,
  };
}
