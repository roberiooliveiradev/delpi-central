import { useCallback, useEffect, useState } from "react";

import { fetchStockBalancesReport } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { PpcBranch, StockBalancesReportPayload } from "../types";

export type StockBalancesFilters = {
  search: string;
  page: number;
  pageSize: number;
  sort: string;
};

export const STOCK_BALANCES_DEFAULT_FILTERS: StockBalancesFilters = {
  search: "",
  page: 1,
  pageSize: 50,
  sort: "product_code_asc",
};

/**
 * Relatório de saldos — BFF mantém snapshot em cache (TTL);
 * página/busca/sort são baratos. `refreshing` mantém a tabela na tela.
 */
export function useStockBalancesReport(branch: PpcBranch, filters: StockBalancesFilters) {
  const [data, setData] = useState<StockBalancesReportPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchStockBalancesReport({
      branch,
      search: filters.search,
      sort: filters.sort,
      page: filters.page,
      pageSize: filters.pageSize,
      refresh: reloadToken > 0,
      signal: controller.signal,
    })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.reports.loadError);
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, filters.page, filters.pageSize, filters.search, filters.sort, reloadToken]);

  return {
    data,
    loading: loading && data === null,
    refreshing: loading && data !== null,
    error,
    reload,
  };
}
