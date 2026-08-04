import { useEffect, useMemo, useState } from "react";

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

export function useCustomerBillingSeries(
  customers: CustomerSummary[] | undefined,
): UseCustomerBillingSeriesResult {
  const [selectedKey, setSelectedKey] = useState(ALL_KEY);
  const [points, setPoints] = useState<CustomerBillingSeriesPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const requestPairs = useMemo(
    () => buildRequestPairs(customers, selectedKey),
    [customers, selectedKey],
  );
  const fingerprint = useMemo(() => requestFingerprint(requestPairs), [requestPairs]);

  useEffect(() => {
    if (selectedKey !== ALL_KEY && !customerOptions.some((c) => c.key === selectedKey)) {
      setSelectedKey(ALL_KEY);
    }
  }, [customerOptions, selectedKey]);

  useEffect(() => {
    if (!fingerprint) {
      setPoints([]);
      setError(null);
      setLoading(false);
      return;
    }

    const pairs = fingerprint.split("|").map((token) => {
      const [customer_code, customer_store] = token.split("\0");
      return { customer_code, customer_store };
    });

    const controller = new AbortController();
    let cancelled = false;
    setLoading(true);
    setError(null);

    void fetchCustomerBillingSeries(pairs, {
      months: 12,
      signal: controller.signal,
    })
      .then((payload) => {
        if (cancelled) return;
        setPoints(payload.points ?? []);
      })
      .catch((err: unknown) => {
        if (cancelled || controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar o gráfico.";
        setError(message);
        setPoints([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [fingerprint]);

  const totalValue = useMemo(
    () => points.reduce((sum, point) => sum + (Number(point.value) || 0), 0),
    [points],
  );

  return {
    selectedKey,
    setSelectedKey,
    customerOptions,
    points,
    loading,
    error,
    totalValue,
  };
}

export { ALL_KEY as BILLING_SERIES_ALL_KEY };
