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

export function useRetrabalhoDashboard(appliedFilters: RetrabalhoQueryFilters | null) {
  const [state, setState] = useState<DashboardLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RetrabalhoDashboardData>(emptyDashboard);
  const requestIdRef = useRef(0);

  const reload = useCallback(async () => {
    if (!hasRequiredFilters(appliedFilters)) {
      setState("idle");
      setData(emptyDashboard);
      setError(null);
      return;
    }

    const requestId = ++requestIdRef.current;
    setState("loading");
    setError(null);

    try {
      const [resumo, mensal, recursos, colaboradores] = await Promise.all([
        fetchRetrabalhoResumo(appliedFilters),
        fetchRetrabalhoMensal(appliedFilters),
        fetchRetrabalhoRecursos(appliedFilters, DEFAULT_RANKING_LIMIT),
        fetchRetrabalhoColaboradores(appliedFilters, DEFAULT_RANKING_LIMIT),
      ]);

      if (requestId !== requestIdRef.current) return;

      setData({
        resumo,
        mensal: mensal.items ?? [],
        recursos: recursos.items ?? [],
        colaboradores: colaboradores.items ?? [],
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

  return { state, error, data, reload, isLoading: state === "loading" };
}
