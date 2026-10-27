import { useCallback, useEffect, useRef, useState } from "react";

type Snapshot<T> = {
  key: string;
  data: T | null;
  error: string | null;
  refreshing: boolean;
};

/** Estado associado à identidade da consulta: dados de outra
 * filial/consulta nunca são expostos, nem por um único render;
 * requisições obsoletas são canceladas e respostas atrasadas
 * descartadas. O último snapshot da MESMA consulta é preservado quando
 * uma atualização falha. Quando a consulta é nula, nenhuma requisição é
 * emitida. Mecanismo compartilhado pelas consultas de paradas
 * (analytics e insights). */
export function useDowntimeQuerySnapshot<T>(
  query: { [key: string]: unknown } | null,
  fetcher: (query: never, signal: AbortSignal) => Promise<T>,
  errorFallback: string,
) {
  const [snapshot, setSnapshot] = useState<Snapshot<T> | null>(null);
  const controller = useRef<AbortController | null>(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
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
      const response = await fetcherRef.current(
        JSON.parse(key) as never,
        next.signal,
      );
      if (!next.signal.aborted) {
        setSnapshot({ key, data: response, error: null, refreshing: false });
      }
    } catch (reason) {
      if (!next.signal.aborted) {
        setSnapshot((prev) => ({
          key,
          data: prev?.key === key ? prev.data : null,
          error: reason instanceof Error ? reason.message : errorFallback,
          refreshing: false,
        }));
      }
    }
  }, [queryKey, errorFallback]);

  useEffect(() => {
    void refresh();
    return () => controller.current?.abort();
  }, [refresh]);

  const matches = queryKey !== null && snapshot !== null && snapshot.key === queryKey;
  return {
    data: matches ? snapshot.data : null,
    error: matches ? snapshot.error : null,
    loading:
      queryKey !== null &&
      (!matches || (snapshot.data === null && snapshot.error === null)),
    refreshing: matches && snapshot.refreshing,
    refresh,
  };
}
