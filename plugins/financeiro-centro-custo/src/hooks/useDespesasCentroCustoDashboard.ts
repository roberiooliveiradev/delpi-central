import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchDespesasFiltros,
  fetchDespesasRankingCentros,
  fetchDespesasRankingFornecedores,
  fetchDespesasResumo,
  fetchDespesasSerie,
} from "../api/despesasCentroCustoApi";
import type {
  DespesasFiltrosData,
  DespesasQueryFilters,
  DespesasRankingCentrosData,
  DespesasRankingFornecedoresData,
  DespesasResumoData,
  DespesasSerieData,
} from "../types/despesasCentroCusto";
import { DEFAULT_RANKING_LIMIT as rankingLimit } from "../types/despesasCentroCusto";

export type DashboardLoadState = "idle" | "loading" | "success" | "error";

export type DespesasDashboardData = {
  filtros: DespesasFiltrosData | null;
  resumo: DespesasResumoData | null;
  serie: DespesasSerieData | null;
  rankingCentros: DespesasRankingCentrosData | null;
  rankingFornecedores: DespesasRankingFornecedoresData | null;
};

const emptyDashboard: DespesasDashboardData = {
  filtros: null,
  resumo: null,
  serie: null,
  rankingCentros: null,
  rankingFornecedores: null,
};

function hasRequiredPeriod(filters: DespesasQueryFilters | null): filters is DespesasQueryFilters {
  return Boolean(filters?.startDate && filters?.endDate);
}

export function useDespesasCentroCustoDashboard(appliedFilters: DespesasQueryFilters | null) {
  const [state, setState] = useState<DashboardLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DespesasDashboardData>(emptyDashboard);
  const requestIdRef = useRef(0);

  const reload = useCallback(async () => {
    if (!hasRequiredPeriod(appliedFilters)) {
      setState("idle");
      setData(emptyDashboard);
      setError(null);
      return;
    }

    const requestId = ++requestIdRef.current;
    setState("loading");
    setError(null);

    try {
      const filtros = await fetchDespesasFiltros(appliedFilters);

      if (requestId !== requestIdRef.current) return;

      const rankingCentrosPromise = appliedFilters.costCenter
        ? Promise.resolve(null)
        : fetchDespesasRankingCentros(appliedFilters, rankingLimit);

      const [resumo, serie, rankingCentros, rankingFornecedores] = await Promise.all([
        fetchDespesasResumo(appliedFilters),
        fetchDespesasSerie(appliedFilters),
        rankingCentrosPromise,
        fetchDespesasRankingFornecedores(appliedFilters, rankingLimit),
      ]);

      if (requestId !== requestIdRef.current) return;

      setData({
        filtros,
        resumo,
        serie,
        rankingCentros,
        rankingFornecedores,
      });
      setState("success");
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      setState("error");
      setError(err instanceof Error ? err.message : "Falha ao carregar o painel.");
      setData(emptyDashboard);
    }
  }, [appliedFilters]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    state,
    error,
    data,
    reload,
    isLoading: state === "loading",
  };
}
