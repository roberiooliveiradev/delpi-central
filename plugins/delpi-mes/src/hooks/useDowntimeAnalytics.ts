import { useCallback, useEffect, useRef, useState } from "react";

import { getDowntimeAnalytics } from "../api/mesApi";
import type { DowntimeAnalyticsQuery, DowntimeAnalyticsResponse } from "../types/mes";

type AnalyticsSnapshot = {
  key: string;
  data: DowntimeAnalyticsResponse | null;
  error: string | null;
  refreshing: boolean;
};

/** Agregações gerenciais de paradas (Etapa 2) — estado associado à
 * identidade da consulta: indicadores de outra filial/consulta nunca são
 * expostos, nem por um único render; requisições obsoletas são canceladas
 * e respostas atrasadas descartadas. O último snapshot da MESMA consulta é
 * preservado quando uma atualização falha. Quando a consulta é nula (período
 * sem início definido), nenhuma requisição é emitida. */
export function useDowntimeAnalytics(query: DowntimeAnalyticsQuery | null) {
  const [snapshot, setSnapshot] = useState<AnalyticsSnapshot | null>(null);
  const controller = useRef<AbortController | null>(null);
  const queryKey = query === null ? null : JSON.stringify(query);

  const refresh = useCallback(async () => {
    const key = queryKey;
    controller.current?.abort();
    if (key === null) {
      setSnapshot(null);
      return;
    }
    const next = new AbortController();
    controller.current = next;
    setSnapshot((prev) => ({
      key,
      data: prev?.key === key ? prev.data : null,
      error: null,
      refreshing: prev?.key === key && prev.data !== null,
    }));
    try {
      const response = await getDowntimeAnalytics(JSON.parse(key), next.signal);
      if (!next.signal.aborted) {
        setSnapshot({ key, data: response, error: null, refreshing: false });
      }
    } catch (reason) {
      if (!next.signal.aborted) {
        setSnapshot((prev) => ({
          key,
          data: prev?.key === key ? prev.data : null,
          error:
            reason instanceof Error
              ? reason.message
              : "Falha ao consultar os indicadores de paradas.",
          refreshing: false,
        }));
      }
    }
  }, [queryKey]);

  useEffect(() => {
    void refresh();
    return () => controller.current?.abort();
  }, [refresh]);

  const matches = queryKey !== null && snapshot !== null && snapshot.key === queryKey;
  return {
    data: matches ? snapshot.data : null,
    error: matches ? snapshot.error : null,
    loading: queryKey !== null && (!matches || (snapshot.data === null && snapshot.error === null)),
    refreshing: matches && snapshot.refreshing,
    refresh,
  };
}
