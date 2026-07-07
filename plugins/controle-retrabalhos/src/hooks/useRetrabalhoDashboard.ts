import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchRetrabalhoColaboradores,
  fetchRetrabalhoMensal,
  fetchRetrabalhoRecursos,
  fetchRetrabalhoResumo,
} from "../api/retrabalhoApi";
import type {
  RetrabalhoColaboradorItem,
  RetrabalhoMensalItem,
  RetrabalhoQueryFilters,
  RetrabalhoResumo,
  RetrabalhoRecursoItem,
} from "../types/retrabalho";
import { DEFAULT_RANKING_LIMIT } from "../types/retrabalho";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

export type DashboardLoadState = "idle" | "loading" | "success" | "error";

export type RetrabalhoDashboardData = {
  resumo: RetrabalhoResumo | null;
  mensal: RetrabalhoMensalItem[];
  recursos: RetrabalhoRecursoItem[];
  colaboradores: RetrabalhoColaboradorItem[];
};

const emptyDashboard: RetrabalhoDashboardData = {
  resumo: null,
  mensal: [],
  recursos: [],
  colaboradores: [],
};

function hasRequiredFilters(
  filters: RetrabalhoQueryFilters | null,
): filters is RetrabalhoQueryFilters {
  return Boolean(filters?.filial && filters.dataInicio && filters.dataFim);
}

function firstRejectedReason(
  results: Array<PromiseSettledResult<unknown>>,
): unknown {
  for (const result of results) {
    if (result.status === "rejected") {
      return result.reason;
    }
  }
  return null;
}

export function useRetrabalhoDashboard(appliedFilters: RetrabalhoQueryFilters | null) {
  const [state, setState] = useState<DashboardLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RetrabalhoDashboardData>(emptyDashboard);
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
            (signal) => fetchRetrabalhoResumo(filters, { signal }),
            (signal) => fetchRetrabalhoMensal(filters, { signal }),
            (signal) =>
              fetchRetrabalhoRecursos(filters, DEFAULT_RANKING_LIMIT, { signal }),
            (signal) =>
              fetchRetrabalhoColaboradores(filters, DEFAULT_RANKING_LIMIT, {
                signal,
              }),
          ] as ReadonlyArray<(signal: AbortSignal) => Promise<unknown>>,
          controller.signal,
          setRequestProgress,
        );

        if (controller.signal.aborted) return;

        const rejectedReason = firstRejectedReason(results);
        if (rejectedReason) {
          throw rejectedReason;
        }

        const [resumoResult, mensalResult, recursosResult, colaboradoresResult] =
          results;

        if (
          resumoResult.status !== "fulfilled" ||
          mensalResult.status !== "fulfilled" ||
          recursosResult.status !== "fulfilled" ||
          colaboradoresResult.status !== "fulfilled"
        ) {
          throw new Error("Falha ao carregar o painel.");
        }

        setData({
          resumo: resumoResult.value as RetrabalhoResumo,
          mensal: (mensalResult.value as { items?: RetrabalhoMensalItem[] }).items ?? [],
          recursos: (recursosResult.value as { items?: RetrabalhoRecursoItem[] }).items ?? [],
          colaboradores:
            (colaboradoresResult.value as { items?: RetrabalhoColaboradorItem[] }).items ??
            [],
        });
        setState("success");
      } catch (err) {
        if (controller.signal.aborted) return;
        setState("error");
        setError(err instanceof Error ? err.message : "Falha ao carregar o painel.");
        if (!hasPreviousData) {
          setData(emptyDashboard);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();

    return () => {
      controller.abort();
    };
  }, [appliedFilters, reloadKey]);

  return {
    state,
    error,
    data,
    reload,
    loading,
    refreshing,
    requestProgress,
    isLoading: loading || refreshing,
  };
}
