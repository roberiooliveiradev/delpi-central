import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchInadimplenciaClientes,
  fetchInadimplenciaFaixas,
  fetchInadimplenciaMensal,
  fetchInadimplenciaResumo,
} from "../api/inadimplenciaApi";
import type {
  InadimplenciaClienteItem,
  InadimplenciaFaixasData,
  InadimplenciaMensalData,
  InadimplenciaResumoData,
  PeriodFilter,
} from "../types/inadimplencia";
import { getCurrentMonthRange } from "../utils/period";

export type DashboardLoadState = "idle" | "loading" | "success" | "error";

export type InadimplenciaDashboardData = {
  resumo: InadimplenciaResumoData | null;
  mensal: InadimplenciaMensalData | null;
  faixas: InadimplenciaFaixasData | null;
  topClienteMes: InadimplenciaClienteItem | null;
};

const emptyDashboard: InadimplenciaDashboardData = {
  resumo: null,
  mensal: null,
  faixas: null,
  topClienteMes: null,
};

export function useInadimplenciaDashboard(period: PeriodFilter) {
  const [state, setState] = useState<DashboardLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<InadimplenciaDashboardData>(emptyDashboard);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const requestIdRef = useRef(0);

  const reload = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setState("loading");
    setError(null);

    try {
      const currentMonth = getCurrentMonthRange();
      const [resumo, mensal, faixas, topClientes] = await Promise.all([
        fetchInadimplenciaResumo(period),
        fetchInadimplenciaMensal(period),
        fetchInadimplenciaFaixas(period),
        fetchInadimplenciaClientes({
          startDate: currentMonth.startDate,
          endDate: currentMonth.endDate,
          page: 1,
          pageSize: 1,
          sortBy: "late_amount",
          sortDir: "desc",
          onlyWithDelays: true,
        }),
      ]);

      if (requestId !== requestIdRef.current) return;

      setData({
        resumo,
        mensal,
        faixas,
        topClienteMes: topClientes.items[0] ?? null,
      });
      setUpdatedAt(new Date());
      setState("success");
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      setState("error");
      setError(err instanceof Error ? err.message : "Falha ao carregar o painel.");
      setData(emptyDashboard);
    }
  }, [period]);

  useEffect(() => {
    queueMicrotask(() => {
      void reload();
    });
  }, [reload]);

  return {
    state,
    error,
    data,
    updatedAt,
    reload,
    isLoading: state === "loading",
  };
}
