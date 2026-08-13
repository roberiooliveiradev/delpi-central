import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchCustomerBillingSeries,
  type CustomerBillingSeriesPoint,
} from "../../../api/customerBillingSeriesApi";
import {
  mergeSeriesWithPriorYear,
  shiftPeriodRangeByYears,
} from "../../analytics/utils/periodShift";
import type { CustomerSummary } from "../types/customerSummary";

export type BillingSeriesCustomerOption = {
  key: string;
  codigo: string;
  loja: string;
  nome: string;
};

export type BillingSeriesChartPoint = CustomerBillingSeriesPoint & {
  value_prior?: number | null;
};

export type UseCustomerBillingSeriesResult = {
  /** Chaves selecionadas; vazio = toda a carteira. */
  selectedKeys: string[];
  setSelectedKeys: (keys: string[]) => void;
  customerOptions: BillingSeriesCustomerOption[];
  points: BillingSeriesChartPoint[];
  loading: boolean;
  error: string | null;
  totalValue: number;
  coverage: { covered: number; total: number; failedBatches: number };
  reload: () => void;
};

function buildRequestPairs(
  customers: CustomerSummary[] | undefined,
  selectedKeys: string[],
): Array<{ customer_code: string; customer_store: string }> {
  if (!customers?.length) return [];
  if (!selectedKeys.length) {
    return customers.map((c) => ({
      customer_code: c.codigo,
      customer_store: c.loja,
    }));
  }
  const selected = new Set(selectedKeys);
  return customers
    .filter((c) => selected.has(c.key))
    .map((c) => ({
      customer_code: c.codigo,
      customer_store: c.loja,
    }));
}

function requestFingerprint(
  pairs: Array<{ customer_code: string; customer_store: string }>,
): string {
  return pairs
    .map((p) => `${p.customer_code}\0${p.customer_store}`)
    .sort()
    .join("|");
}

export type UseCustomerBillingSeriesOptions = {
  enabled?: boolean;
  startDate?: string;
  endDate?: string;
  granularity?: "day" | "week" | "month" | "year";
  /** Overlay YoY: 2ª chamada com o mesmo intervalo −1 ano. */
  comparePriorYear?: boolean;
};

export function useCustomerBillingSeries(
  customers: CustomerSummary[] | undefined,
  options?: UseCustomerBillingSeriesOptions,
): UseCustomerBillingSeriesResult {
  const enabled = options?.enabled ?? true;
  const startDate = options?.startDate;
  const endDate = options?.endDate;
  const granularity = options?.granularity;
  const comparePriorYear = Boolean(options?.comparePriorYear);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [points, setPoints] = useState<BillingSeriesChartPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [coverage, setCoverage] = useState({ covered: 0, total: 0, failedBatches: 0 });
  const [reloadKey, setReloadKey] = useState(0);
  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  const customerOptions = useMemo(() => {
    return (customers ?? [])
      .map((customer) => ({
        key: customer.key,
        codigo: customer.codigo,
        loja: customer.loja,
        nome: customer.nome,
      }))
      .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  }, [customers]);

  const optionKeySet = useMemo(
    () => new Set(customerOptions.map((customer) => customer.key)),
    [customerOptions],
  );
  const effectiveSelectedKeys = useMemo(
    () => selectedKeys.filter((key) => optionKeySet.has(key)),
    [optionKeySet, selectedKeys],
  );

  const requestPairs = useMemo(
    () => buildRequestPairs(customers, effectiveSelectedKeys),
    [customers, effectiveSelectedKeys],
  );
  const fingerprint = useMemo(() => requestFingerprint(requestPairs), [requestPairs]);

  useEffect(() => {
    if (!enabled || !fingerprint) return;

    const pairs = fingerprint.split("|").map((token) => {
      const [customer_code, customer_store] = token.split("\0");
      return { customer_code, customer_store };
    });

    const controller = new AbortController();
    let cancelled = false;
    setLoading(true);
    setError(null);

    const currentQuery = {
      months: startDate && endDate ? undefined : 12,
      startDate,
      endDate,
      granularity,
      signal: controller.signal,
    } as const;

    const priorRange =
      comparePriorYear && startDate && endDate
        ? shiftPeriodRangeByYears(
            { start_date: startDate, end_date: endDate },
            -1,
          )
        : null;

    const currentPromise = fetchCustomerBillingSeries(pairs, currentQuery);
    const priorPromise = priorRange
      ? fetchCustomerBillingSeries(pairs, {
          startDate: priorRange.start_date,
          endDate: priorRange.end_date,
          granularity,
          signal: controller.signal,
        })
      : Promise.resolve(null);

    void Promise.all([currentPromise, priorPromise])
      .then(([currentPayload, priorPayload]) => {
        if (cancelled) return;
        const current = currentPayload.points ?? [];
        const prior = priorPayload?.points ?? [];
        const next: BillingSeriesChartPoint[] = comparePriorYear
          ? mergeSeriesWithPriorYear(current, prior, (p) => ({
              value_prior: p?.value ?? null,
            }))
          : current;
        setPoints(next);
        setCoverage(currentPayload.coverage);
        setError(currentPayload.partialError);
      })
      .catch((err: unknown) => {
        if (cancelled || controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar o gráfico.";
        setError(message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [
    enabled,
    fingerprint,
    reloadKey,
    startDate,
    endDate,
    granularity,
    comparePriorYear,
  ]);

  const displayedPoints = useMemo(
    () => (enabled && fingerprint ? points : []),
    [enabled, fingerprint, points],
  );
  const totalValue = useMemo(
    () => displayedPoints.reduce((sum, point) => sum + (Number(point.value) || 0), 0),
    [displayedPoints],
  );

  return {
    selectedKeys: effectiveSelectedKeys,
    setSelectedKeys,
    customerOptions,
    points: displayedPoints,
    loading: enabled && fingerprint ? loading : false,
    error: enabled && fingerprint ? error : null,
    totalValue,
    coverage:
      enabled && fingerprint ? coverage : { covered: 0, total: 0, failedBatches: 0 },
    reload,
  };
}
