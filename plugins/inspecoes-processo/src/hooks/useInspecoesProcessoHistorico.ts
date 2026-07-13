import { useCallback, useEffect, useRef, useState } from "react";

import { getHistorico } from "../api/inspecoesProcessoApi";
import type {
  InspecoesProcessoHistoricoItem,
  InspecoesProcessoHistoricoResponse,
} from "../types/api";

export const HISTORICO_DEFAULT_PAGE_SIZE = 25;
export const HISTORICO_MAX_PAGE_SIZE = 50;
export const HISTORICO_PAGE_SIZE_OPTIONS = [25, 50] as const;
/** Prefetch em background após a 1ª página (alívio de UX sem saturar o TOTVS). */
const HISTORICO_PREFETCH_MAX_PAGES = 8;

export type HistoricoFilters = {
  ordem_producao: string;
  codigo_produto: string;
};

export const EMPTY_HISTORICO_FILTERS: HistoricoFilters = {
  ordem_producao: "",
  codigo_produto: "",
};

type CachedPage = {
  items: InspecoesProcessoHistoricoItem[];
  hasNext: boolean;
};

function clampPageSize(value: number): number {
  if (!Number.isFinite(value) || value < 1) return HISTORICO_DEFAULT_PAGE_SIZE;
  return Math.min(Math.floor(value), HISTORICO_MAX_PAGE_SIZE);
}

function toQueryFilters(filters: HistoricoFilters) {
  return {
    ordem_producao: filters.ordem_producao.trim() || undefined,
    codigo_produto: filters.codigo_produto.trim() || undefined,
  };
}

type UseInspecoesProcessoHistoricoResult = {
  draftFilters: HistoricoFilters;
  updateDraftFilters: (patch: Partial<HistoricoFilters>) => void;
  clearFilters: () => void;
  search: () => void;
  page: number;
  pageSize: number;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  pageSizeOptions: readonly number[];
  items: InspecoesProcessoHistoricoItem[];
  hasNext: boolean;
  hasSearched: boolean;
  loading: boolean;
  prefetching: boolean;
  error: string | null;
  reload: () => void;
};

function applyCachedPage(
  cached: CachedPage | undefined,
  setters: {
    setItems: (items: InspecoesProcessoHistoricoItem[]) => void;
    setHasNext: (value: boolean) => void;
  },
): boolean {
  if (!cached) return false;
  setters.setItems(cached.items);
  setters.setHasNext(cached.hasNext);
  return true;
}

export function useInspecoesProcessoHistorico(
  branch: string,
  refreshToken = 0,
): UseInspecoesProcessoHistoricoResult {
  const [draftFilters, setDraftFilters] =
    useState<HistoricoFilters>(EMPTY_HISTORICO_FILTERS);
  const [appliedFilters, setAppliedFilters] =
    useState<HistoricoFilters>(EMPTY_HISTORICO_FILTERS);
  const [page, setPageState] = useState(1);
  const [pageSize, setPageSizeState] = useState(HISTORICO_DEFAULT_PAGE_SIZE);
  const [hasSearched, setHasSearched] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [items, setItems] = useState<InspecoesProcessoHistoricoItem[]>([]);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(false);
  const [prefetching, setPrefetching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pageCacheRef = useRef<Map<number, CachedPage>>(new Map());
  const prefetchGenerationRef = useRef(0);

  const updateDraftFilters = useCallback((patch: Partial<HistoricoFilters>) => {
    setDraftFilters((current) => ({ ...current, ...patch }));
  }, []);

  const clearFilters = useCallback(() => {
    prefetchGenerationRef.current += 1;
    pageCacheRef.current.clear();
    setDraftFilters(EMPTY_HISTORICO_FILTERS);
    setAppliedFilters(EMPTY_HISTORICO_FILTERS);
    setPageState(1);
    setHasSearched(false);
    setItems([]);
    setHasNext(false);
    setError(null);
    setLoading(false);
    setPrefetching(false);
  }, []);

  const search = useCallback(() => {
    const hasSelectiveFilter = Boolean(
      draftFilters.ordem_producao.trim() || draftFilters.codigo_produto.trim(),
    );
    if (!hasSelectiveFilter) {
      setError(
        "Informe ordem de produção ou código de produto para buscar o histórico.",
      );
      setHasSearched(false);
      setItems([]);
      setHasNext(false);
      return;
    }
    prefetchGenerationRef.current += 1;
    pageCacheRef.current.clear();
    setAppliedFilters(draftFilters);
    setPageState(1);
    setHasSearched(true);
    setError(null);
    setReloadKey((value) => value + 1);
  }, [draftFilters]);

  const setPage = useCallback((nextPage: number) => {
    setPageState(Math.max(1, Math.floor(nextPage) || 1));
  }, []);

  const setPageSize = useCallback((nextPageSize: number) => {
    prefetchGenerationRef.current += 1;
    pageCacheRef.current.clear();
    setPageSizeState(clampPageSize(nextPageSize));
    setPageState(1);
  }, []);

  const reload = useCallback(() => {
    if (!hasSearched) return;
    prefetchGenerationRef.current += 1;
    pageCacheRef.current.clear();
    setReloadKey((value) => value + 1);
  }, [hasSearched]);

  const [trackedBranch, setTrackedBranch] = useState(branch);
  if (branch !== trackedBranch) {
    setTrackedBranch(branch);
    prefetchGenerationRef.current += 1;
    pageCacheRef.current.clear();
    setDraftFilters(EMPTY_HISTORICO_FILTERS);
    setAppliedFilters(EMPTY_HISTORICO_FILTERS);
    setPageState(1);
    setHasSearched(false);
    setItems([]);
    setHasNext(false);
    setError(null);
    setLoading(false);
    setPrefetching(false);
  }

  useEffect(() => {
    if (!hasSearched) {
      setLoading(false);
      setPrefetching(false);
      return;
    }

    const controller = new AbortController();
    let cancelled = false;
    const generation = prefetchGenerationRef.current;
    const resolvedPageSize = clampPageSize(pageSize);
    const query = toQueryFilters(appliedFilters);

    async function fetchPage(targetPage: number): Promise<CachedPage> {
      const response: InspecoesProcessoHistoricoResponse = await getHistorico({
        branch,
        page: targetPage,
        page_size: resolvedPageSize,
        ...query,
        signal: controller.signal,
      });
      return {
        items: Array.isArray(response.items) ? response.items : [],
        hasNext: Boolean(response.has_next),
      };
    }

    async function prefetchFollowing(fromPage: number, startHasNext: boolean) {
      if (!startHasNext) {
        setPrefetching(false);
        return;
      }
      setPrefetching(true);
      let nextPage = fromPage + 1;
      let canContinue = startHasNext;
      while (
        canContinue &&
        nextPage <= HISTORICO_PREFETCH_MAX_PAGES &&
        !cancelled &&
        !controller.signal.aborted &&
        generation === prefetchGenerationRef.current
      ) {
        if (pageCacheRef.current.has(nextPage)) {
          const cached = pageCacheRef.current.get(nextPage);
          canContinue = Boolean(cached?.hasNext);
          nextPage += 1;
          continue;
        }
        try {
          const cached = await fetchPage(nextPage);
          if (
            cancelled ||
            controller.signal.aborted ||
            generation !== prefetchGenerationRef.current
          ) {
            return;
          }
          pageCacheRef.current.set(nextPage, cached);
          canContinue = cached.hasNext;
          nextPage += 1;
        } catch {
          break;
        }
      }
      if (!cancelled && generation === prefetchGenerationRef.current) {
        setPrefetching(false);
      }
    }

    async function run() {
      const cached = pageCacheRef.current.get(page);
      if (
        applyCachedPage(cached, { setItems, setHasNext }) &&
        generation === prefetchGenerationRef.current
      ) {
        setLoading(false);
        setError(null);
        void prefetchFollowing(page, cached.hasNext);
        return;
      }

      setLoading(true);
      setError(null);
      setPrefetching(false);

      try {
        const result = await fetchPage(page);
        if (
          cancelled ||
          controller.signal.aborted ||
          generation !== prefetchGenerationRef.current
        ) {
          return;
        }
        pageCacheRef.current.set(page, result);
        setItems(result.items);
        setHasNext(result.hasNext);
        setError(null);
        setLoading(false);
        void prefetchFollowing(page, result.hasNext);
      } catch (err) {
        if (
          cancelled ||
          controller.signal.aborted ||
          generation !== prefetchGenerationRef.current
        ) {
          return;
        }
        setItems([]);
        setHasNext(false);
        setError(err instanceof Error ? err.message : "Erro ao carregar o histórico.");
        setLoading(false);
        setPrefetching(false);
      }
    }

    void run();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [branch, hasSearched, appliedFilters, page, pageSize, reloadKey, refreshToken]);

  return {
    draftFilters,
    updateDraftFilters,
    clearFilters,
    search,
    page,
    pageSize,
    setPage,
    setPageSize,
    pageSizeOptions: HISTORICO_PAGE_SIZE_OPTIONS,
    items,
    hasNext,
    hasSearched,
    loading,
    prefetching,
    error,
    reload,
  };
}
