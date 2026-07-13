import { useCallback, useEffect, useState } from "react";

import { getResumo } from "../api/inspecoesProcessoApi";
import type { InspecoesProcessoResumo } from "../types/api";

type UseInspecoesProcessoResumoResult = {
  data: InspecoesProcessoResumo | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useInspecoesProcessoResumo(
  branch: string,
  refreshToken = 0,
): UseInspecoesProcessoResumoResult {
  const [data, setData] = useState<InspecoesProcessoResumo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      setLoading(true);
      setError(null);
      setData(null);

      try {
        const resumo = await getResumo(branch, controller.signal);
        if (controller.signal.aborted) return;
        setData(resumo);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Erro ao carregar o resumo.");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();

    return () => {
      controller.abort();
    };
  }, [branch, reloadKey, refreshToken]);

  return { data, loading, error, reload };
}
