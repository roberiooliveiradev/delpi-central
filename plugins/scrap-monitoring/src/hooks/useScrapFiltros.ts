import { useCallback, useEffect, useState } from "react";

import { fetchScrapFiltros } from "../api/refugosApi";
import type { ScrapFiltrosData, ScrapQueryFilters } from "../types/scrap";

const emptyFiltros: ScrapFiltrosData = {
  materiasPrimas: [],
  produtosAcabados: [],
  ordensProducao: [],
  motivos: [],
};

function hasPeriod(
  filters: ScrapQueryFilters | null,
): filters is ScrapQueryFilters {
  return Boolean(filters?.filial && filters.start_date && filters.end_date);
}

export function useScrapFiltros(appliedFilters: ScrapQueryFilters | null) {
  const [data, setData] = useState<ScrapFiltrosData>(emptyFiltros);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((current) => current + 1);
  }, []);

  useEffect(() => {
    if (!hasPeriod(appliedFilters)) {
      setData(emptyFiltros);
      setError(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const period = {
      filial: appliedFilters.filial,
      start_date: appliedFilters.start_date,
      end_date: appliedFilters.end_date,
    };

    async function run() {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchScrapFiltros(period, {
          signal: controller.signal,
        });
        setData({
          materiasPrimas: result.materiasPrimas ?? [],
          produtosAcabados: result.produtosAcabados ?? [],
          ordensProducao: result.ordensProducao ?? [],
          motivos: result.motivos ?? [],
        });
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof Error ? err.message : "Falha ao carregar filtros.",
        );
        setData(emptyFiltros);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [
    appliedFilters?.filial,
    appliedFilters?.start_date,
    appliedFilters?.end_date,
    reloadKey,
  ]);

  return { data, loading, error, reload };
}
