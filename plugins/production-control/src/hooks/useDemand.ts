import { useCallback, useEffect, useState } from "react";

import { fetchDemand } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { DemandPayload, PpcBranch } from "../types";

export type DemandFilters = {
  search: string;
  status: string;
  dueFrom: string;
  dueTo: string;
  page: number;
  pageSize: number;
  sort: string;
  direction: "asc" | "desc";
};

export const DEMAND_DEFAULT_FILTERS: DemandFilters = {
  search: "",
  status: "",
  dueFrom: "",
  dueTo: "",
  page: 1,
  pageSize: 50,
  sort: "due_date",
  direction: "asc",
};

/**
 * Carteira a entregar da filial.
 *
 * Filtro, ordenação e página são resolvidos no BFF (que mantém o dump em cache),
 * então cada mudança é uma consulta barata. `refreshing` segura os dados na tela
 * enquanto a nova página chega.
 */
export function useDemand(branch: PpcBranch, filters: DemandFilters) {
  const [data, setData] = useState<DemandPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchDemand({
      branch,
      search: filters.search,
      status: filters.status,
      dueFrom: filters.dueFrom || null,
      dueTo: filters.dueTo || null,
      sort: filters.sort,
      direction: filters.direction,
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
        setError(err instanceof Error ? err.message : copy.demand.loadError);
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    branch,
    filters.direction,
    filters.dueFrom,
    filters.dueTo,
    filters.page,
    filters.pageSize,
    filters.search,
    filters.sort,
    filters.status,
    reloadToken,
  ]);

  return {
    data,
    loading: loading && data === null,
    refreshing: loading && data !== null,
    error,
    reload,
  };
}
