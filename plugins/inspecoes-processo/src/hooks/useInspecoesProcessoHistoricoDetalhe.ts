import { useCallback, useEffect, useState } from "react";

import { getHistoricoDetalhe } from "../api/inspecoesProcessoApi";
import type { InspecoesProcessoHistoricoDetalheResponse } from "../types/api";

export const DETALHE_DEFAULT_PAGE_SIZE = 100;
export const DETALHE_MAX_PAGE_SIZE = 200;
export const DETALHE_PAGE_SIZE_OPTIONS = [100, 200] as const;

function clampPageSize(value: number): number {
  if (!Number.isFinite(value) || value < 1) return DETALHE_DEFAULT_PAGE_SIZE;
  return Math.min(Math.floor(value), DETALHE_MAX_PAGE_SIZE);
}

type UseInspecoesProcessoHistoricoDetalheResult = {
  data: InspecoesProcessoHistoricoDetalheResponse | null;
  loading: boolean;
  error: string | null;
  page: number;
  pageSize: number;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  pageSizeOptions: readonly number[];
  reload: () => void;
};

export function useInspecoesProcessoHistoricoDetalhe(
  branch: string,
  ordemProducao: string | null,
): UseInspecoesProcessoHistoricoDetalheResult {
  const [data, setData] = useState<InspecoesProcessoHistoricoDetalheResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPageState] = useState(1);
  const [pageSize, setPageSizeState] = useState(DETALHE_DEFAULT_PAGE_SIZE);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  const setPage = useCallback((nextPage: number) => {
    setPageState(Math.max(1, Math.floor(nextPage) || 1));
  }, []);

  const setPageSize = useCallback((nextPageSize: number) => {
    setPageSizeState(clampPageSize(nextPageSize));
    setPageState(1);
  }, []);

  const [trackedOp, setTrackedOp] = useState(ordemProducao);
  if (ordemProducao !== trackedOp) {
    setTrackedOp(ordemProducao);
    setData(null);
    setError(null);
    setLoading(false);
    setPageState(1);
  }

  useEffect(() => {
    if (!ordemProducao) {
      return;
    }

    const resolvedOrdemProducao = ordemProducao;
    const controller = new AbortController();

    async function run() {
      setLoading(true);
      setError(null);

      try {
        const result = await getHistoricoDetalhe({
          branch,
          ordem_producao: resolvedOrdemProducao,
          page,
          page_size: clampPageSize(pageSize),
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setData(result);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setData(null);
        setError(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar o detalhe da ordem de produção.",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();

    return () => {
      controller.abort();
    };
  }, [branch, ordemProducao, page, pageSize, reloadKey]);

  if (!ordemProducao) {
    return {
      data: null,
      loading: false,
      error: null,
      page: 1,
      pageSize: DETALHE_DEFAULT_PAGE_SIZE,
      setPage,
      setPageSize,
      pageSizeOptions: DETALHE_PAGE_SIZE_OPTIONS,
      reload,
    };
  }

  return {
    data,
    loading,
    error,
    page,
    pageSize,
    setPage,
    setPageSize,
    pageSizeOptions: DETALHE_PAGE_SIZE_OPTIONS,
    reload,
  };
}
