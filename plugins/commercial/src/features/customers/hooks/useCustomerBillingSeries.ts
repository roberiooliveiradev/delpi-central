import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchCustomerBillingSeries,
  type CustomerBillingSeriesPoint,
} from "../../../api/customerBillingSeriesApi";
import {
  compareYearOffsets,
  type CompareYearsCount,
  clampCompareYears,
} from "../../analytics/utils/compareYears";
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
  value_prior_2?: number | null;
  value_prior_3?: number | null;
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
  /** Overlay YoY legado (equivale a compareYears=1). */
  comparePriorYear?: boolean;
  /** Overlays −1a…−3a (0–3). Preferir sobre comparePriorYear. */
  compareYears?: CompareYearsCount;
  nature?: "gross" | "net";
  productCodes?: string[];
  productGroups?: string[];
  market?: "domestic" | "export";
  /** Controle externo do filtro de clientes (workspace Faturamento). */
  selectedKeys?: string[];
  onSelectedKeysChange?: (keys: string[]) => void;
};

const PRIOR_VALUE_KEYS = ["value_prior", "value_prior_2", "value_prior_3"] as const;

export function useCustomerBillingSeries(
  customers: CustomerSummary[] | undefined,
  options?: UseCustomerBillingSeriesOptions,
): UseCustomerBillingSeriesResult {
  const enabled = options?.enabled ?? true;
  const startDate = options?.startDate;
  const endDate = options?.endDate;
  const granularity = options?.granularity;
  const compareYears = clampCompareYears(
    options?.compareYears ?? (options?.comparePriorYear ? 1 : 0),
  );
  const nature = options?.nature;
  const productCodesKey = (options?.productCodes ?? []).join("\0");
  const productGroupsKey = (options?.productGroups ?? []).join("\0");
  const market = options?.market;
  const productCodes = options?.productCodes;
  const productGroups = options?.productGroups;
  const controlledKeys = options?.selectedKeys;
  const onSelectedKeysChange = options?.onSelectedKeysChange;
  const [internalSelectedKeys, setInternalSelectedKeys] = useState<string[]>([]);
  const selectedKeys = controlledKeys ?? internalSelectedKeys;
  const setSelectedKeys = onSelectedKeysChange ?? setInternalSelectedKeys;
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
      nature,
      productCodes,
      productGroups,
      market,
      signal: controller.signal,
    } as const;

    const offsets = compareYearOffsets(compareYears);
    const currentPromise = fetchCustomerBillingSeries(pairs, currentQuery);
    const priorPromises = offsets.map((years) => {
      if (!startDate || !endDate) return Promise.resolve(null);
      const range = shiftPeriodRangeByYears(
        { start_date: startDate, end_date: endDate },
        years,
      );
      return fetchCustomerBillingSeries(pairs, {
        startDate: range.start_date,
        endDate: range.end_date,
        granularity,
        nature,
        productCodes,
        productGroups,
        market,
        signal: controller.signal,
      });
    });

    void Promise.all([currentPromise, ...priorPromises])
      .then(([currentPayload, ...priorPayloads]) => {
        if (cancelled) return;
        let next: BillingSeriesChartPoint[] = currentPayload.points ?? [];
        priorPayloads.forEach((priorPayload, index) => {
          const key = PRIOR_VALUE_KEYS[index];
          if (!key) return;
          const prior = priorPayload?.points ?? [];
          next = mergeSeriesWithPriorYear(next, prior, (p) => ({
            [key]: p?.value ?? null,
          }));
        });
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
    compareYears,
    nature,
    productCodesKey,
    productGroupsKey,
    market,
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
