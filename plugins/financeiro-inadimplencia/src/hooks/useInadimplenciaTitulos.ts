import { useCallback, useEffect, useRef, useState } from "react";
import { fetchInadimplenciaTitulos } from "../api/inadimplenciaApi";
import type {
  InadimplenciaTitulosData,
  PeriodFilter,
  SortDirection,
  TituloStatus,
  TitulosSortBy,
} from "../types/inadimplencia";
import { DEFAULT_PAGE_SIZE } from "../types/inadimplencia";

export type TitulosLoadState = "idle" | "loading" | "success" | "error";

export type TitulosTableState = {
  page: number;
  pageSize: number;
  search: string;
  sortBy: TitulosSortBy;
  sortDir: SortDirection;
  status: TituloStatus;
  delayRange: string;
};

export const defaultTitulosTableState: TitulosTableState = {
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  search: "",
  sortBy: "payment_date",
  sortDir: "desc",
  status: "late",
  delayRange: "",
};

export function useInadimplenciaTitulos(
  period: PeriodFilter,
  customerCode: string | null,
  storeCode: string | null,
  tableState: TitulosTableState,
  enabled: boolean,
) {
  const [state, setState] = useState<TitulosLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<InadimplenciaTitulosData | null>(null);
  const requestIdRef = useRef(0);

  const reload = useCallback(async () => {
    if (!enabled || !customerCode) {
      setState("idle");
      setData(null);
      setError(null);
      return;
    }

    const requestId = ++requestIdRef.current;
    setState("loading");
    setError(null);

    try {
      const response = await fetchInadimplenciaTitulos({
        ...period,
        customerCode,
        storeCode: storeCode ?? undefined,
        status: tableState.status,
        delayRange: tableState.delayRange || undefined,
        q: tableState.search,
        page: tableState.page,
        pageSize: tableState.pageSize,
        sortBy: tableState.sortBy,
        sortDir: tableState.sortDir,
      });

      if (requestId !== requestIdRef.current) return;

      setData(response);
      setState("success");
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      setState("error");
      setError(err instanceof Error ? err.message : "Falha ao carregar títulos.");
      setData(null);
    }
  }, [period, customerCode, storeCode, tableState, enabled]);

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
