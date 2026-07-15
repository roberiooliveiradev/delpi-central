import { useCallback, useEffect, useState } from "react";

import { fetchScrapRegistros } from "../api/refugosApi";
import type { ScrapQueryFilters, ScrapRegistrosData } from "../types/scrap";

const DEFAULT_PAGE_SIZE = 25;

export function useScrapRegistros(
  appliedFilters: ScrapQueryFilters | null,
  page: number,
  pageSize = DEFAULT_PAGE_SIZE,
) {
  const [data, setData] = useState<ScrapRegistrosData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((current) => current + 1);
  }, []);

  useEffect(() => {
    if (!appliedFilters?.filial || !appliedFilters.dataInicio || !appliedFilters.dataFim) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const filters = appliedFilters;

    async function run() {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchScrapRegistros(filters, page, pageSize, {
          signal: controller.signal,
        });
        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar registros.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void run();
    return () => controller.abort();
  }, [appliedFilters, page, pageSize, reloadKey]);

  return { data, loading, error, reload, pageSize };
}
