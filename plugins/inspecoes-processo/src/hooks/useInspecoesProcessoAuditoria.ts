import { useCallback, useEffect, useState } from "react";

import { getAuditoriaApontamentos } from "../api/inspecoesProcessoApi";
import {
  AUDITORIA_DEFAULT_STATUS,
  type AuditoriaInspecaoStatus,
} from "../constants/auditoriaStatus";
import {
  AUDITORIA_SHIFT_ALL,
  type AuditoriaShiftFilter,
} from "../constants/factoryShifts";
import type {
  InspecoesProcessoAuditoriaApontamentoItem,
  InspecoesProcessoAuditoriaApontamentosSummary,
} from "../types/api";
import { resolveHasNext } from "../utils/format";
import { validateAuditRange } from "../utils/auditRange";

export const AUDITORIA_DEFAULT_PAGE_SIZE = 50;
export const AUDITORIA_MAX_PAGE_SIZE = 100;
export const AUDITORIA_PAGE_SIZE_OPTIONS = [25, 50, 100] as const;

const EMPTY_SUMMARY: InspecoesProcessoAuditoriaApontamentosSummary = {
  operadores_pendentes: 0,
  apontamentos_pendentes: 0,
  ops_operacoes_pendentes: 0,
  apontamentos_com_inspecao: 0,
  apontamentos_sem_cadastro: 0,
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
  startDate: string;
  endDate: string;
  setStartDate: (value: string) => void;
  setEndDate: (value: string) => void;
  rangeError: string | null;
  status: AuditoriaInspecaoStatus;
  setStatus: (value: AuditoriaInspecaoStatus) => void;
  shift: AuditoriaShiftFilter;
  setShift: (value: AuditoriaShiftFilter) => void;
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
  const [startDate, setStartDateState] = useState(todayIso);
  const [endDate, setEndDateState] = useState(todayIso);
  const rangeError = validateAuditRange(startDate, endDate);
  const [status, setStatusState] = useState<AuditoriaInspecaoStatus>(
    AUDITORIA_DEFAULT_STATUS,
  );
  const [shift, setShiftState] =
    useState<AuditoriaShiftFilter>(AUDITORIA_SHIFT_ALL);
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

  const setStartDate = useCallback((value: string) => {
    setStartDateState(value);
    setPageState(1);
  }, []);
  const setEndDate = useCallback((value: string) => {
    setEndDateState(value);
    setPageState(1);
  }, []);

  const setStatus = useCallback((value: AuditoriaInspecaoStatus) => {
    setStatusState(value);
    setPageState(1);
  }, []);

  const setShift = useCallback((value: AuditoriaShiftFilter) => {
    setShiftState(value);
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
    setStartDateState(todayIso());
    setEndDateState(todayIso());
    setStatusState(AUDITORIA_DEFAULT_STATUS);
    setShiftState(AUDITORIA_SHIFT_ALL);
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
      if (rangeError) {
        setItems([]);
        setSummary(EMPTY_SUMMARY);
        setHasNext(false);
        setError(rangeError);
        setLoading(false);
        return;
      }
      try {
        const response = await getAuditoriaApontamentos({
          branch,
          start_date: startDate,
          end_date: endDate,
          inspecao_status: status,
          ...(shift ? { shift } : {}),
          page,
          page_size: clampPageSize(pageSize),
          signal: controller.signal,
        });
        if (cancelled || controller.signal.aborted) return;
        setItems(Array.isArray(response.items) ? response.items : []);
        setSummary(response.summary ?? EMPTY_SUMMARY);
        setHasNext(resolveHasNext(response));
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
  }, [branch, startDate, endDate, rangeError, status, shift, page, pageSize, reloadKey, refreshToken]);

  return {
    startDate,
    endDate,
    setStartDate,
    setEndDate,
    rangeError,
    status,
    setStatus,
    shift,
    setShift,
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
