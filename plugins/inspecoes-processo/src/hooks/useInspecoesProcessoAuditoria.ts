import { useCallback, useEffect, useState } from "react";

import { getAuditoriaApontamentos } from "../api/inspecoesProcessoApi";
import type {
  InspecoesProcessoAuditoriaApontamentoItem,
  InspecoesProcessoAuditoriaApontamentosSummary,
} from "../types/api";

export const AUDITORIA_DEFAULT_PAGE_SIZE = 50;
export const AUDITORIA_MAX_PAGE_SIZE = 100;
export const AUDITORIA_PAGE_SIZE_OPTIONS = [25, 50, 100] as const;

const EMPTY_SUMMARY: InspecoesProcessoAuditoriaApontamentosSummary = {
  operadores_pendentes: 0,
  apontamentos_pendentes: 0,
  ops_operacoes_pendentes: 0,
  apontamentos_com_inspecao: 0,
  apontamentos_total: 0,
};

function todayIso(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function clampPageSize(value: number): number {
  if (!Number.isFinite(value) || value < 1) return AUDITORIA_DEFAULT_PAGE_SIZE;
  return Math.min(Math.floor(value), AUDITORIA_MAX_PAGE_SIZE);
}

type UseInspecoesProcessoAuditoriaResult = {
  data: string;
  setData: (value: string) => void;
  page: number;
  pageSize: number;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  pageSizeOptions: readonly number[];
  items: InspecoesProcessoAuditoriaApontamentoItem[];
  summary: InspecoesProcessoAuditoriaApontamentosSummary;
  hasNext: boolean;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useInspecoesProcessoAuditoria(
  branch: string,
  refreshToken = 0,
): UseInspecoesProcessoAuditoriaResult {
  const [data, setDataState] = useState(todayIso);
  const [page, setPageState] = useState(1);
  const [pageSize, setPageSizeState] = useState(AUDITORIA_DEFAULT_PAGE_SIZE);
  const [reloadKey, setReloadKey] = useState(0);
  const [items, setItems] = useState<InspecoesProcessoAuditoriaApontamentoItem[]>(
    [],
  );
  const [summary, setSummary] =
    useState<InspecoesProcessoAuditoriaApontamentosSummary>(EMPTY_SUMMARY);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const setData = useCallback((value: string) => {
    setDataState(value);
    setPageState(1);
  }, []);

  const setPage = useCallback((nextPage: number) => {
    setPageState(Math.max(1, Math.floor(nextPage) || 1));
  }, []);

  const setPageSize = useCallback((nextPageSize: number) => {
    setPageSizeState(clampPageSize(nextPageSize));
    setPageState(1);
  }, []);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  const [trackedBranch, setTrackedBranch] = useState(branch);
  if (branch !== trackedBranch) {
    setTrackedBranch(branch);
    setDataState(todayIso());
    setPageState(1);
    setItems([]);
    setSummary(EMPTY_SUMMARY);
    setHasNext(false);
    setError(null);
  }

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const response = await getAuditoriaApontamentos({
          branch,
          data,
          page,
          page_size: clampPageSize(pageSize),
          signal: controller.signal,
        });
        if (cancelled || controller.signal.aborted) return;
        setItems(Array.isArray(response.items) ? response.items : []);
        setSummary(response.summary ?? EMPTY_SUMMARY);
        setHasNext(Boolean(response.has_next));
        if (response.data && response.data !== data) {
          setDataState(response.data);
        }
        setError(null);
      } catch (err) {
        if (cancelled || controller.signal.aborted) return;
        setItems([]);
        setSummary(EMPTY_SUMMARY);
        setHasNext(false);
        setError(
          err instanceof Error
            ? err.message
            : "Erro ao carregar a auditoria de apontamentos.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void run();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [branch, data, page, pageSize, reloadKey, refreshToken]);

  return {
    data,
    setData,
    page,
    pageSize,
    setPage,
    setPageSize,
    pageSizeOptions: AUDITORIA_PAGE_SIZE_OPTIONS,
    items,
    summary,
    hasNext,
    loading,
    error,
    reload,
  };
}
