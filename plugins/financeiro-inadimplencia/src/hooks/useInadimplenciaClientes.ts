import { useCallback, useEffect, useRef, useState } from "react";
import { fetchInadimplenciaClientes } from "../api/inadimplenciaApi";
import type {
  ClientesSortBy,
  InadimplenciaClientesData,
  PeriodFilter,
  SortDirection,
} from "../types/inadimplencia";
import { DEFAULT_PAGE_SIZE } from "../types/inadimplencia";

export type ClientesLoadState = "idle" | "loading" | "success" | "error";

export type ClientesTableState = {
  page: number;
  pageSize: number;
  search: string;
  sortBy: ClientesSortBy;
  sortDir: SortDirection;
  onlyWithDelays: boolean;
};

export const defaultClientesTableState: ClientesTableState = {
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  search: "",
  sortBy: "late_amount",
  sortDir: "desc",
  onlyWithDelays: true,
};

export function useInadimplenciaClientes(
  period: PeriodFilter,
  tableState: ClientesTableState,
) {
  const [state, setState] = useState<ClientesLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<InadimplenciaClientesData | null>(null);
  const requestIdRef = useRef(0);

  const reload = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setState("loading");
    setError(null);

    try {
      const response = await fetchInadimplenciaClientes({
        ...period,
        page: tableState.page,
        pageSize: tableState.pageSize,
        sortBy: tableState.sortBy,
        sortDir: tableState.sortDir,
        q: tableState.search,
        onlyWithDelays: tableState.onlyWithDelays,
      });

      if (requestId !== requestIdRef.current) return;

      setData(response);
      setState("success");
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      setState("error");
      setError(err instanceof Error ? err.message : "Falha ao carregar clientes.");
      setData(null);
    }
  }, [period, tableState]);

  useEffect(() => {
    queueMicrotask(() => {
      void reload();
    });
  }, [reload]);

  return {
    state,
    error,
    data,
    reload,
    isLoading: state === "loading",
  };
}
