import { useCallback, useEffect, useState } from "react";

import { fetchInspecoesEntradaHistorico } from "../api/inspecoesEntradaApi";
import type {
  HistoricoFilters,
  InspecoesEntradaHistoricoData,
} from "../types/inspecoesEntradaHistorico";
import {
  EMPTY_HISTORICO_FILTERS,
  filtersToFetchParams,
  hasActiveHistoricoFilters,
} from "../utils/historicoFilters";
import type { BranchCode } from "../constants/branch";
import { useDebouncedValue } from "./useDebouncedValue";

const DEFAULT_PAGE_SIZE = 20;
const PAGE_SIZE_OPTIONS = [20, 50, 100] as const;
const FILTER_DEBOUNCE_MS = 400;

type UseInspecoesEntradaHistoricoResult = {
  branch: string;
  setBranch: (branch: string) => void;
  filters: HistoricoFilters;
  updateFilters: (patch: Partial<HistoricoFilters>) => void;
  clearFilters: () => void;
  hasActiveFilters: boolean;
  page: number;
  pageSize: number;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  pageSizeOptions: readonly number[];
  data: InspecoesEntradaHistoricoData | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useInspecoesEntradaHistorico(
  routeBranch?: string | null,
  refreshToken = 0,
): UseInspecoesEntradaHistoricoResult {
  const resolvedRouteBranch =
    routeBranch === "01" || routeBranch === "02" ? routeBranch : null;
  const [branchOverride, setBranchOverride] = useState<BranchCode>("01");
  const branch: BranchCode = resolvedRouteBranch ?? branchOverride;
  const [filters, setFilters] = useState<HistoricoFilters>(EMPTY_HISTORICO_FILTERS);
  const debouncedFilters = useDebouncedValue(filters, FILTER_DEBOUNCE_MS);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSizeState] = useState(DEFAULT_PAGE_SIZE);
  const [data, setData] = useState<InspecoesEntradaHistoricoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  const updateFilters = useCallback((patch: Partial<HistoricoFilters>) => {
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1);
  }, []);

  const clearFilters = useCallback(() => {
    setFilters(EMPTY_HISTORICO_FILTERS);
    setPage(1);
  }, []);

  const setBranch = useCallback(
    (nextBranch: string) => {
      if (resolvedRouteBranch) return;
      if (nextBranch === "01" || nextBranch === "02") {
        setBranchOverride(nextBranch);
        setPage(1);
      }
    },
    [resolvedRouteBranch],
  );

  const setPageSize = useCallback((nextPageSize: number) => {
    setPageSizeState(nextPageSize);
    setPage(1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      try {
        setLoading(true);
        setError(null);

        const result = await fetchInspecoesEntradaHistorico(
          filtersToFetchParams(branch, page, pageSize, debouncedFilters),
          controller.signal,
        );

        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error
            ? err.message
            : "Não foi possível carregar o histórico de inspeções.";
        setError(message);
        setData(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [branch, debouncedFilters, page, pageSize, reloadKey, refreshToken]);

  return {
    branch,
    setBranch,
    filters,
    updateFilters,
    clearFilters,
    hasActiveFilters: hasActiveHistoricoFilters(filters),
    page,
    pageSize,
    setPage,
    setPageSize,
    pageSizeOptions: PAGE_SIZE_OPTIONS,
    data,
    loading,
    error,
    reload,
  };
}
