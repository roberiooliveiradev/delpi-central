import { useCallback, useEffect, useRef, useState } from "react";
import { getRunPerformance } from "../api/mesApi";
import type { RunPerformanceResponse } from "../types/mes";

/**
 * Performance detalhada de um run específico — um fetch por run selecionado.
 *  (ex.: referenceAt do monitoring) provoca refetch silencioso
 * mantendo o último valor visível; erros ficam localizados na seção.
 */
export function useRunPerformance(runId: string | null, refreshKey?: string | null) {
  const [data, setData] = useState<RunPerformanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [nonce, setNonce] = useState(0);
  const loadedRun = useRef<string | null>(null);

  useEffect(() => {
    if (!runId) {
      loadedRun.current = null;
      queueMicrotask(() => { setData(null); setError(null); setLoading(false); });
      return;
    }
    // Refetch só quando o run muda ou quando o refreshKey avança (poll do
    // monitoring). Nunca dispara um ciclo próprio.
    const controller = new AbortController();
    let stale = false;
    const firstLoad = loadedRun.current !== runId;
    if (firstLoad) setLoading(true);
    getRunPerformance(runId, controller.signal)
      .then((response) => {
        if (stale) return;
        loadedRun.current = runId;
        setData(response);
        setError(null);
      })
      .catch((reason) => {
        if (stale || controller.signal.aborted) return;
        setError(reason instanceof Error ? reason.message : "Falha ao carregar a Performance.");
      })
      .finally(() => { if (!stale) setLoading(false); });
    return () => { stale = true; controller.abort(); };
  }, [runId, refreshKey, nonce]);

  const retry = useCallback(() => setNonce((value) => value + 1), []);
  return { data, error, loading, retry };
}
