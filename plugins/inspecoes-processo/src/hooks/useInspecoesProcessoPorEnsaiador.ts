import { useCallback, useEffect, useState } from "react";

import { getPorEnsaiador } from "../api/inspecoesProcessoApi";
import type { InspecoesProcessoPorEnsaiadorItem } from "../types/api";

export const POR_ENSAIADOR_LIMIT = 10;

type UseInspecoesProcessoPorEnsaiadorResult = {
  items: InspecoesProcessoPorEnsaiadorItem[];
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useInspecoesProcessoPorEnsaiador(
  branch: string,
  refreshToken = 0,
): UseInspecoesProcessoPorEnsaiadorResult {
  const [items, setItems] = useState<InspecoesProcessoPorEnsaiadorItem[]>([]);
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
      setItems([]);

      try {
        const ranking = await getPorEnsaiador(
          branch,
          POR_ENSAIADOR_LIMIT,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        setItems(Array.isArray(ranking) ? ranking.slice(0, POR_ENSAIADOR_LIMIT) : []);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setItems([]);
        setError(
          err instanceof Error
            ? err.message
            : "Erro ao carregar os indicadores por ensaiador.",
        );
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

  return { items, loading, error, reload };
}
