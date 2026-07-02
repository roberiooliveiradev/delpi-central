import { useCallback, useEffect, useRef, useState } from "react";
import { fetchDespesasLancamentos } from "../api/despesasCentroCustoApi";
import type {
  DespesasLancamentosData,
  DespesasQueryFilters,
  LancamentosSortBy,
  SortDirection,
} from "../types/despesasCentroCusto";
import { DEFAULT_LANCAMENTOS_PAGE_SIZE as defaultPageSize } from "../types/despesasCentroCusto";

export type LancamentosLoadState = "idle" | "loading" | "success" | "error";

export type LancamentosTableState = {
  page: number;
  pageSize: number;
  search: string;
  sortBy: LancamentosSortBy;
  sortDir: SortDirection;
};

export const defaultLancamentosTableState: LancamentosTableState = {
  page: 1,
  pageSize: defaultPageSize,
  search: "",
  sortBy: "data_emissao",
  sortDir: "desc",
};

function hasRequiredPeriod(filters: DespesasQueryFilters | null): filters is DespesasQueryFilters {
  return Boolean(filters?.startDate && filters?.endDate);
}

export function useLancamentosCentroCusto(
  appliedFilters: DespesasQueryFilters | null,
  tableState: LancamentosTableState,
) {
  const [state, setState] = useState<LancamentosLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DespesasLancamentosData | null>(null);
  const requestIdRef = useRef(0);

  const reload = useCallback(async () => {
    if (!hasRequiredPeriod(appliedFilters)) {
      setState("idle");
      setData(null);
      setError(null);
      return;
    }

    const requestId = ++requestIdRef.current;
    setState("loading");
    setError(null);

    try {
      const response = await fetchDespesasLancamentos({
        ...appliedFilters,
        page: tableState.page,
        pageSize: tableState.pageSize,
        search: tableState.search,
        sortBy: tableState.sortBy,
        sortDir: tableState.sortDir,
      });

      if (requestId !== requestIdRef.current) return;

      setData(response);
      setState("success");
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      setState("error");
      setError(err instanceof Error ? err.message : "Falha ao carregar lançamentos.");
      setData(null);
    }
  }, [appliedFilters, tableState]);

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
