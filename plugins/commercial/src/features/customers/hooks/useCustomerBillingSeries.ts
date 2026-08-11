import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchCustomerBillingSeries,
  type CustomerBillingSeriesPoint,
} from "../../../api/customerBillingSeriesApi";
import type { CustomerSummary } from "../types/customerSummary";

export type BillingSeriesCustomerOption = {
  key: string;
  codigo: string;
  loja: string;
  nome: string;
};

const ALL_KEY = "all";

export type UseCustomerBillingSeriesResult = {
  selectedKey: string;
  setSelectedKey: (key: string) => void;
  customerOptions: BillingSeriesCustomerOption[];
  points: CustomerBillingSeriesPoint[];
  loading: boolean;
  error: string | null;
  totalValue: number;
  coverage: { covered: number; total: number; failedBatches: number };
  reload: () => void;
};

function buildRequestPairs(
  customers: CustomerSummary[] | undefined,
  selectedKey: string,
): Array<{ customer_code: string; customer_store: string }> {
  if (!customers?.length) return [];
  if (selectedKey === ALL_KEY) {
    return customers.map((c) => ({
      customer_code: c.codigo,
      customer_store: c.loja,
    }));
  }
  const match = customers.find((c) => c.key === selectedKey);
  if (!match) return [];
  return [{ customer_code: match.codigo, customer_store: match.loja }];
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
};

export function useCustomerBillingSeries(
  customers: CustomerSummary[] | undefined,
  options?: UseCustomerBillingSeriesOptions,
): UseCustomerBillingSeriesResult {
  const enabled = options?.enabled ?? true;
  const startDate = options?.startDate;
  const endDate = options?.endDate;
  const granularity = options?.granularity;
  const [selectedKey, setSelectedKey] = useState(ALL_KEY);
  const [points, setPoints] = useState<CustomerBillingSeriesPoint[]>([]);
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
  const effectiveSelectedKey =
    selectedKey === ALL_KEY || customerOptions.some((customer) => customer.key === selectedKey)
      ? selectedKey
      : ALL_KEY;

  const requestPairs = useMemo(
    () => buildRequestPairs(customers, effectiveSelectedKey),
    [customers, effectiveSelectedKey],
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

    void fetchCustomerBillingSeries(pairs, {
      months: startDate && endDate ? undefined : 12,
      startDate,
      endDate,
      granularity,
      signal: controller.signal,
    })
      .then((payload) => {
        if (cancelled) return;
        setPoints(payload.points ?? []);
        setCoverage(payload.coverage);
        setError(payload.partialError);
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
  }, [enabled, fingerprint, reloadKey, startDate, endDate, granularity]);

  const displayedPoints = useMemo(
    () => (enabled && fingerprint ? points : []),
    [enabled, fingerprint, points],
  );
  const totalValue = useMemo(
    () => displayedPoints.reduce((sum, point) => sum + (Number(point.value) || 0), 0),
    [displayedPoints],
  );

  return {
    selectedKey: effectiveSelectedKey,
    setSelectedKey,
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

export { ALL_KEY as BILLING_SERIES_ALL_KEY };
