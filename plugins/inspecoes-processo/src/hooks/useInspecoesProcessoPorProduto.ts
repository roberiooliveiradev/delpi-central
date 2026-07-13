import { useCallback, useEffect, useState } from "react";

import { getPorProduto } from "../api/inspecoesProcessoApi";
import type { InspecoesProcessoPorProdutoItem } from "../types/api";

export const POR_PRODUTO_LIMIT = 10;

type UseInspecoesProcessoPorProdutoResult = {
  items: InspecoesProcessoPorProdutoItem[];
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useInspecoesProcessoPorProduto(
  branch: string,
  refreshToken = 0,
): UseInspecoesProcessoPorProdutoResult {
  const [items, setItems] = useState<InspecoesProcessoPorProdutoItem[]>([]);
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
        const ranking = await getPorProduto(branch, POR_PRODUTO_LIMIT, controller.signal);
        if (controller.signal.aborted) return;
        setItems(Array.isArray(ranking) ? ranking.slice(0, POR_PRODUTO_LIMIT) : []);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setItems([]);
        setError(
          err instanceof Error ? err.message : "Erro ao carregar o ranking por produto.",
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
