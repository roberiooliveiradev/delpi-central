import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getCustomerOutboundInvoices } from "../api/customerBillingApi";
import type {
  CustomerBillingData,
  CustomerBillingPeriodPreset,
  CustomerBillingSituationFilter,
} from "../types/customerBilling";
import {
  periodRangeFromPreset,
  validateBillingPeriod,
} from "../utils/billingPeriod";

export type UseCustomerBillingResult = {
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  validationError: string | null;
  hasData: boolean;
  data: CustomerBillingData | null;
  preset: CustomerBillingPeriodPreset;
  setPreset: (value: CustomerBillingPeriodPreset) => void;
  startDate: string;
  endDate: string;
  setStartDate: (value: string) => void;
  setEndDate: (value: string) => void;
  situation: CustomerBillingSituationFilter;
  setSituation: (value: CustomerBillingSituationFilter) => void;
  search: string;
  setSearch: (value: string) => void;
  page: number;
  setPage: (value: number) => void;
  reload: () => void;
};

/**
 * Faturamento independente dos pedidos em aberto.
 * Uma falha aqui não afeta useCustomerDetailData.
 */
export function useCustomerBilling(
  codigo: string,
  loja: string,
  enabled: boolean,
): UseCustomerBillingResult {
  const initial = periodRangeFromPreset("90");
  const [preset, setPresetState] = useState<CustomerBillingPeriodPreset>("90");
  const [startDate, setStartDateState] = useState(initial.startDate);
  const [endDate, setEndDateState] = useState(initial.endDate);
  const [situation, setSituationState] = useState<CustomerBillingSituationFilter>("all");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [reloadKey, setReloadKey] = useState(0);

  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CustomerBillingData | null>(null);
  const hasDataRef = useRef(false);

  const validationError = useMemo(
    () => validateBillingPeriod(startDate, endDate),
    [startDate, endDate],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  const setPreset = useCallback((value: CustomerBillingPeriodPreset) => {
    setPresetState(value);
    if (value !== "custom") {
      const range = periodRangeFromPreset(value);
      setStartDateState(range.startDate);
      setEndDateState(range.endDate);
    }
    setPage(1);
  }, []);

  const setStartDate = useCallback((value: string) => {
    setPresetState("custom");
    setStartDateState(value);
    setPage(1);
  }, []);

  const setEndDate = useCallback((value: string) => {
    setPresetState("custom");
    setEndDateState(value);
    setPage(1);
  }, []);

  const setSituation = useCallback((value: CustomerBillingSituationFilter) => {
    setSituationState(value);
    setPage(1);
  }, []);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    if (!enabled || validationError) return;

    const controller = new AbortController();
    const isRefresh = hasDataRef.current;

    async function run() {
      try {
        if (isRefresh) setRefreshing(true);
        else setLoading(true);
        setError(null);

        const result = await getCustomerOutboundInvoices(
          {
            codigo,
            loja,
            startDate,
            endDate,
            page,
            pageSize: 20,
            situation,
            search: debouncedSearch,
          },
          controller.signal,
        );

        if (
          result.pagination.total_pages > 0 &&
          page > result.pagination.total_pages
        ) {
          setPage(1);
          return;
        }

        setData(result);
        hasDataRef.current = true;
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error
            ? err.message
            : "Não foi possível carregar o faturamento.";
        setError(message);
        if (!hasDataRef.current) setData(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [
    enabled,
    validationError,
    codigo,
    loja,
    startDate,
    endDate,
    page,
    situation,
    debouncedSearch,
    reloadKey,
  ]);

  return {
    loading,
    refreshing,
    error,
    validationError,
    hasData: Boolean(data),
    data,
    preset,
    setPreset,
    startDate,
    endDate,
    setStartDate,
    setEndDate,
    situation,
    setSituation,
    search,
    setSearch,
    page,
    setPage,
    reload,
  };
}
