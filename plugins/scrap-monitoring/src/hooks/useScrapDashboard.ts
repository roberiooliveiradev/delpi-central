import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchScrapRankings,
  fetchScrapResumo,
  fetchScrapSerie,
} from "../api/refugosApi";
import type {
  ScrapQueryFilters,
  ScrapRankingItem,
  ScrapResumo,
  ScrapSeriePoint,
} from "../types/scrap";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

export type DashboardLoadState = "idle" | "loading" | "success" | "error";

export type ScrapDashboardData = {
  resumo: ScrapResumo | null;
  motivos: ScrapRankingItem[];
  serie: ScrapSeriePoint[];
  serieGranularity: "day" | "month" | null;
  materiais: ScrapRankingItem[];
  produtos: ScrapRankingItem[];
  centros: ScrapRankingItem[];
  colaboradores: ScrapRankingItem[];
};

const emptyDashboard: ScrapDashboardData = {
  resumo: null,
  motivos: [],
  serie: [],
  serieGranularity: null,
  materiais: [],
  produtos: [],
  centros: [],
  colaboradores: [],
};

function hasRequiredFilters(
  filters: ScrapQueryFilters | null,
): filters is ScrapQueryFilters {
  return Boolean(filters?.filial && filters.start_date && filters.end_date);
}

export function useScrapDashboard(appliedFilters: ScrapQueryFilters | null) {
  const [state, setState] = useState<DashboardLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ScrapDashboardData>(emptyDashboard);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS,
  );
  const [reloadKey, setReloadKey] = useState(0);
  const dataRef = useRef(data);
  dataRef.current = data;

  const reload = useCallback(() => {
    setReloadKey((current) => current + 1);
  }, []);

  useEffect(() => {
    if (!hasRequiredFilters(appliedFilters)) {
      setState("idle");
      setData(emptyDashboard);
      setError(null);
      setLoading(false);
      setRefreshing(false);
      setRequestProgress(EMPTY_REQUEST_PROGRESS);
      return;
    }

    const controller = new AbortController();
    const filters = appliedFilters;
    const hasPreviousData = dataRef.current.resumo !== null;

    async function run() {
      try {
        setError(null);
        setRequestProgress(EMPTY_REQUEST_PROGRESS);

        if (hasPreviousData) {
          setRefreshing(true);
        } else {
          setLoading(true);
          setState("loading");
        }

        const results = await runParallelWithProgress(
          [
            (signal) => fetchScrapResumo(filters, { signal }),
            (signal) => fetchScrapRankings(filters, "motivo", 10, { signal }),
            (signal) => fetchScrapSerie(filters, "auto", { signal }),
            (signal) =>
              fetchScrapRankings(filters, "materia_prima", 10, { signal }),
            (signal) =>
              fetchScrapRankings(filters, "produto_acabado", 10, { signal }),
            (signal) =>
              fetchScrapRankings(filters, "centro_trabalho", 10, { signal }),
            (signal) =>
              fetchScrapRankings(filters, "colaborador", 10, { signal }),
          ],
          controller.signal,
          setRequestProgress,
        );

        const rejected = results.find((result) => result.status === "rejected");
        if (rejected && rejected.status === "rejected") {
          throw rejected.reason;
        }

        const values = results.map((result) =>
          result.status === "fulfilled" ? result.value : null,
        );

        const seriePayload = values[2] as {
          points: ScrapSeriePoint[];
          granularity: "day" | "month";
        } | null;

        setData({
          resumo: values[0] as ScrapResumo,
          motivos: ((values[1] as { items: ScrapRankingItem[] })?.items) ?? [],
          serie: seriePayload?.points ?? [],
          serieGranularity: seriePayload?.granularity ?? null,
          materiais: ((values[3] as { items: ScrapRankingItem[] })?.items) ?? [],
          produtos: ((values[4] as { items: ScrapRankingItem[] })?.items) ?? [],
          centros: ((values[5] as { items: ScrapRankingItem[] })?.items) ?? [],
          colaboradores:
            ((values[6] as { items: ScrapRankingItem[] })?.items) ?? [],
        });
        setState("success");
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Falha ao carregar o painel.";
        setError(message);
        setState("error");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [appliedFilters, reloadKey]);

  return {
    state,
    error,
    data,
    loading,
    refreshing,
    requestProgress,
    reload,
  };
}
